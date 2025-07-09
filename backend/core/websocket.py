from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import asyncio
import json
import logging
from datetime import datetime
from integrations.prometheus_client import PrometheusClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.prometheus_client = PrometheusClient()
        self.monitoring_task = None
        self.is_monitoring = False

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}")

        # Start monitoring if this is the first connection
        if len(self.active_connections) == 1 and not self.is_monitoring:
            self.monitoring_task = asyncio.create_task(self.monitor_system())

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

        # Stop monitoring if no connections left
        if len(self.active_connections) == 0 and self.monitoring_task:
            self.monitoring_task.cancel()
            self.is_monitoring = False

    async def send_to_all(self, message: Dict[str, Any]):
        """Send message to all connected clients"""
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def monitor_system(self):
        """Background monitoring task"""
        self.is_monitoring = True
        logger.info("Started system monitoring")

        try:
            while self.is_monitoring and self.active_connections:
                # Get system status
                system_status = await self.get_system_status()

                # Send to all connected clients
                await self.send_to_all({
                    "type": "system_status",
                    "timestamp": datetime.now().isoformat(),
                    "data": system_status
                })

                # Wait 30 seconds before next update
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}")
        finally:
            self.is_monitoring = False

    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # Banking services health
            banking_health = await self.prometheus_client.query_metric('up{job="banking-services"}')

            # Cache status
            cache_status = await self.prometheus_client.query_metric('redis_connected_clients')

            # Cache hit ratio (try different metric names)
            cache_hit_ratio = None
            for metric_name in ['redis_cache_hit_ratio', 'redis_keyspace_hits_total', 'redis_keyspace_hits']:
                try:
                    cache_hit_ratio = await self.prometheus_client.query_metric(metric_name)
                    if cache_hit_ratio and cache_hit_ratio.get('status') == 'success':
                        break
                except:
                    continue

            # Count healthy services
            healthy_services = 0
            total_services = 0
            service_details = []

            if banking_health and banking_health.get('status') == 'success':
                results = banking_health.get('data', {}).get('result', [])
                total_services = len(results)

                for result in results:
                    metric = result.get('metric', {})
                    value = result.get('value', [None, '0'])
                    is_healthy = value[1] == '1'

                    if is_healthy:
                        healthy_services += 1

                    service_details.append({
                        'name': metric.get('instance', 'unknown'),
                        'healthy': is_healthy,
                        'port': metric.get('instance', '').split(':')[-1] if ':' in metric.get('instance', '') else None
                    })

            # Cache metrics
            cache_clients = 0
            cache_hit_rate = 0

            if cache_status and cache_status.get('status') == 'success':
                results = cache_status.get('data', {}).get('result', [])
                if results:
                    cache_clients = int(
                        float(results[0].get('value', [None, '0'])[1]))

            if cache_hit_ratio and cache_hit_ratio.get('status') == 'success':
                results = cache_hit_ratio.get('data', {}).get('result', [])
                if results:
                    cache_hit_rate = float(results[0].get(
                        'value', [None, '0'])[1])
                    # If it's already a percentage (0-1), convert to percentage
                    if cache_hit_rate <= 1:
                        cache_hit_rate = cache_hit_rate * 100

            return {
                'banking_services': {
                    'healthy': healthy_services,
                    'total': total_services,
                    'percentage': (healthy_services / total_services * 100) if total_services > 0 else 0,
                    'services': service_details
                },
                'cache': {
                    'connected_clients': cache_clients,
                    'hit_ratio': round(cache_hit_rate, 2)
                },
                'overall_health': healthy_services == total_services if total_services > 0 else False
            }

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'banking_services': {'healthy': 0, 'total': 0, 'percentage': 0, 'services': []},
                'cache': {'connected_clients': 0, 'hit_ratio': 0},
                'overall_health': False
            }


# Global WebSocket manager instance
ws_manager = WebSocketManager()

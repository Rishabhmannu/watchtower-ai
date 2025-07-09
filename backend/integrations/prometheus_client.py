import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusClient:
    """
    Backward-compatible Prometheus client that wraps the enhanced client
    Maintains all existing functionality while providing access to advanced features
    """
    
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.session = None
        self._enhanced_client = None

    async def _get_enhanced_client(self):
        """Lazy-load the enhanced client to avoid circular imports"""
        if self._enhanced_client is None:
            from integrations.enhanced_prometheus_client import EnhancedPrometheusClient
            self._enhanced_client = EnhancedPrometheusClient(self.base_url)
        return self._enhanced_client

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def query_metric(self, query: str) -> Optional[Dict]:
        """
        Query Prometheus with a PromQL query (original method)
        Maintains backward compatibility
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v1/query"
            params = {"query": query}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Prometheus query '{query}' successful")
                    return data
                else:
                    logger.error(f"Prometheus query failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None

    async def get_targets(self) -> Optional[List]:
        """Get list of all monitored targets (original method)"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v1/targets"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Retrieved Prometheus targets successfully")
                    return data.get("data", {}).get("activeTargets", [])
                else:
                    logger.error(f"Failed to get targets: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting targets: {e}")
            return None

    async def check_connection(self) -> bool:
        """Check if Prometheus is accessible (original method)"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v1/query"
            params = {"query": "up"}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    logger.info("Prometheus connection successful")
                    return True
                else:
                    logger.error(
                        f"Prometheus connection failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Prometheus connection error: {e}")
            return False

    # NEW ENHANCED METHODS - Access to advanced functionality
    
    async def query_service_metrics(self, service_name: str, metric_types: Optional[List] = None) -> Dict:
        """
        NEW: Query comprehensive metrics for a specific service
        Uses the enhanced client for advanced service-aware querying
        """
        enhanced_client = await self._get_enhanced_client()
        return await enhanced_client.query_service_metrics(service_name, metric_types)

    async def query_category_health(self, category: str) -> Dict:
        """
        NEW: Get health summary for all services in a category
        """
        enhanced_client = await self._get_enhanced_client()
        from models.service_models import ServiceCategory
        try:
            category_enum = ServiceCategory(category)
            return await enhanced_client.query_category_health(category_enum)
        except ValueError:
            raise ValueError(f"Invalid category: {category}")

    async def get_system_overview(self) -> Dict:
        """
        NEW: Get comprehensive system overview across all 31 services
        """
        enhanced_client = await self._get_enhanced_client()
        return await enhanced_client.get_system_overview()

    async def query_multiple_services(self, service_names: List[str], metric_types: Optional[List] = None) -> Dict:
        """
        NEW: Query metrics for multiple services concurrently
        """
        enhanced_client = await self._get_enhanced_client()
        return await enhanced_client.query_multiple_services(service_names, metric_types)

    async def query_with_retry(self, query: str) -> Dict:
        """
        NEW: Query with retry logic and enhanced error handling
        """
        enhanced_client = await self._get_enhanced_client()
        result = await enhanced_client.query_metric_with_retry(query)
        
        # Convert to dict format for easier consumption
        return {
            "query": result.query,
            "success": result.success,
            "data": result.data,
            "timestamp": result.timestamp.isoformat(),
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message
        }

    async def clear_cache(self):
        """NEW: Clear the enhanced client's cache"""
        if self._enhanced_client:
            await self._enhanced_client.clear_cache()

    async def close(self):
        """Close the HTTP session and cleanup"""
        if self.session:
            await self.session.close()
            self.session = None
            
        if self._enhanced_client:
            await self._enhanced_client.close()
            
        logger.info("Prometheus client closed")

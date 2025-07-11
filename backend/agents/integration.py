"""
Agent Integration Module - Connects multi-agent system to main application
File: backend/agents/integration.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from .executor import executor, WorkflowType, WorkflowRequest
from .base_agent import communication_hub

logger = logging.getLogger(__name__)


class AgentIntegration:
    """Integration layer for WatchTower AI agents"""

    def __init__(self):
        self.is_initialized = False
        self.background_tasks = []
        self.monitoring_active = False

    async def initialize(self):
        """Initialize the agent system"""
        if self.is_initialized:
            logger.warning("Agent system already initialized")
            return

        try:
            logger.info("Initializing WatchTower AI Agent System...")

            # Start the executor
            await executor.start()

            # Start background monitoring
            await self._start_background_monitoring()

            self.is_initialized = True
            logger.info("✅ Agent system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent system: {e}")
            raise

    async def shutdown(self):
        """Shutdown the agent system"""
        if not self.is_initialized:
            return

        logger.info("Shutting down WatchTower AI Agent System...")

        # Stop background monitoring
        await self._stop_background_monitoring()

        # Stop executor
        await executor.stop()

        self.is_initialized = False
        logger.info("Agent system shutdown complete")

    async def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        try:
            self.monitoring_active = True

            # Create background task for proactive monitoring
            monitoring_task = asyncio.create_task(
                self._proactive_monitoring_loop())
            self.background_tasks.append(monitoring_task)

            logger.info("Background monitoring started")

        except Exception as e:
            logger.error(f"Failed to start background monitoring: {e}")

    async def _stop_background_monitoring(self):
        """Stop background monitoring tasks"""
        self.monitoring_active = False

        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        self.background_tasks.clear()
        logger.info("Background monitoring stopped")

    async def _proactive_monitoring_loop(self):
        """Main proactive monitoring loop"""
        while self.monitoring_active:
            try:
                # Run proactive monitoring workflow every 5 minutes
                await self._run_proactive_monitoring()
                await asyncio.sleep(300)  # 5 minutes

            except asyncio.CancelledError:
                logger.info("Proactive monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in proactive monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _run_proactive_monitoring(self):
        """Run proactive monitoring workflow"""
        try:
            request = WorkflowRequest(
                request_id=f"proactive_{int(datetime.now().timestamp())}",
                workflow_type=WorkflowType.PROACTIVE_MONITORING,
                parameters={},
                priority=1
            )

            result = await executor.execute_workflow(request)

            if result.success:
                logger.debug("Proactive monitoring completed successfully")
            else:
                logger.warning(
                    f"Proactive monitoring failed: {result.error_message}")

        except Exception as e:
            logger.error(f"Error running proactive monitoring: {e}")

    # Public API methods for integration with chat system
    async def process_chat_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chat query using agent system"""
        if not self.is_initialized:
            return {"error": "Agent system not initialized"}

        try:
            # Determine query type and route to appropriate workflow
            if any(word in query.lower() for word in ["health", "status", "how are"]):
                return await self._handle_health_query(query, context)
            elif any(word in query.lower() for word in ["analyze", "analysis", "why", "problem"]):
                return await self._handle_analysis_query(query, context)
            elif any(word in query.lower() for word in ["overview", "summary", "report"]):
                return await self._handle_overview_query(query, context)
            else:
                return await self._handle_general_query(query, context)

        except Exception as e:
            logger.error(f"Error processing chat query: {e}")
            return {"error": f"Failed to process query: {str(e)}"}

    async def _handle_health_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health-related queries"""
        try:
            result = await executor.perform_health_check()

            if result.success:
                health_data = result.result

                # Format response for chat
                return {
                    "response_type": "health_check",
                    "success": True,
                    "data": health_data,
                    "summary": self._format_health_summary(health_data),
                    "execution_time": result.execution_time
                }
            else:
                return {
                    "response_type": "health_check",
                    "success": False,
                    "error": result.error_message
                }

        except Exception as e:
            logger.error(f"Error handling health query: {e}")
            return {"error": f"Health query failed: {str(e)}"}

    async def _handle_analysis_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis-related queries"""
        try:
            result = await executor.analyze_system()

            if result.success:
                analysis_data = result.result

                return {
                    "response_type": "system_analysis",
                    "success": True,
                    "data": analysis_data,
                    "summary": self._format_analysis_summary(analysis_data),
                    "execution_time": result.execution_time
                }
            else:
                return {
                    "response_type": "system_analysis",
                    "success": False,
                    "error": result.error_message
                }

        except Exception as e:
            logger.error(f"Error handling analysis query: {e}")
            return {"error": f"Analysis query failed: {str(e)}"}

    async def _handle_overview_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle overview-related queries"""
        try:
            # Get both health and analysis data
            health_result = await executor.perform_health_check()
            analysis_result = await executor.analyze_system()

            overview_data = {
                "health_data": health_result.result if health_result.success else {},
                "analysis_data": analysis_result.result if analysis_result.success else {},
                "agent_status": executor.get_status()
            }

            return {
                "response_type": "system_overview",
                "success": True,
                "data": overview_data,
                "summary": self._format_overview_summary(overview_data),
                "execution_time": (health_result.execution_time if health_result.success else 0) +
                                 (analysis_result.execution_time if analysis_result.success else 0)
            }

        except Exception as e:
            logger.error(f"Error handling overview query: {e}")
            return {"error": f"Overview query failed: {str(e)}"}

    async def _handle_general_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general queries"""
        try:
            # For general queries, perform a basic health check
            result = await executor.perform_health_check()

            return {
                "response_type": "general",
                "success": True,
                "data": result.result if result.success else {},
                "summary": f"I've checked the system status. {self._format_health_summary(result.result) if result.success else 'System check failed.'}",
                "execution_time": result.execution_time
            }

        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return {"error": f"General query failed: {str(e)}"}

    def _format_health_summary(self, health_data: Dict[str, Any]) -> str:
        """Format health data for chat response"""
        try:
            health_summary = health_data.get("health_summary", {})

            if not health_summary:
                return "System health data not available"

            total_services = health_summary.get("total_services", 0)
            healthy_services = health_summary.get("healthy_services", 0)
            health_percentage = health_summary.get("health_percentage", 0)

            status_emoji = "✅" if health_percentage > 90 else "⚠️" if health_percentage > 70 else "🚨"

            summary = f"{status_emoji} **System Health: {health_percentage:.1f}%**\n"
            summary += f"• {healthy_services}/{total_services} services healthy\n"

            if health_summary.get("issues_detected"):
                summary += f"• Issues: {', '.join(health_summary['issues_detected'])}\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting health summary: {e}")
            return "Unable to format health summary"

    def _format_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Format analysis data for chat response"""
        try:
            insights = analysis_data.get("insights", {})
            recommendations = analysis_data.get("recommendations", [])

            summary = "🔍 **System Analysis Complete**\n\n"

            # Add insights
            if insights:
                summary += "**Key Insights:**\n"
                for category, items in insights.items():
                    if isinstance(items, list) and items:
                        summary += f"• {category.replace('_', ' ').title()}: {items[0]}\n"
                    elif isinstance(items, str):
                        summary += f"• {category.replace('_', ' ').title()}: {items}\n"
                summary += "\n"

            # Add recommendations
            if recommendations:
                summary += "**Recommendations:**\n"
                for rec in recommendations[:3]:  # Show first 3 recommendations
                    summary += f"• {rec}\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting analysis summary: {e}")
            return "Analysis completed but summary formatting failed"

    def _format_overview_summary(self, overview_data: Dict[str, Any]) -> str:
        """Format overview data for chat response"""
        try:
            health_data = overview_data.get("health_data", {})
            agent_status = overview_data.get("agent_status", {})

            summary = "📊 **System Overview**\n\n"

            # Add health information
            if health_data and "health_summary" in health_data:
                health_summary = health_data["health_summary"]
                health_percentage = health_summary.get("health_percentage", 0)

                status_emoji = "✅" if health_percentage > 90 else "⚠️" if health_percentage > 70 else "🚨"
                summary += f"{status_emoji} **Health:** {health_percentage:.1f}%\n"

            # Add agent status
            if agent_status:
                workflows_executed = agent_status.get("workflows_executed", 0)
                uptime = agent_status.get("uptime_seconds", 0)

                summary += f"🤖 **AI Agents:** {agent_status.get('registered_agents', 0)} active\n"
                summary += f"⚡ **Workflows:** {workflows_executed} executed\n"
                summary += f"⏱️ **Uptime:** {uptime/3600:.1f} hours\n"

            return summary

        except Exception as e:
            logger.error(f"Error formatting overview summary: {e}")
            return "Overview data available but summary formatting failed"

    # Alert processing methods
    async def process_alert(self, alert_data: Dict[str, Any], metric_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process alert using agent system"""
        if not self.is_initialized:
            return {"error": "Agent system not initialized"}

        try:
            result = await executor.process_alert(alert_data, metric_data or {})

            if result.success:
                return {
                    "success": True,
                    "analysis": result.result,
                    "execution_time": result.execution_time
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }

        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return {"error": f"Alert processing failed: {str(e)}"}

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "initialized": self.is_initialized,
            "monitoring_active": self.monitoring_active,
            "background_tasks": len(self.background_tasks),
            "executor_status": executor.get_status() if self.is_initialized else {},
            "agent_statuses": communication_hub.get_agent_statuses() if self.is_initialized else {}
        }


# Global integration instance
agent_integration = AgentIntegration()

# Context manager for easy lifecycle management


@asynccontextmanager
async def managed_agent_system():
    """Context manager for agent system lifecycle"""
    await agent_integration.initialize()
    try:
        yield agent_integration
    finally:
        await agent_integration.shutdown()

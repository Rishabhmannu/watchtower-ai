"""
LangGraph Executor for Multi-Agent Orchestration
File: backend/agents/executor.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from .base_agent import BaseAgent, AgentType, AgentMessage, MessageType, create_message, communication_hub
from .alert_agent import HealthAgent
from .analysis_agent import AnalysisAgent
from core.service_registry import BankingServiceRegistry
from core.dashboard_registry import DashboardRegistry
from llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of workflows supported"""
    HEALTH_CHECK = "health_check"
    ALERT_ANALYSIS = "alert_analysis"
    SYSTEM_ANALYSIS = "system_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"
    PROACTIVE_MONITORING = "proactive_monitoring"


@dataclass
class WorkflowRequest:
    """Request for workflow execution"""
    request_id: str
    workflow_type: WorkflowType
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 300  # 5 minutes
    callback: Optional[Callable] = None


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    request_id: str
    workflow_type: WorkflowType
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None

# LangGraph State


class AgentState(TypedDict):
    """State for LangGraph workflow"""
    messages: Annotated[List[AgentMessage], add_messages]
    workflow_type: str
    request_id: str
    current_step: str
    results: Dict[str, Any]
    error: Optional[str]
    metadata: Dict[str, Any]


class WatchTowerExecutor:
    """Main executor for WatchTower AI multi-agent system"""

    def __init__(self):
        self.is_running = False
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, StateGraph] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}

        # Initialize components
        self.service_registry = BankingServiceRegistry()
        self.dashboard_registry = DashboardRegistry()
        self.openai_client = OpenAIClient()

        # Performance tracking
        self.workflows_executed = 0
        self.start_time = datetime.now()

        # Initialize agents and workflows
        self._initialize_agents()
        self._initialize_workflows()

        logger.info("WatchTower Executor initialized")

    def _initialize_agents(self):
        """Initialize all agents"""
        try:
            # Create agents
            self.agents = {
                "health_agent": HealthAgent("health_agent"),
                "analysis_agent": AnalysisAgent("analysis_agent")
            }

            # Register agents with communication hub
            for agent in self.agents.values():
                communication_hub.register_agent(agent)

            logger.info(f"Initialized {len(self.agents)} agents")

        except Exception as e:
            logger.error(f"Error initializing agents: {e}")

    def _initialize_workflows(self):
        """Initialize LangGraph workflows"""
        try:
            # Create workflows for different scenarios
            self.workflows = {
                WorkflowType.HEALTH_CHECK.value: self._create_health_check_workflow(),
                WorkflowType.ALERT_ANALYSIS.value: self._create_alert_analysis_workflow(),
                WorkflowType.SYSTEM_ANALYSIS.value: self._create_system_analysis_workflow(),
                WorkflowType.CORRELATION_ANALYSIS.value: self._create_correlation_analysis_workflow(),
                WorkflowType.PROACTIVE_MONITORING.value: self._create_proactive_monitoring_workflow()
            }

            logger.info(f"Initialized {len(self.workflows)} workflows")

        except Exception as e:
            logger.error(f"Error initializing workflows: {e}")

    def _create_health_check_workflow(self) -> StateGraph:
        """Create health check workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("health_check", self._health_check_node)
        workflow.add_node("process_results", self._process_health_results_node)

        # Add edges
        workflow.add_edge("health_check", "process_results")
        workflow.add_edge("process_results", END)

        # Set entry point
        workflow.set_entry_point("health_check")

        return workflow.compile()

    def _create_alert_analysis_workflow(self) -> StateGraph:
        """Create alert analysis workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("receive_alert", self._receive_alert_node)
        workflow.add_node("analyze_alert", self._analyze_alert_node)
        workflow.add_node("correlate_services", self._correlate_services_node)
        workflow.add_node("generate_response", self._generate_response_node)

        # Add edges
        workflow.add_edge("receive_alert", "analyze_alert")
        workflow.add_edge("analyze_alert", "correlate_services")
        workflow.add_edge("correlate_services", "generate_response")
        workflow.add_edge("generate_response", END)

        # Set entry point
        workflow.set_entry_point("receive_alert")

        return workflow.compile()

    def _create_system_analysis_workflow(self) -> StateGraph:
        """Create system analysis workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("gather_metrics", self._gather_metrics_node)
        workflow.add_node("analyze_patterns", self._analyze_patterns_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        workflow.add_node("create_recommendations",
                          self._create_recommendations_node)

        # Add edges
        workflow.add_edge("gather_metrics", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "generate_insights")
        workflow.add_edge("generate_insights", "create_recommendations")
        workflow.add_edge("create_recommendations", END)

        # Set entry point
        workflow.set_entry_point("gather_metrics")

        return workflow.compile()

    def _create_correlation_analysis_workflow(self) -> StateGraph:
        """Create correlation analysis workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("identify_services", self._identify_services_node)
        workflow.add_node("analyze_correlations",
                          self._analyze_correlations_node)
        workflow.add_node("evaluate_impact", self._evaluate_impact_node)

        # Add edges
        workflow.add_edge("identify_services", "analyze_correlations")
        workflow.add_edge("analyze_correlations", "evaluate_impact")
        workflow.add_edge("evaluate_impact", END)

        # Set entry point
        workflow.set_entry_point("identify_services")

        return workflow.compile()

    def _create_proactive_monitoring_workflow(self) -> StateGraph:
        """Create proactive monitoring workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("monitor_health", self._monitor_health_node)
        workflow.add_node("detect_anomalies", self._detect_anomalies_node)
        workflow.add_node("predict_issues", self._predict_issues_node)
        workflow.add_node("generate_alerts", self._generate_alerts_node)

        # Add edges
        workflow.add_edge("monitor_health", "detect_anomalies")
        workflow.add_edge("detect_anomalies", "predict_issues")
        workflow.add_edge("predict_issues", "generate_alerts")
        workflow.add_edge("generate_alerts", END)

        # Set entry point
        workflow.set_entry_point("monitor_health")

        return workflow.compile()

    # Workflow nodes implementation
    async def _health_check_node(self, state: AgentState) -> AgentState:
        """Health check workflow node"""
        try:
            # Send health check request to health agent
            health_message = create_message(
                sender="executor",
                recipient="health_agent",
                message_type=MessageType.QUERY,
                content={"type": "system_overview"}
            )

            # Get health agent response
            health_agent = self.agents["health_agent"]
            response = await health_agent.process_message(health_message)

            if response:
                state["results"]["health_data"] = response.content
                state["current_step"] = "health_check_completed"
            else:
                state["error"] = "Failed to get health data"

            return state

        except Exception as e:
            state["error"] = f"Health check failed: {str(e)}"
            logger.error(f"Health check node error: {e}")
            return state

    async def _process_health_results_node(self, state: AgentState) -> AgentState:
        """Process health results node"""
        try:
            health_data = state["results"].get("health_data", {})

            # Process and summarize health data
            summary = {
                "overall_health": "healthy",
                "total_services": 0,
                "healthy_services": 0,
                "issues_detected": []
            }

            if "overview" in health_data:
                overview = health_data["overview"]
                summary["total_services"] = overview.get("total_services", 0)
                summary["healthy_services"] = overview.get(
                    "healthy_services", 0)

                if overview.get("critical_services", 0) > 0:
                    summary["overall_health"] = "critical"
                    summary["issues_detected"].append(
                        f"{overview['critical_services']} critical services")
                elif overview.get("warning_services", 0) > 0:
                    summary["overall_health"] = "warning"
                    summary["issues_detected"].append(
                        f"{overview['warning_services']} services with warnings")

            state["results"]["health_summary"] = summary
            state["current_step"] = "results_processed"

            return state

        except Exception as e:
            state["error"] = f"Processing health results failed: {str(e)}"
            logger.error(f"Process health results node error: {e}")
            return state

    async def _receive_alert_node(self, state: AgentState) -> AgentState:
        """Receive alert workflow node"""
        try:
            # Extract alert information from state
            alert_data = state["metadata"].get("alert_data", {})

            state["results"]["alert_info"] = {
                "service_name": alert_data.get("service_name"),
                "severity": alert_data.get("severity"),
                "message": alert_data.get("message"),
                "timestamp": alert_data.get("timestamp")
            }

            state["current_step"] = "alert_received"
            return state

        except Exception as e:
            state["error"] = f"Receive alert failed: {str(e)}"
            logger.error(f"Receive alert node error: {e}")
            return state

    async def _analyze_alert_node(self, state: AgentState) -> AgentState:
        """Analyze alert workflow node"""
        try:
            alert_info = state["results"]["alert_info"]

            # Send analysis request to analysis agent
            analysis_message = create_message(
                sender="executor",
                recipient="analysis_agent",
                message_type=MessageType.ALERT,
                content={
                    "alert": alert_info,
                    "metric": state["metadata"].get("metric_data", {})
                }
            )

            # Get analysis agent response
            analysis_agent = self.agents["analysis_agent"]
            response = await analysis_agent.process_message(analysis_message)

            if response:
                state["results"]["analysis_result"] = response.content
                state["current_step"] = "alert_analyzed"
            else:
                state["error"] = "Failed to analyze alert"

            return state

        except Exception as e:
            state["error"] = f"Analyze alert failed: {str(e)}"
            logger.error(f"Analyze alert node error: {e}")
            return state

    async def _correlate_services_node(self, state: AgentState) -> AgentState:
        """Correlate services workflow node"""
        try:
            alert_info = state["results"]["alert_info"]
            service_name = alert_info["service_name"]

            # Request correlation analysis
            correlation_message = create_message(
                sender="executor",
                recipient="analysis_agent",
                message_type=MessageType.QUERY,
                content={
                    "type": "correlation",
                    "service_name": service_name
                }
            )

            analysis_agent = self.agents["analysis_agent"]
            response = await analysis_agent.process_message(correlation_message)

            if response:
                state["results"]["correlation_data"] = response.content
                state["current_step"] = "services_correlated"
            else:
                state["results"]["correlation_data"] = {"correlations": []}

            return state

        except Exception as e:
            state["error"] = f"Correlate services failed: {str(e)}"
            logger.error(f"Correlate services node error: {e}")
            return state

    async def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate response workflow node"""
        try:
            # Compile all results into a comprehensive response
            alert_info = state["results"]["alert_info"]
            analysis_result = state["results"].get("analysis_result", {})
            correlation_data = state["results"].get("correlation_data", {})

            # Generate comprehensive response
            response = {
                "alert_summary": f"Alert from {alert_info['service_name']}: {alert_info['message']}",
                "analysis_findings": analysis_result.get("analysis_result", {}).get("findings", []),
                "recommendations": analysis_result.get("analysis_result", {}).get("recommendations", []),
                "affected_services": correlation_data.get("correlations", []),
                "confidence": analysis_result.get("analysis_result", {}).get("confidence", 0.5),
                "response_message": analysis_result.get("response_message", "Analysis completed")
            }

            state["results"]["final_response"] = response
            state["current_step"] = "response_generated"

            return state

        except Exception as e:
            state["error"] = f"Generate response failed: {str(e)}"
            logger.error(f"Generate response node error: {e}")
            return state

    async def _gather_metrics_node(self, state: AgentState) -> AgentState:
        """Gather metrics workflow node"""
        try:
            # Request health agent to gather comprehensive metrics
            metrics_message = create_message(
                sender="executor",
                recipient="health_agent",
                message_type=MessageType.QUERY,
                content={"type": "system_overview"}
            )

            health_agent = self.agents["health_agent"]
            response = await health_agent.process_message(metrics_message)

            if response:
                state["results"]["metrics_data"] = response.content
                state["current_step"] = "metrics_gathered"
            else:
                state["error"] = "Failed to gather metrics"

            return state

        except Exception as e:
            state["error"] = f"Gather metrics failed: {str(e)}"
            logger.error(f"Gather metrics node error: {e}")
            return state

    async def _analyze_patterns_node(self, state: AgentState) -> AgentState:
        """Analyze patterns workflow node"""
        try:
            # Request analysis agent to analyze patterns
            patterns_message = create_message(
                sender="executor",
                recipient="analysis_agent",
                message_type=MessageType.QUERY,
                content={"type": "recent_analyses"}
            )

            analysis_agent = self.agents["analysis_agent"]
            response = await analysis_agent.process_message(patterns_message)

            if response:
                state["results"]["pattern_analysis"] = response.content
                state["current_step"] = "patterns_analyzed"
            else:
                state["results"]["pattern_analysis"] = {"analyses": []}

            return state

        except Exception as e:
            state["error"] = f"Analyze patterns failed: {str(e)}"
            logger.error(f"Analyze patterns node error: {e}")
            return state

    async def _generate_insights_node(self, state: AgentState) -> AgentState:
        """Generate insights workflow node"""
        try:
            metrics_data = state["results"].get("metrics_data", {})
            pattern_analysis = state["results"].get("pattern_analysis", {})

            # Generate insights based on metrics and patterns
            insights = {
                "system_health_trends": "System health is stable",
                "performance_insights": [],
                "capacity_recommendations": [],
                "security_observations": []
            }

            # Add insights based on metrics
            if "overview" in metrics_data:
                overview = metrics_data["overview"]
                health_percentage = overview.get("health_percentage", 0)

                if health_percentage < 80:
                    insights["performance_insights"].append(
                        f"System health at {health_percentage}% - investigate degraded services"
                    )
                elif health_percentage > 95:
                    insights["performance_insights"].append(
                        "System performing optimally"
                    )

            # Add insights based on patterns
            analyses = pattern_analysis.get("analyses", [])
            if len(analyses) > 3:
                insights["security_observations"].append(
                    f"High analysis activity detected - {len(analyses)} analyses in recent period"
                )

            state["results"]["insights"] = insights
            state["current_step"] = "insights_generated"

            return state

        except Exception as e:
            state["error"] = f"Generate insights failed: {str(e)}"
            logger.error(f"Generate insights node error: {e}")
            return state

    async def _create_recommendations_node(self, state: AgentState) -> AgentState:
        """Create recommendations workflow node"""
        try:
            insights = state["results"].get("insights", {})

            # Generate recommendations based on insights
            recommendations = []

            for insight_category, insight_items in insights.items():
                if isinstance(insight_items, list):
                    for item in insight_items:
                        if "investigate" in item.lower():
                            recommendations.append(f"Action needed: {item}")
                        elif "degraded" in item.lower():
                            recommendations.append(f"Monitor closely: {item}")
                        elif "optimal" in item.lower():
                            recommendations.append(
                                f"Maintain current state: {item}")

            if not recommendations:
                recommendations.append(
                    "System appears stable - continue monitoring")

            state["results"]["recommendations"] = recommendations
            state["current_step"] = "recommendations_created"

            return state

        except Exception as e:
            state["error"] = f"Create recommendations failed: {str(e)}"
            logger.error(f"Create recommendations node error: {e}")
            return state

    # Additional workflow nodes (simplified for brevity)
    async def _identify_services_node(self, state: AgentState) -> AgentState:
        """Identify services workflow node"""
        state["results"]["identified_services"] = list(
            self.service_registry.get_all_services().keys())
        state["current_step"] = "services_identified"
        return state

    async def _analyze_correlations_node(self, state: AgentState) -> AgentState:
        """Analyze correlations workflow node"""
        state["results"]["correlations"] = {
            "message": "Correlation analysis completed"}
        state["current_step"] = "correlations_analyzed"
        return state

    async def _evaluate_impact_node(self, state: AgentState) -> AgentState:
        """Evaluate impact workflow node"""
        state["results"]["impact_assessment"] = {
            "impact": "low", "services_affected": 0}
        state["current_step"] = "impact_evaluated"
        return state

    async def _monitor_health_node(self, state: AgentState) -> AgentState:
        """Monitor health workflow node"""
        state["results"]["health_status"] = {"status": "monitoring_active"}
        state["current_step"] = "health_monitored"
        return state

    async def _detect_anomalies_node(self, state: AgentState) -> AgentState:
        """Detect anomalies workflow node"""
        state["results"]["anomalies"] = {"detected": False, "count": 0}
        state["current_step"] = "anomalies_detected"
        return state

    async def _predict_issues_node(self, state: AgentState) -> AgentState:
        """Predict issues workflow node"""
        state["results"]["predictions"] = {"issues_predicted": False}
        state["current_step"] = "issues_predicted"
        return state

    async def _generate_alerts_node(self, state: AgentState) -> AgentState:
        """Generate alerts workflow node"""
        state["results"]["alerts_generated"] = {"count": 0}
        state["current_step"] = "alerts_generated"
        return state

    # Public API methods
    async def start(self):
        """Start the executor and all agents"""
        if self.is_running:
            logger.warning("Executor is already running")
            return

        self.is_running = True
        logger.info("Starting WatchTower Executor...")

        # Start all agents
        await communication_hub.start_all_agents()

        logger.info("WatchTower Executor started successfully")

    async def stop(self):
        """Stop the executor and all agents"""
        self.is_running = False
        logger.info("Stopping WatchTower Executor...")

        # Stop all agents
        await communication_hub.stop_all_agents()

        logger.info("WatchTower Executor stopped")

    async def execute_workflow(self, request: WorkflowRequest) -> WorkflowResult:
        """Execute a workflow"""
        try:
            start_time = datetime.now()

            # Get workflow
            workflow_key = request.workflow_type.value
            if workflow_key not in self.workflows:
                return WorkflowResult(
                    request_id=request.request_id,
                    workflow_type=request.workflow_type,
                    success=False,
                    result={},
                    execution_time=0,
                    error_message=f"Workflow {workflow_key} not found"
                )

            workflow = self.workflows[workflow_key]

            # Create initial state
            initial_state = AgentState(
                messages=[],
                workflow_type=workflow_key,
                request_id=request.request_id,
                current_step="started",
                results={},
                error=None,
                metadata=request.parameters
            )

            # Execute workflow
            final_state = await workflow.ainvoke(initial_state)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Create result
            result = WorkflowResult(
                request_id=request.request_id,
                workflow_type=request.workflow_type,
                success=final_state.get("error") is None,
                result=final_state.get("results", {}),
                execution_time=execution_time,
                error_message=final_state.get("error")
            )

            self.workflows_executed += 1

            logger.info(
                f"Workflow {workflow_key} completed in {execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(f"Workflow execution failed: {e}")

            return WorkflowResult(
                request_id=request.request_id,
                workflow_type=request.workflow_type,
                success=False,
                result={},
                execution_time=execution_time,
                error_message=str(e)
            )

    async def process_alert(self, alert_data: Dict[str, Any], metric_data: Dict[str, Any]) -> WorkflowResult:
        """Process an alert using the alert analysis workflow"""
        request = WorkflowRequest(
            request_id=str(uuid.uuid4()),
            workflow_type=WorkflowType.ALERT_ANALYSIS,
            parameters={
                "alert_data": alert_data,
                "metric_data": metric_data
            },
            priority=3
        )

        return await self.execute_workflow(request)

    async def perform_health_check(self) -> WorkflowResult:
        """Perform system health check"""
        request = WorkflowRequest(
            request_id=str(uuid.uuid4()),
            workflow_type=WorkflowType.HEALTH_CHECK,
            parameters={},
            priority=2
        )

        return await self.execute_workflow(request)

    async def analyze_system(self) -> WorkflowResult:
        """Perform comprehensive system analysis"""
        request = WorkflowRequest(
            request_id=str(uuid.uuid4()),
            workflow_type=WorkflowType.SYSTEM_ANALYSIS,
            parameters={},
            priority=1
        )

        return await self.execute_workflow(request)

    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        uptime = datetime.now() - self.start_time

        return {
            "is_running": self.is_running,
            "workflows_executed": self.workflows_executed,
            "uptime_seconds": uptime.total_seconds(),
            "active_workflows": len(self.active_workflows),
            "registered_agents": len(self.agents),
            "available_workflows": list(self.workflows.keys()),
            "agents_status": communication_hub.get_agent_statuses()
        }


# Global executor instance
executor = WatchTowerExecutor()

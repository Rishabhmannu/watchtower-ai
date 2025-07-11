"""
Analysis Agent for Intelligent Analysis and Correlation
File: backend/agents/analysis_agent.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict

from .base_agent import BaseAgent, AgentType, AgentMessage, MessageType, create_message
from .alert_agent import HealthAlert, HealthMetric
from core.service_registry import BankingServiceRegistry
from core.dashboard_registry import DashboardRegistry
from integrations.enhanced_prometheus_client import EnhancedPrometheusClient
from llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis performed"""
    ROOT_CAUSE = "root_cause"
    CORRELATION = "correlation"
    TREND = "trend"
    PREDICTION = "prediction"
    DEPENDENCY = "dependency"


@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    analysis_id: str
    analysis_type: AnalysisType
    trigger_event: str
    findings: List[str]
    confidence: float
    recommendations: List[str]
    affected_services: List[str]
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class ServiceDependency:
    """Service dependency relationship"""
    service: str
    depends_on: List[str]
    dependency_type: str  # "database", "cache", "api", "messaging"
    impact_level: str  # "high", "medium", "low"


class AnalysisAgent(BaseAgent):
    """Intelligent Analysis and Correlation Agent"""

    def __init__(self, agent_id: str = "analysis_agent"):
        super().__init__(agent_id, AgentType.ANALYSIS)

        # Initialize components
        self.service_registry = BankingServiceRegistry()
        self.dashboard_registry = DashboardRegistry()
        self.prometheus_client = EnhancedPrometheusClient()
        self.openai_client = OpenAIClient()

        # Analysis configuration
        self.analysis_history: List[AnalysisResult] = []
        self.correlation_cache: Dict[str, List[Tuple[str, float]]] = {}
        self.dependency_map: Dict[str, ServiceDependency] = {}

        # Pattern learning
        self.pattern_memory: Dict[str,
                                  List[Dict[str, Any]]] = defaultdict(list)
        self.correlation_threshold = 0.7

        # Initialize service dependencies
        self.initialize_service_dependencies()

        self.log_info(
            "Analysis Agent initialized with intelligent correlation capabilities")

    def initialize_service_dependencies(self):
        """Initialize service dependency map"""
        try:
            # Define known service dependencies in banking system
            dependencies = {
                "transaction_service": ServiceDependency(
                    service="transaction_service",
                    depends_on=["banking_mysql",
                                "banking_redis", "fraud_detection"],
                    dependency_type="database,cache,api",
                    impact_level="high"
                ),
                "account_service": ServiceDependency(
                    service="account_service",
                    depends_on=["banking_mysql"],
                    dependency_type="database",
                    impact_level="high"
                ),
                "auth_service": ServiceDependency(
                    service="auth_service",
                    depends_on=["banking_mysql"],
                    dependency_type="database",
                    impact_level="high"
                ),
                "notification_service": ServiceDependency(
                    service="notification_service",
                    depends_on=["banking_rabbitmq"],
                    dependency_type="messaging",
                    impact_level="medium"
                ),
                "fraud_detection": ServiceDependency(
                    service="fraud_detection",
                    depends_on=["banking_redis", "transaction_service"],
                    dependency_type="cache,api",
                    impact_level="high"
                ),
                "api_gateway": ServiceDependency(
                    service="api_gateway",
                    depends_on=["account_service",
                                "transaction_service", "auth_service"],
                    dependency_type="api",
                    impact_level="critical"
                )
            }

            self.dependency_map = dependencies
            self.log_info(
                f"Initialized {len(dependencies)} service dependencies")

        except Exception as e:
            self.log_error(f"Error initializing service dependencies: {e}")

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages"""
        try:
            if message.message_type == MessageType.ALERT:
                return await self._analyze_alert(message)
            elif message.message_type == MessageType.QUERY:
                return await self._handle_analysis_query(message)
            elif message.message_type == MessageType.STATUS:
                return await self._handle_status_request(message)
            else:
                self.log_warning(
                    f"Unknown message type: {message.message_type}")
                return None
        except Exception as e:
            self.log_error(f"Error processing message: {e}")
            return None

    async def background_task(self):
        """Background analysis tasks"""
        try:
            # Perform correlation analysis
            await self._perform_correlation_analysis()

            # Analyze patterns
            await self._analyze_patterns()

            # Generate insights
            await self._generate_insights()

            # Wait for next analysis cycle
            await asyncio.sleep(60)  # Run every minute

        except Exception as e:
            self.log_error(f"Error in background analysis task: {e}")

    async def _analyze_alert(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Analyze incoming alert and perform root cause analysis"""
        try:
            alert_data = message.content.get("alert", {})
            metric_data = message.content.get("metric", {})

            # Perform root cause analysis
            root_cause_analysis = await self._perform_root_cause_analysis(alert_data, metric_data)

            # Perform correlation analysis
            correlation_analysis = await self._perform_correlation_analysis_for_alert(alert_data)

            # Generate comprehensive analysis
            analysis_result = AnalysisResult(
                analysis_id=f"analysis_{int(datetime.now().timestamp())}",
                analysis_type=AnalysisType.ROOT_CAUSE,
                trigger_event=f"Alert: {alert_data.get('message', 'Unknown alert')}",
                findings=root_cause_analysis.get("findings", []),
                confidence=root_cause_analysis.get("confidence", 0.5),
                recommendations=root_cause_analysis.get("recommendations", []),
                affected_services=correlation_analysis.get(
                    "affected_services", []),
                timestamp=datetime.now(),
                details={
                    "alert_data": alert_data,
                    "metric_data": metric_data,
                    "correlation_data": correlation_analysis,
                    "root_cause_data": root_cause_analysis
                }
            )

            # Store analysis
            self.analysis_history.append(analysis_result)

            # Generate intelligent response
            response_message = await self._generate_analysis_response(analysis_result)

            self.log_info(
                f"Completed analysis for alert: {alert_data.get('message', 'Unknown')}")

            return create_message(
                sender=self.agent_id,
                recipient="broadcast",
                message_type=MessageType.INSIGHT,
                content={
                    "analysis_result": analysis_result.__dict__,
                    "response_message": response_message
                },
                priority=message.priority
            )

        except Exception as e:
            self.log_error(f"Error analyzing alert: {e}")
            return None

    async def _perform_root_cause_analysis(self, alert_data: Dict[str, Any], metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform root cause analysis for an alert"""
        try:
            service_name = alert_data.get("service_name", "")
            severity = alert_data.get("severity", "")

            findings = []
            recommendations = []
            confidence = 0.5

            # Check service dependencies
            if service_name in self.dependency_map:
                dependency = self.dependency_map[service_name]

                # Check if dependencies are healthy
                unhealthy_deps = await self._check_dependency_health(dependency.depends_on)
                if unhealthy_deps:
                    findings.append(
                        f"Dependency issues detected: {', '.join(unhealthy_deps)}")
                    recommendations.append(
                        f"Investigate {', '.join(unhealthy_deps)} services")
                    confidence += 0.3

            # Analyze metric patterns
            metric_name = metric_data.get("metric_name", "")
            current_value = metric_data.get("current_value", 0)

            if metric_name == "service_health" and current_value == 0:
                findings.append("Service is completely down")
                recommendations.append(
                    "Check service logs and restart if necessary")
                confidence += 0.4
            elif metric_name == "cache_hit_ratio" and current_value < 60:
                findings.append("Cache performance degraded significantly")
                recommendations.append(
                    "Investigate cache configuration and data patterns")
                confidence += 0.3

            # Analyze historical patterns
            historical_analysis = await self._analyze_historical_patterns(service_name, metric_name)
            if historical_analysis:
                findings.extend(historical_analysis.get("findings", []))
                recommendations.extend(
                    historical_analysis.get("recommendations", []))
                confidence += historical_analysis.get("confidence_boost", 0.1)

            # Use AI for additional insights
            ai_insights = await self._get_ai_insights(alert_data, metric_data, findings)
            if ai_insights:
                findings.extend(ai_insights.get("findings", []))
                recommendations.extend(ai_insights.get("recommendations", []))

            return {
                "findings": findings,
                "recommendations": recommendations,
                "confidence": min(confidence, 1.0),
                "analysis_method": "dependency_check,pattern_analysis,ai_insights"
            }

        except Exception as e:
            self.log_error(f"Error in root cause analysis: {e}")
            return {"findings": [], "recommendations": [], "confidence": 0.0}

    async def _check_dependency_health(self, dependencies: List[str]) -> List[str]:
        """Check health of service dependencies"""
        try:
            unhealthy_deps = []

            for dep in dependencies:
                # Query health of dependency
                health_query = f'up{{job=~".*{dep}.*"}}'
                try:
                    result = await self.prometheus_client.query_metric(health_query)

                    if result.get("status") == "success":
                        value = self._extract_metric_value(result)
                        if value is not None and value < 1.0:
                            unhealthy_deps.append(dep)
                    else:
                        unhealthy_deps.append(dep)

                except Exception as e:
                    self.log_warning(f"Could not check health of {dep}: {e}")

            return unhealthy_deps

        except Exception as e:
            self.log_error(f"Error checking dependency health: {e}")
            return []

    def _extract_metric_value(self, result: Dict[str, Any]) -> Optional[float]:
        """Extract numeric value from Prometheus response"""
        try:
            data = result.get("data", {})
            inner_data = data.get("data", {})
            result_data = inner_data.get("result", [])

            if result_data:
                value = result_data[0].get("value", [])
                if len(value) >= 2:
                    return float(value[1])
        except Exception:
            pass
        return None

    async def _perform_correlation_analysis_for_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform correlation analysis for a specific alert"""
        try:
            service_name = alert_data.get("service_name", "")
            affected_services = [service_name]

            # Check services that depend on this service
            for svc_name, dependency in self.dependency_map.items():
                if service_name in dependency.depends_on:
                    affected_services.append(svc_name)

            # Check services in same category
            service_category = alert_data.get("category", "")
            if service_category:
                category_services = [
                    svc.name for svc in self.service_registry.get_services_by_category(service_category)
                ]
                affected_services.extend(category_services)

            # Remove duplicates
            affected_services = list(set(affected_services))

            return {
                "affected_services": affected_services,
                "impact_level": self._calculate_impact_level(service_name),
                "correlation_score": 0.8 if len(affected_services) > 1 else 0.3
            }

        except Exception as e:
            self.log_error(f"Error in correlation analysis: {e}")
            return {"affected_services": [], "impact_level": "low", "correlation_score": 0.0}

    def _calculate_impact_level(self, service_name: str) -> str:
        """Calculate impact level of service failure"""
        if service_name in self.dependency_map:
            dependency = self.dependency_map[service_name]
            return dependency.impact_level

        # Check if other services depend on this one
        dependent_services = [
            svc_name for svc_name, dep in self.dependency_map.items()
            if service_name in dep.depends_on
        ]

        if len(dependent_services) > 3:
            return "critical"
        elif len(dependent_services) > 1:
            return "high"
        elif len(dependent_services) > 0:
            return "medium"
        else:
            return "low"

    async def _analyze_historical_patterns(self, service_name: str, metric_name: str) -> Optional[Dict[str, Any]]:
        """Analyze historical patterns for insights"""
        try:
            # Look for similar patterns in analysis history
            similar_patterns = [
                analysis for analysis in self.analysis_history
                if (service_name in analysis.affected_services or
                    service_name in analysis.trigger_event) and
                analysis.timestamp > datetime.now() - timedelta(days=7)
            ]

            if not similar_patterns:
                return None

            findings = []
            recommendations = []
            confidence_boost = 0.0

            # Analyze frequency
            if len(similar_patterns) > 2:
                findings.append(
                    f"Recurring issue: {len(similar_patterns)} similar incidents in last 7 days")
                recommendations.append(
                    "Implement preventive measures for recurring issue")
                confidence_boost += 0.2

            # Analyze resolution patterns
            resolved_patterns = [
                p for p in similar_patterns if p.details.get("resolved")]
            if resolved_patterns:
                common_solutions = self._find_common_solutions(
                    resolved_patterns)
                if common_solutions:
                    recommendations.extend(common_solutions)
                    confidence_boost += 0.1

            return {
                "findings": findings,
                "recommendations": recommendations,
                "confidence_boost": confidence_boost,
                "pattern_count": len(similar_patterns)
            }

        except Exception as e:
            self.log_error(f"Error analyzing historical patterns: {e}")
            return None

    def _find_common_solutions(self, resolved_patterns: List[AnalysisResult]) -> List[str]:
        """Find common solutions from resolved patterns"""
        try:
            all_recommendations = []
            for pattern in resolved_patterns:
                all_recommendations.extend(pattern.recommendations)

            # Count frequency of recommendations
            recommendation_counts = {}
            for rec in all_recommendations:
                recommendation_counts[rec] = recommendation_counts.get(
                    rec, 0) + 1

            # Return recommendations that appear in multiple patterns
            common_solutions = [
                rec for rec, count in recommendation_counts.items()
                if count > 1
            ]

            return common_solutions

        except Exception as e:
            self.log_error(f"Error finding common solutions: {e}")
            return []

    async def _get_ai_insights(self, alert_data: Dict[str, Any], metric_data: Dict[str, Any], findings: List[str]) -> Optional[Dict[str, Any]]:
        """Get AI-powered insights for the alert"""
        try:
            # Prepare context for AI
            context = {
                "alert": alert_data,
                "metric": metric_data,
                "current_findings": findings,
                "service_dependencies": self.dependency_map,
                # Last 5 analyses
                "analysis_history": [a.__dict__ for a in self.analysis_history[-5:]]
            }

            # Generate AI insights using OpenAI
            prompt = f"""
            You are an expert system administrator analyzing a banking system alert.
            
            Alert Details:
            - Service: {alert_data.get('service_name', 'Unknown')}
            - Severity: {alert_data.get('severity', 'Unknown')}
            - Message: {alert_data.get('message', 'Unknown')}
            
            Current Findings:
            {chr(10).join(findings) if findings else 'No findings yet'}
            
            System Context:
            - This is a banking system with 31+ services
            - Services include: core banking, ML detection, infrastructure, messaging
            - System uses Prometheus for monitoring
            
            Provide additional insights and recommendations focusing on:
            1. Potential root causes not yet identified
            2. Immediate action items
            3. Preventive measures
            
            Respond in JSON format with 'findings' and 'recommendations' arrays.
            """

            # Note: In a real implementation, you would call OpenAI API here
            # For now, we'll return some intelligent defaults

            ai_insights = {
                "findings": [
                    "Consider checking resource utilization patterns",
                    "Review recent deployment or configuration changes"
                ],
                "recommendations": [
                    "Monitor resource usage trends",
                    "Review application logs for error patterns",
                    "Consider scaling if resource-related issue"
                ]
            }

            return ai_insights

        except Exception as e:
            self.log_error(f"Error getting AI insights: {e}")
            return None

    async def _generate_analysis_response(self, analysis_result: AnalysisResult) -> str:
        """Generate human-readable analysis response"""
        try:
            confidence_desc = "high" if analysis_result.confidence > 0.7 else "medium" if analysis_result.confidence > 0.4 else "low"

            response = f"🔍 **Analysis Complete** (Confidence: {confidence_desc})\n\n"
            response += f"**Trigger**: {analysis_result.trigger_event}\n\n"

            if analysis_result.findings:
                response += "**🔎 Key Findings:**\n"
                for finding in analysis_result.findings:
                    response += f"• {finding}\n"
                response += "\n"

            if analysis_result.recommendations:
                response += "**💡 Recommendations:**\n"
                for rec in analysis_result.recommendations:
                    response += f"• {rec}\n"
                response += "\n"

            if analysis_result.affected_services:
                response += f"**🔗 Affected Services:** {', '.join(analysis_result.affected_services)}\n\n"

            response += f"**📊 Analysis ID:** {analysis_result.analysis_id}"

            return response

        except Exception as e:
            self.log_error(f"Error generating analysis response: {e}")
            return "Analysis completed but response generation failed"

    async def _perform_correlation_analysis(self):
        """Perform background correlation analysis"""
        try:
            # This would perform correlation analysis between different metrics
            # For now, we'll implement a basic version

            current_time = datetime.now()

            # Analyze correlations every 5 minutes
            if not hasattr(self, '_last_correlation_analysis'):
                self._last_correlation_analysis = current_time

            if current_time - self._last_correlation_analysis < timedelta(minutes=5):
                return

            self._last_correlation_analysis = current_time

            # Get system metrics for correlation
            system_metrics = await self._get_system_metrics_for_correlation()

            # Analyze correlations
            correlations = self._calculate_correlations(system_metrics)

            # Store strong correlations
            for correlation in correlations:
                if correlation["strength"] > self.correlation_threshold:
                    self.correlation_cache[correlation["metric1"]] = [
                        (correlation["metric2"], correlation["strength"])
                    ]

            self.log_info(
                f"Correlation analysis completed. Found {len(correlations)} correlations.")

        except Exception as e:
            self.log_error(f"Error in correlation analysis: {e}")

    async def _get_system_metrics_for_correlation(self) -> Dict[str, List[float]]:
        """Get system metrics for correlation analysis"""
        try:
            metrics = {}

            # Define key metrics to correlate
            key_metrics = {
                "cache_hit_ratio": "banking_cache_hits_total / (banking_cache_hits_total + banking_cache_misses_total) * 100",
                "db_connections": "banking_db_pool_connections_active",
                "response_time": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "error_rate": "rate(http_requests_total{status=~\"5..\"}[5m])"
            }

            for metric_name, query in key_metrics.items():
                try:
                    result = await self.prometheus_client.query_metric(query)
                    value = self._extract_metric_value(result)

                    if value is not None:
                        if metric_name not in metrics:
                            metrics[metric_name] = []
                        metrics[metric_name].append(value)

                except Exception as e:
                    self.log_warning(
                        f"Could not get metric {metric_name}: {e}")

            return metrics

        except Exception as e:
            self.log_error(f"Error getting system metrics: {e}")
            return {}

    def _calculate_correlations(self, metrics: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """Calculate correlations between metrics"""
        try:
            correlations = []
            metric_names = list(metrics.keys())

            for i in range(len(metric_names)):
                for j in range(i + 1, len(metric_names)):
                    metric1 = metric_names[i]
                    metric2 = metric_names[j]

                    if metric1 in metrics and metric2 in metrics:
                        values1 = metrics[metric1]
                        values2 = metrics[metric2]

                        if len(values1) > 1 and len(values2) > 1:
                            correlation = self._calculate_correlation_coefficient(
                                values1, values2)

                            correlations.append({
                                "metric1": metric1,
                                "metric2": metric2,
                                "strength": abs(correlation),
                                "direction": "positive" if correlation > 0 else "negative"
                            })

            return correlations

        except Exception as e:
            self.log_error(f"Error calculating correlations: {e}")
            return []

    def _calculate_correlation_coefficient(self, values1: List[float], values2: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        try:
            n = min(len(values1), len(values2))
            if n < 2:
                return 0.0

            # Take last n values
            x = values1[-n:]
            y = values2[-n:]

            # Calculate means
            mean_x = sum(x) / n
            mean_y = sum(y) / n

            # Calculate correlation coefficient
            numerator = sum((x[i] - mean_x) * (y[i] - mean_y)
                            for i in range(n))

            sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
            sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))

            denominator = (sum_sq_x * sum_sq_y) ** 0.5

            if denominator == 0:
                return 0.0

            return numerator / denominator

        except Exception as e:
            self.log_error(f"Error calculating correlation coefficient: {e}")
            return 0.0

    async def _analyze_patterns(self):
        """Analyze patterns in system behavior"""
        try:
            # This would analyze patterns in the analysis history
            # For now, implement basic pattern detection

            current_time = datetime.now()
            recent_analyses = [
                analysis for analysis in self.analysis_history
                if current_time - analysis.timestamp < timedelta(hours=24)
            ]

            if len(recent_analyses) < 3:
                return

            # Detect recurring issues
            issue_patterns = {}
            for analysis in recent_analyses:
                for finding in analysis.findings:
                    if finding in issue_patterns:
                        issue_patterns[finding] += 1
                    else:
                        issue_patterns[finding] = 1

            # Identify patterns that occur frequently
            frequent_patterns = [
                pattern for pattern, count in issue_patterns.items()
                if count > 2
            ]

            if frequent_patterns:
                self.log_info(
                    f"Detected {len(frequent_patterns)} recurring patterns")

                # Store patterns for future reference
                for pattern in frequent_patterns:
                    self.pattern_memory["frequent_issues"].append({
                        "pattern": pattern,
                        "occurrences": issue_patterns[pattern],
                        "last_seen": current_time.isoformat()
                    })

        except Exception as e:
            self.log_error(f"Error analyzing patterns: {e}")

    async def _generate_insights(self):
        """Generate proactive insights"""
        try:
            # This would generate insights based on analysis history and patterns
            # For now, implement basic insight generation

            insights = []

            # Analyze analysis history for insights
            if len(self.analysis_history) > 5:
                latest_analyses = self.analysis_history[-5:]

                # Check for increasing alert frequency
                alert_frequency = len(latest_analyses)
                if alert_frequency > 3:
                    insights.append(
                        "Alert frequency has increased - consider proactive maintenance")

                # Check for common affected services
                affected_services = []
                for analysis in latest_analyses:
                    affected_services.extend(analysis.affected_services)

                service_counts = {}
                for service in affected_services:
                    service_counts[service] = service_counts.get(
                        service, 0) + 1

                frequently_affected = [
                    service for service, count in service_counts.items()
                    if count > 2
                ]

                if frequently_affected:
                    insights.append(
                        f"Services frequently affected: {', '.join(frequently_affected)}")

            # Store insights
            if insights:
                self.update_context("recent_insights", insights)
                self.log_info(f"Generated {len(insights)} system insights")

        except Exception as e:
            self.log_error(f"Error generating insights: {e}")

    async def _handle_analysis_query(self, message: AgentMessage) -> AgentMessage:
        """Handle analysis query from other agents"""
        try:
            query_content = message.content
            query_type = query_content.get("type")

            if query_type == "correlation":
                service_name = query_content.get("service_name")
                correlations = self.correlation_cache.get(service_name, [])

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={"correlations": correlations}
                )

            elif query_type == "dependencies":
                service_name = query_content.get("service_name")
                dependencies = self.dependency_map.get(service_name, None)

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={
                        "dependencies": dependencies.__dict__ if dependencies else None}
                )

            elif query_type == "recent_analyses":
                recent_analyses = [
                    analysis.__dict__ for analysis in self.analysis_history[-10:]
                ]

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={"analyses": recent_analyses}
                )

        except Exception as e:
            self.log_error(f"Error handling analysis query: {e}")

        return create_message(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content={"error": "Unable to process analysis query"}
        )

    async def _handle_status_request(self, message: AgentMessage) -> AgentMessage:
        """Handle status request"""
        status_data = self.get_status()
        status_data.update({
            "analyses_completed": len(self.analysis_history),
            "correlations_tracked": len(self.correlation_cache),
            "dependencies_mapped": len(self.dependency_map),
            "patterns_detected": len(self.pattern_memory)
        })

        return create_message(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content={"status": status_data}
        )

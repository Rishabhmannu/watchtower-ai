"""
Enhanced OpenAI Client with Dashboard and Service Registry Integration
File: backend/llm/openai_client.py
"""

from openai import OpenAI
from core.config import settings
import logging
from typing import Dict, List, Optional, Any
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

        # Cache for system context to avoid repeated lookups
        self._system_context = None
        self._dashboard_context = None

    def _get_system_context(self) -> str:
        """Get comprehensive system context for prompts"""
        if self._system_context is None:
            try:
                # Import here to avoid circular imports
                from core.service_registry import BankingServiceRegistry
                from core.dashboard_registry import DashboardRegistry

                service_registry = BankingServiceRegistry()
                dashboard_registry = DashboardRegistry()

                # Build comprehensive system context
                services_by_category = {}
                for category in service_registry.get_categories():
                    services = service_registry.get_services_by_category(
                        category)
                    services_by_category[category.value] = [
                        {
                            "name": svc.name,
                            "display_name": svc.display_name,
                            "port": svc.port,
                            "prometheus_job": svc.prometheus_job
                        }
                        for svc in services
                    ]

                # Get dashboard context
                dashboard_stats = dashboard_registry.get_registry_stats()
                categories = dashboard_registry.get_all_categories()

                self._system_context = f"""
BANKING SYSTEM OVERVIEW:
Total Services: {service_registry.get_services_count()}
Service Categories: {', '.join([cat.value for cat in service_registry.get_categories()])}

CORE BANKING SERVICES:
{self._format_services(services_by_category.get('core_banking', []))}

ML & DETECTION SERVICES:
{self._format_services(services_by_category.get('ml_detection', []))}

INFRASTRUCTURE SERVICES:
{self._format_services(services_by_category.get('infrastructure', []))}

MESSAGING SERVICES:
{self._format_services(services_by_category.get('messaging', []))}

CACHE & PERFORMANCE SERVICES:
{self._format_services(services_by_category.get('cache_performance', []))}

DATABASE SERVICES:
{self._format_services(services_by_category.get('database_storage', []))}

DASHBOARD INTEGRATION:
Total Dashboards: {dashboard_stats.get('total_dashboards', 0)}
Total Panels: {dashboard_stats.get('total_panels', 0)}
Dashboard Categories: {', '.join(categories)}

COMMON METRICS AVAILABLE:
- Service Health: up{{job="<job_name>"}}
- Cache Hit Ratio: banking_cache_hits_total / (banking_cache_hits_total + banking_cache_misses_total) * 100
- Transaction Rates: rate(transaction_requests_total[5m])
- Response Times: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
- Error Rates: rate(http_requests_total{{status=~"5.."}}[5m])
- Container Resources: container_cpu_usage_seconds_total, container_memory_usage_bytes
- Database Connections: banking_db_pool_connections_active
- Message Queue Metrics: banking_unprocessed_messages
- Kubernetes Metrics: k8s_pod_count_total, k8s_scaling_events_total
"""

            except Exception as e:
                logger.error(f"Error building system context: {e}")
                self._system_context = "System context unavailable"

        return self._system_context

    def _format_services(self, services: List[Dict]) -> str:
        """Format services for prompt"""
        if not services:
            return "None"

        formatted = []
        for svc in services:
            formatted.append(
                f"  - {svc['display_name']} ({svc['name']}) - Port {svc['port']} - Job: {svc['prometheus_job']}")

        return "\n".join(formatted)

    async def natural_language_to_promql(self, user_query: str) -> str:
        """Convert natural language query to PromQL with enhanced context"""
        system_context = self._get_system_context()

        system_prompt = f"""You are an expert at converting natural language queries about banking systems to PromQL queries.

{system_context}

CONVERSION RULES:
1. For service health queries, use: up{{job="<prometheus_job>"}}
2. For specific services, include instance filters when using banking-services job
3. For cache metrics, use global banking_cache_* metrics
4. For transaction metrics, use banking or transaction prefixed metrics
5. For container metrics, use container_* metrics
6. For database metrics, use banking_db_* metrics
7. For message queue metrics, use banking_*_messages metrics
8. For kubernetes metrics, use k8s_* metrics

EXAMPLES:
- "How are banking services?" → up{{job="banking-services"}}
- "Cache hit ratio" → banking_cache_hits_total / (banking_cache_hits_total + banking_cache_misses_total) * 100
- "Transaction service health" → up{{job="banking-services", instance="transaction-service:8082"}}
- "Redis connections" → redis_connected_clients
- "Database connections" → banking_db_pool_connections_active
- "Container CPU usage" → rate(container_cpu_usage_seconds_total[5m])

Convert the user query to a PromQL query. Return ONLY the PromQL query, nothing else.

User query: {user_query}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=150,
                temperature=0.1
            )

            promql_query = response.choices[0].message.content.strip()
            # Remove any backticks or code block markers
            promql_query = promql_query.replace(
                "```", "").replace("`", "").strip()

            logger.info(f"Converted '{user_query}' to PromQL: {promql_query}")
            return promql_query

        except Exception as e:
            logger.error(f"Error converting to PromQL: {e}")
            return "up"  # fallback to basic health check

    async def explain_metrics(self, user_query: str, metric_data: Any) -> str:
        """Explain metric data in natural language with banking context"""
        system_context = self._get_system_context()

        system_prompt = f"""You are WatchTower AI, an intelligent monitoring assistant for banking systems.

{system_context}

EXPLANATION GUIDELINES:
1. Always start with a clear, direct answer to the user's question
2. Use banking terminology and business context
3. Include specific numbers and percentages when available
4. Use emojis for visual clarity: ✅ (healthy), ❌ (unhealthy), ⚠️ (warning), 🔍 (analysis), 💡 (insight), 🚨 (alert)
5. Explain what the metrics mean for business operations
6. Provide actionable insights when possible
7. Keep explanations concise but comprehensive
8. Use professional but friendly tone

RESPONSE FORMAT:
- Start with status summary
- Include key metrics with business context
- Add insights or recommendations
- End with next steps if needed

Focus on banking system reliability, performance, and business impact."""

        user_prompt = f"""
User asked: {user_query}

Metric data: {metric_data}

Explain this data in a helpful way for banking system monitoring, focusing on:
1. Current system health and status
2. Key performance indicators
3. Business impact and implications
4. Any recommendations or next steps
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated explanation for query: {user_query}")
            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "I'm having trouble analyzing the data right now. Please try again."

    async def analyze_dashboard_query(self, user_query: str, relevant_panels: List[Dict]) -> str:
        """Analyze query against available dashboard panels"""
        try:
            if not relevant_panels:
                return await self.natural_language_to_promql(user_query)

            # Build context from relevant panels
            panel_context = "RELEVANT DASHBOARD PANELS:\n"
            for panel in relevant_panels[:5]:  # Limit to top 5
                panel_context += f"- {panel.get('title', 'Unknown')}: {panel.get('query', 'No query')}\n"

            system_prompt = f"""You are an expert at analyzing banking system queries against dashboard panels.

{self._get_system_context()}

{panel_context}

Based on the user query and relevant dashboard panels above, choose the BEST PromQL query that matches the user's intent.

Rules:
1. If a dashboard panel query directly matches the user intent, use it
2. If multiple panels are relevant, choose the most specific one
3. If no panels match well, generate a new PromQL query
4. Always return a valid PromQL query

User query: {user_query}

Return only the PromQL query, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=100,
                temperature=0.1
            )

            promql_query = response.choices[0].message.content.strip()
            promql_query = promql_query.replace(
                "```", "").replace("`", "").strip()

            logger.info(
                f"Dashboard-aware query for '{user_query}': {promql_query}")
            return promql_query

        except Exception as e:
            logger.error(f"Error analyzing dashboard query: {e}")
            return await self.natural_language_to_promql(user_query)

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, test connection"}],
                max_tokens=10
            )
            logger.info("OpenAI connection successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection failed: {e}")
            return False

    def clear_context_cache(self):
        """Clear cached system context to force refresh"""
        self._system_context = None
        self._dashboard_context = None
        logger.info("OpenAI client context cache cleared")

    async def get_query_suggestions(self, partial_query: str = "") -> List[str]:
        """Get smart query suggestions based on system context"""
        try:
            system_context = self._get_system_context()

            prompt = f"""Based on the banking system below, generate 8 helpful query suggestions for monitoring.

{system_context}

Current partial query: "{partial_query}"

Generate practical questions that users might ask about:
1. Service health and status
2. Performance metrics
3. Cache performance
4. Database operations
5. Transaction processing
6. System overview
7. Error monitoring
8. Resource utilization

Return only the suggestions, one per line, no numbering or extra text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            suggestions = response.choices[0].message.content.strip().split(
                '\n')
            return [s.strip() for s in suggestions if s.strip()]

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return [
                "How are the banking services doing?",
                "What's the cache hit ratio?",
                "Show me transaction service performance",
                "Are there any unhealthy services?",
                "What's the system overview?",
                "Check database connection status",
                "Show me error rates",
                "How is container resource usage?"
            ]

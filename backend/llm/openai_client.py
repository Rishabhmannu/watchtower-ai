from openai import OpenAI
from core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def natural_language_to_promql(self, user_query: str) -> str:
        """Convert natural language query to PromQL"""
        system_prompt = f"""You are an expert at converting natural language queries about banking systems to PromQL queries.

Available banking metrics:
- up{{job="banking-services"}} - Health status of banking services
- redis_connected_clients - Number of Redis connections
- redis_cache_hit_ratio - Cache hit ratio percentage
- transaction_requests_total - Total transaction requests
- http_request_duration_seconds - HTTP response times
- http_requests_total{{status=~"5.*"}} - HTTP 5xx errors

Banking services available:
- api-gateway:8080
- account-service:8081
- transaction-service:8082
- auth-service:8083
- notification-service:8084
- fraud-detection:8085

Convert the user query to a PromQL query. Return ONLY the PromQL query, nothing else.

User query: {user_query}"""

        try:
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
            logger.info(f"Converted '{user_query}' to PromQL: {promql_query}")
            return promql_query

        except Exception as e:
            logger.error(f"Error converting to PromQL: {e}")
            return "up"  # fallback to basic health check

    async def explain_metrics(self, user_query: str, metric_data: dict) -> str:
        """Explain metric data in natural language"""
        system_prompt = """You are WatchTower AI, an intelligent monitoring assistant for banking systems.

Explain the metric data in a friendly, conversational way. Include:
- Current status (healthy/unhealthy)
- Key numbers and what they mean
- Use emojis for visual clarity (✅❌🔍💡🚨)
- Keep it concise but informative

Focus on banking context and business impact."""

        user_prompt = f"""
User asked: {user_query}

Metric data: {metric_data}

Explain this data in a helpful way for banking system monitoring.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated explanation for query: {user_query}")
            return explanation

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "I'm having trouble analyzing the data right now. Please try again."

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

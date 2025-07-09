import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Prometheus Configuration
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

    # Grafana Configuration
    GRAFANA_URL: str = os.getenv("GRAFANA_URL", "http://localhost:3000")

    # Banking System Configuration
    BANKING_SERVICES = [
        "api-gateway:8080",
        "account-service:8081",
        "transaction-service:8082",
        "auth-service:8083",
        "notification-service:8084",
        "fraud-detection:8085"
    ]

    # Common Banking Metrics
    BANKING_METRICS = {
        "health": "up{job=\"banking-services\"}",
        "cache": "redis_connected_clients",
        "cache_hit_ratio": "redis_cache_hit_ratio",
        "transactions": "transaction_requests_total",
        "response_time": "http_request_duration_seconds",
        "error_rate": "http_requests_total{status=~\"5.*\"}"
    }


# Create settings instance
settings = Settings()

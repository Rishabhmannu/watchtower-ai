#!/usr/bin/env python3
"""
Test script to debug import issues
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

print("Testing imports...")
print(f"Python path: {backend_dir}")

try:
    from integrations.prometheus_client import PrometheusClient
    print("✅ PrometheusClient import successful")
except Exception as e:
    print(f"❌ PrometheusClient import failed: {e}")

try:
    from llm.openai_client import OpenAIClient
    print("✅ OpenAIClient import successful")
except Exception as e:
    print(f"❌ OpenAIClient import failed: {e}")

try:
    from core.config import settings
    print("✅ Config import successful")
    print(f"OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")
except Exception as e:
    print(f"❌ Config import failed: {e}")

print("Import test completed!")

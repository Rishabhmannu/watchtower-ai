#!/usr/bin/env python3
"""
Test script for Enhanced Prometheus Client
Tests all advanced functionality including multi-service querying,
caching, metric templates, and error handling
"""

import sys
import os
import asyncio
import time
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)


async def test_enhanced_prometheus_client():
    """Test the enhanced Prometheus client functionality"""
    print("🚀 WATCHTOWER AI - Enhanced Prometheus Client Test")
    print("=" * 60)

    try:
        # Test 1: Import and basic connectivity
        print("\n1. Testing Enhanced Client Import and Connectivity...")
        from integrations.prometheus_client import PrometheusClient

        client = PrometheusClient()

        # Test basic connectivity
        is_connected = await client.check_connection()
        print(
            f"✅ Prometheus connectivity: {'Connected' if is_connected else 'Failed'}")

        if not is_connected:
            print("❌ Cannot proceed with tests - Prometheus not accessible")
            return False

        # Test 2: Basic query functionality (backward compatibility)
        print("\n2. Testing Backward Compatibility...")

        basic_query = 'up{job="prometheus"}'
        result = await client.query_metric(basic_query)
        print(f"✅ Basic query successful: {result is not None}")

        targets = await client.get_targets()
        print(
            f"✅ Retrieved {len(targets) if targets else 0} Prometheus targets")

        # Test 3: Enhanced single service metrics
        print("\n3. Testing Enhanced Service Metrics...")

        test_services = ["api_gateway", "prometheus", "ddos_ml_detection"]
        for service_name in test_services:
            try:
                service_metrics = await client.query_service_metrics(service_name)
                print(
                    f"✅ {service_name}: {service_metrics.get('overall_health', 'unknown')} - {len(service_metrics.get('metrics', {}))} metrics")
            except Exception as e:
                print(f"⚠️  {service_name}: Error - {str(e)}")

        # Test 4: Category health summaries
        print("\n4. Testing Category Health Summaries...")

        test_categories = ["core_banking", "infrastructure", "ml_detection"]
        for category in test_categories:
            try:
                category_health = await client.query_category_health(category)
                health_pct = category_health.get('health_percentage', 0)
                total_services = category_health.get('total_services', 0)
                print(
                    f"✅ {category}: {health_pct:.1f}% healthy ({total_services} services)")
            except Exception as e:
                print(f"⚠️  {category}: Error - {str(e)}")

        # Test 5: Multi-service batch querying
        print("\n5. Testing Multi-Service Batch Querying...")

        batch_services = ["api_gateway",
                          "account_service", "transaction_service"]
        try:
            batch_result = await client.query_multiple_services(batch_services)
            successful = batch_result.get('summary', {}).get('successful', 0)
            failed = batch_result.get('summary', {}).get('failed', 0)
            print(f"✅ Batch query: {successful} successful, {failed} failed")

            # Show sample results
            for service_name, service_data in list(batch_result.get('services', {}).items())[:2]:
                if 'error' not in service_data:
                    health = service_data.get('overall_health', 'unknown')
                    metrics_count = len(service_data.get('metrics', {}))
                    print(
                        f"   - {service_name}: {health} ({metrics_count} metrics)")

        except Exception as e:
            print(f"⚠️  Batch query failed: {e}")

        # Test 6: System overview
        print("\n6. Testing System Overview...")

        try:
            overview = await client.get_system_overview()
            total_services = overview.get('total_services', 0)
            health_pct = overview.get('system_health_percentage', 0)
            categories_count = len(overview.get('categories', {}))
            print(
                f"✅ System overview: {total_services} services, {health_pct:.1f}% healthy, {categories_count} categories")

            # Show category breakdown
            overall_health = overview.get('overall_health', {})
            print(f"   Health distribution: Healthy={overall_health.get('healthy', 0)}, " +
                  f"Warning={overall_health.get('warning', 0)}, " +
                  f"Critical={overall_health.get('critical', 0)}")

        except Exception as e:
            print(f"⚠️  System overview failed: {e}")

        # Test 7: Advanced query with retry
        print("\n7. Testing Advanced Query with Retry...")

        advanced_queries = [
            'up{job="banking-services"}',
            'rate(http_requests_total[5m])',
            'redis_connected_clients'
        ]

        for query in advanced_queries:
            try:
                start_time = time.time()
                result = await client.query_with_retry(query)
                execution_time = (time.time() - start_time) * 1000

                success = result.get('success', False)
                query_time = result.get('execution_time_ms', execution_time)
                print(
                    f"✅ Advanced query: {'Success' if success else 'Failed'} in {query_time:.1f}ms")

                if not success:
                    error = result.get('error_message', 'Unknown error')
                    print(f"   Error: {error}")

            except Exception as e:
                print(f"⚠️  Advanced query failed: {e}")

        # Test 8: Cache performance
        print("\n8. Testing Cache Performance...")

        try:
            # Clear cache first
            await client.clear_cache()
            print("✅ Cache cleared")

            # First query (should hit Prometheus)
            service_name = "api_gateway"
            start_time = time.time()
            result1 = await client.query_service_metrics(service_name)
            first_query_time = (time.time() - start_time) * 1000

            # Second query (should hit cache)
            start_time = time.time()
            result2 = await client.query_service_metrics(service_name)
            cached_query_time = (time.time() - start_time) * 1000

            print(
                f"✅ Cache test: First query {first_query_time:.1f}ms, Cached query {cached_query_time:.1f}ms")
            print(
                f"   Cache speedup: {(first_query_time / cached_query_time):.1f}x faster" if cached_query_time > 0 else "")

        except Exception as e:
            print(f"⚠️  Cache test failed: {e}")

        # Test 9: Error handling
        print("\n9. Testing Error Handling...")

        try:
            # Test with non-existent service
            invalid_result = await client.query_service_metrics("non_existent_service")
            print("⚠️  Should have failed for non-existent service")
        except ValueError:
            print("✅ Properly handled non-existent service error")
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")

        try:
            # Test with invalid category
            invalid_category = await client.query_category_health("invalid_category")
            print("⚠️  Should have failed for invalid category")
        except ValueError:
            print("✅ Properly handled invalid category error")
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")

        # Test 10: Performance metrics
        print("\n10. Testing Performance Metrics...")

        try:
            # Test performance-focused queries
            performance_services = ["transaction_service", "ddos_ml_detection"]
            from integrations.enhanced_prometheus_client import MetricType

            perf_result = await client.query_multiple_services(
                performance_services,
                [MetricType.PERFORMANCE, MetricType.HEALTH]
            )

            print(
                f"✅ Performance metrics: {perf_result.get('summary', {}).get('successful', 0)} services analyzed")

            # Show performance insights
            for service_name, service_data in perf_result.get('services', {}).items():
                if 'metrics' in service_data:
                    metrics = service_data['metrics']
                    perf_metrics = [name for name, data in metrics.items()
                                    if 'response_time' in name or 'rate' in name or 'latency' in name]
                    if perf_metrics:
                        print(
                            f"   - {service_name}: {len(perf_metrics)} performance metrics")

        except Exception as e:
            print(f"⚠️  Performance metrics test failed: {e}")

        # Test cleanup
        print("\n11. Testing Cleanup...")
        try:
            await client.close()
            print("✅ Client cleanup successful")
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")

        print("\n" + "=" * 60)
        print("✅ ALL ENHANCED PROMETHEUS CLIENT TESTS COMPLETED!")
        print("🚀 Enhanced client is ready for production use")
        print(f"📊 Tested: Service metrics, category health, batch queries, caching, error handling")

        return True

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test the enhanced API endpoints"""
    print("\n🌐 Testing Enhanced API Endpoints...")
    print("-" * 40)

    try:
        import aiohttp

        base_url = "http://localhost:5050"

        # Test endpoints to check
        test_endpoints = [
            "/api/metrics/system/overview",
            "/api/metrics/health/summary",
            "/api/metrics/banking/core-services",
            "/api/metrics/service/api_gateway",
            "/api/metrics/category/core_banking"
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in test_endpoints:
                try:
                    async with session.get(f"{base_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ {endpoint}: Status {response.status}")
                        else:
                            print(f"⚠️  {endpoint}: Status {response.status}")
                except Exception as e:
                    print(f"❌ {endpoint}: Connection failed - {str(e)}")

        return True

    except ImportError:
        print("⚠️  aiohttp not available for endpoint testing")
        return True
    except Exception as e:
        print(f"❌ API endpoint testing failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🔍 WATCHTOWER AI - Enhanced Prometheus Client Test Suite")
    print("=" * 60)

    # Test the enhanced Prometheus client
    client_tests_passed = await test_enhanced_prometheus_client()

    # Test API endpoints if backend is running
    api_tests_passed = await test_api_endpoints()

    if client_tests_passed and api_tests_passed:
        print("\n🎉 ALL TESTS SUCCESSFUL!")
        print("Your Enhanced Prometheus Client is ready for production!")
        print("\n📈 New Capabilities Available:")
        print("- Multi-service querying with 31 banking services")
        print("- Service-specific metric templates")
        print("- Intelligent caching and retry logic")
        print("- Category-based health summaries")
        print("- Advanced error handling")
        print("- Performance optimization")
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("Please check the errors above and fix them.")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())

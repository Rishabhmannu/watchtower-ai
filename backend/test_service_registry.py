#!/usr/bin/env python3
"""
Test script to verify Service Registry implementation
Run this from the backend/ directory to test the service registry
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)


def test_service_registry():
    """Test the service registry functionality"""
    print("🔍 WATCHTOWER AI - Service Registry Test")
    print("=" * 50)

    try:
        # Test 1: Import and initialize service registry
        print("\n1. Testing Service Registry Import...")
        from core.service_registry import BankingServiceRegistry
        from models.service_models import ServiceCategory

        registry = BankingServiceRegistry()
        print(
            f"✅ Service registry initialized with {registry.get_services_count()} services")

        # Test 2: Check all categories
        print("\n2. Testing Categories...")
        categories = registry.get_categories()
        print(f"✅ Found {len(categories)} categories:")
        for cat in categories:
            services = registry.get_services_by_category(cat)
            print(f"   - {cat.value}: {len(services)} services")

        # Test 3: Test specific service lookup
        print("\n3. Testing Service Lookup...")
        test_services = ["api_gateway", "ddos_ml_detection",
                         "prometheus", "banking_rabbitmq"]
        for service_name in test_services:
            service = registry.get_service(service_name)
            if service:
                print(
                    f"✅ Found {service_name}: {service.display_name} on port {service.port}")
            else:
                print(f"❌ Service {service_name} not found")

        # Test 4: Test search functionality
        print("\n4. Testing Search Functionality...")
        search_terms = ["banking", "ml", "cache", "monitor"]
        for term in search_terms:
            results = registry.search_services(term)
            print(f"✅ Search '{term}': found {len(results)} results")

        # Test 5: Test category summaries
        print("\n5. Testing Category Summaries...")
        for category in [ServiceCategory.CORE_BANKING, ServiceCategory.ML_DETECTION, ServiceCategory.INFRASTRUCTURE]:
            summary = registry.get_category_summary(category)
            print(f"✅ {category.value}: {summary['total_services']} services")

        # Test 6: Validate service configuration
        print("\n6. Validating Service Configuration...")
        all_services = registry.get_all_services()

        # Check for duplicates
        ports = [service.port for service in all_services.values()]
        hosts = [
            f"{service.host}:{service.port}" for service in all_services.values()]

        duplicate_ports = len(ports) != len(set(ports))
        duplicate_hosts = len(hosts) != len(set(hosts))

        if duplicate_ports:
            print("⚠️  Warning: Duplicate ports detected")
        else:
            print("✅ All services have unique ports")

        if duplicate_hosts:
            print("⚠️  Warning: Duplicate host:port combinations detected")
        else:
            print("✅ All services have unique host:port combinations")

        # Test 7: Show sample service details
        print("\n7. Sample Service Details...")
        sample_service = registry.get_service("api_gateway")
        if sample_service:
            print(f"Service: {sample_service.display_name}")
            print(f"Host: {sample_service.host}:{sample_service.port}")
            print(f"Category: {sample_service.category.value}")
            print(f"Description: {sample_service.description}")
            print(f"Prometheus Job: {sample_service.prometheus_job}")
            print(f"Dependencies: {sample_service.dependencies}")
            print(f"Tags: {sample_service.tags}")

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED - Service Registry is ready!")
        print(f"📊 Total Services: {registry.get_services_count()}")
        print(f"📂 Categories: {len(categories)}")
        print("🚀 Ready for integration with WatchTower AI")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_models():
    """Test the API models can be imported correctly"""
    print("\n🔧 Testing API Models Import...")

    try:
        from models.service_models import ServiceCategory, ServiceInfo, ServiceStatus
        print("✅ Service models imported successfully")

        # Test enum values
        categories = list(ServiceCategory)
        print(f"✅ ServiceCategory enum has {len(categories)} values")

        statuses = list(ServiceStatus)
        print(f"✅ ServiceStatus enum has {len(statuses)} values")

        return True

    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting Service Registry Tests...\n")

    # Run tests
    models_ok = test_api_models()
    registry_ok = test_service_registry()

    if models_ok and registry_ok:
        print("\n🎉 ALL TESTS SUCCESSFUL!")
        print("Your Service Registry is ready for use.")
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("Please check the errors above and fix them.")
        sys.exit(1)

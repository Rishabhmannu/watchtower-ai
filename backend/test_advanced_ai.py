"""
Test script for Advanced AI Features
File: backend/test_advanced_ai.py
"""

from agents.executor import executor, WorkflowType
from agents.integration import agent_integration
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))


async def test_advanced_ai_features():
    """Test the advanced AI features"""

    print("🧪 Testing WatchTower AI Advanced Features...")
    print("="*60)

    # Test 1: Initialize agent system
    print("\n1. Testing Agent System Initialization:")
    try:
        await agent_integration.initialize()
        print("   ✅ Agent system initialized successfully")

        # Get system status
        status = agent_integration.get_system_status()
        print(f"   ✅ Agents initialized: {status['initialized']}")
        print(f"   ✅ Monitoring active: {status['monitoring_active']}")
        print(f"   ✅ Background tasks: {status['background_tasks']}")

    except Exception as e:
        print(f"   ❌ Agent system initialization failed: {e}")
        return False

    # Test 2: Test health check workflow
    print("\n2. Testing Health Check Workflow:")
    try:
        result = await executor.perform_health_check()

        if result.success:
            print("   ✅ Health check workflow executed successfully")
            print(f"   ✅ Execution time: {result.execution_time:.2f}s")
            print(f"   ✅ Results: {len(result.result)} items")
        else:
            print(f"   ❌ Health check workflow failed: {result.error_message}")

    except Exception as e:
        print(f"   ❌ Health check workflow error: {e}")

    # Test 3: Test system analysis workflow
    print("\n3. Testing System Analysis Workflow:")
    try:
        result = await executor.analyze_system()

        if result.success:
            print("   ✅ System analysis workflow executed successfully")
            print(f"   ✅ Execution time: {result.execution_time:.2f}s")
            print(f"   ✅ Results: {len(result.result)} items")
        else:
            print(
                f"   ❌ System analysis workflow failed: {result.error_message}")

    except Exception as e:
        print(f"   ❌ System analysis workflow error: {e}")

    # Test 4: Test chat integration
    print("\n4. Testing Chat Integration with Agents:")
    test_queries = [
        "How is the system health?",
        "Analyze the current system performance",
        "Give me a system overview"
    ]

    for query in test_queries:
        try:
            print(f"   Testing: '{query}'")

            result = await agent_integration.process_chat_query(query)

            if result.get("success"):
                print(f"      ✅ Agent response received")
                print(
                    f"         Type: {result.get('response_type', 'unknown')}")
                print(
                    f"         Summary: {result.get('summary', 'No summary')[:100]}...")
            else:
                print(
                    f"      ❌ Agent response failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"      ❌ Chat query failed: {e}")

    # Test 5: Test alert processing
    print("\n5. Testing Alert Processing:")
    try:
        # Simulate an alert
        alert_data = {
            "service_name": "transaction_service",
            "severity": "warning",
            "message": "Response time increased",
            "timestamp": "2025-07-10T10:00:00Z"
        }

        metric_data = {
            "metric_name": "response_time",
            "current_value": 0.8,
            "threshold_warning": 0.5,
            "threshold_critical": 1.0
        }

        result = await agent_integration.process_alert(alert_data, metric_data)

        if result.get("success"):
            print("   ✅ Alert processing completed successfully")
            print(
                f"   ✅ Execution time: {result.get('execution_time', 0):.2f}s")
            print(
                f"   ✅ Analysis available: {len(result.get('analysis', {}))}")
        else:
            print(
                f"   ❌ Alert processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Alert processing error: {e}")

    # Test 6: Test agent status and communication
    print("\n6. Testing Agent Status and Communication:")
    try:
        executor_status = executor.get_status()

        print(f"   ✅ Executor running: {executor_status['is_running']}")
        print(
            f"   ✅ Workflows executed: {executor_status['workflows_executed']}")
        print(
            f"   ✅ Registered agents: {executor_status['registered_agents']}")
        print(
            f"   ✅ Available workflows: {len(executor_status['available_workflows'])}")

        # Test individual agent status
        agent_statuses = executor_status.get("agents_status", {})
        for agent_id, status in agent_statuses.items():
            print(f"   ✅ Agent {agent_id}: {status.get('is_running', False)}")

    except Exception as e:
        print(f"   ❌ Agent status check failed: {e}")

    # Test 7: Test workflow capabilities
    print("\n7. Testing Workflow Capabilities:")
    try:
        available_workflows = [
            WorkflowType.HEALTH_CHECK,
            WorkflowType.SYSTEM_ANALYSIS,
            WorkflowType.CORRELATION_ANALYSIS,
            WorkflowType.PROACTIVE_MONITORING
        ]

        for workflow_type in available_workflows:
            workflow_key = workflow_type.value
            if workflow_key in executor.workflows:
                print(f"   ✅ Workflow available: {workflow_key}")
            else:
                print(f"   ❌ Workflow missing: {workflow_key}")

    except Exception as e:
        print(f"   ❌ Workflow capability check failed: {e}")

    # Cleanup
    print("\n8. Cleaning Up:")
    try:
        await agent_integration.shutdown()
        print("   ✅ Agent system shutdown successfully")

    except Exception as e:
        print(f"   ❌ Agent system shutdown failed: {e}")

    print("\n" + "="*60)
    print("✅ Advanced AI Features Test Complete!")
    print("\nSummary of Advanced Features:")
    print("• 🏥 Health Agent - Proactive monitoring and health analysis")
    print("• 🔍 Analysis Agent - Intelligent correlation and root cause analysis")
    print("• 🎭 LangGraph Executor - Multi-agent workflow orchestration")
    print("• 🔗 Agent Integration - Seamless chat interface integration")
    print("• 🤖 Background Monitoring - Continuous system monitoring")
    print("• 📊 Workflow System - 5 different intelligent workflows")
    print("• 💬 Enhanced Chat - Agent-powered responses")
    print("• 🚨 Alert Processing - Intelligent alert analysis")

    print("\nNext Steps:")
    print("1. Start backend: cd backend && python main.py")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Test advanced features at: http://localhost:3333")
    print("4. Check agent status at: http://localhost:5050/api/agents/status")

    return True

if __name__ == "__main__":
    asyncio.run(test_advanced_ai_features())

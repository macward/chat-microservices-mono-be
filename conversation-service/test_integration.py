#!/usr/bin/env python3
"""
Integration test script for Phase 4: External Services Integration

This script tests the integration with Auth Service and Characters Service
to validate that the Conversation Service can properly authenticate users
and validate character existence.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Test configuration
CONVERSATION_SERVICE_URL = "http://localhost:8003"
AUTH_SERVICE_URL = "http://localhost:8001"
CHARACTERS_SERVICE_URL = "http://localhost:8002"

# Test data
TEST_CHARACTER_ID = "507f1f77bcf86cd799439011"
TEST_USER_ID = "507f1f77bcf86cd799439012"
SAMPLE_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


async def test_service_health(client: httpx.AsyncClient, service_name: str, url: str) -> bool:
    """Test if a service is running and healthy."""
    try:
        response = await client.get(f"{url}/health", timeout=5.0)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} health check failed with status {response.status_code}")
            return False
    except httpx.ConnectError:
        print(f"❌ {service_name} is not running or unreachable at {url}")
        return False
    except Exception as e:
        print(f"❌ {service_name} health check error: {e}")
        return False


async def test_auth_service_integration(client: httpx.AsyncClient) -> bool:
    """Test Auth Service integration."""
    print("\n🔐 Testing Auth Service Integration...")
    
    # Test 1: Valid token validation
    try:
        headers = {"Authorization": f"Bearer {SAMPLE_JWT_TOKEN}"}
        response = await client.get(f"{AUTH_SERVICE_URL}/api/v1/auth/validate", headers=headers)
        
        if response.status_code == 200:
            print("✅ Auth service token validation endpoint is working")
            return True
        elif response.status_code == 401:
            print("✅ Auth service correctly rejects invalid token")
            return True
        else:
            print(f"❌ Unexpected auth service response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auth service integration test failed: {e}")
        return False


async def test_characters_service_integration(client: httpx.AsyncClient) -> bool:
    """Test Characters Service integration."""
    print("\n👥 Testing Characters Service Integration...")
    
    try:
        response = await client.get(f"{CHARACTERS_SERVICE_URL}/api/v1/characters/{TEST_CHARACTER_ID}")
        
        if response.status_code in [200, 404]:
            print("✅ Characters service character validation endpoint is working")
            return True
        else:
            print(f"❌ Unexpected characters service response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Characters service integration test failed: {e}")
        return False


async def test_conversation_service_without_auth(client: httpx.AsyncClient) -> bool:
    """Test that conversation service requires authentication."""
    print("\n🚫 Testing Authentication Requirements...")
    
    try:
        # Test creating conversation without auth
        conversation_data = {
            "character_id": TEST_CHARACTER_ID,
            "title": "Test Conversation"
        }
        
        response = await client.post(
            f"{CONVERSATION_SERVICE_URL}/v1/conversations/",
            json=conversation_data
        )
        
        if response.status_code == 401:
            print("✅ Conversation service correctly requires authentication")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication requirement test failed: {e}")
        return False


async def test_conversation_service_with_mock_auth(client: httpx.AsyncClient) -> bool:
    """Test conversation service with mock authentication."""
    print("\n🔗 Testing Conversation Service with Mock Auth...")
    
    try:
        # This will fail because we don't have real auth services running
        # but we can test that the service attempts to validate
        conversation_data = {
            "character_id": TEST_CHARACTER_ID,
            "title": "Test Conversation"
        }
        
        headers = {"Authorization": f"Bearer {SAMPLE_JWT_TOKEN}"}
        response = await client.post(
            f"{CONVERSATION_SERVICE_URL}/v1/conversations/",
            json=conversation_data,
            headers=headers
        )
        
        # We expect this to fail due to auth service being unavailable
        if response.status_code == 503:
            print("✅ Conversation service correctly tries to validate with auth service")
            return True
        elif response.status_code == 401:
            print("✅ Conversation service correctly rejects invalid token")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Conversation service test failed: {e}")
        return False


async def test_circuit_breaker_behavior(client: httpx.AsyncClient) -> bool:
    """Test circuit breaker behavior with multiple failed requests."""
    print("\n⚡ Testing Circuit Breaker Behavior...")
    
    try:
        headers = {"Authorization": f"Bearer {SAMPLE_JWT_TOKEN}"}
        conversation_data = {
            "character_id": TEST_CHARACTER_ID,
            "title": "Circuit Breaker Test"
        }
        
        # Make multiple requests to trigger circuit breaker
        responses = []
        for i in range(3):
            response = await client.post(
                f"{CONVERSATION_SERVICE_URL}/v1/conversations/",
                json=conversation_data,
                headers=headers,
                timeout=10.0
            )
            responses.append(response.status_code)
            print(f"Request {i+1}: Status {response.status_code}")
        
        # All should fail due to unavailable external services
        if all(status in [503, 401] for status in responses):
            print("✅ Circuit breaker is handling external service failures")
            return True
        else:
            print(f"❌ Unexpected status codes: {responses}")
            return False
            
    except Exception as e:
        print(f"❌ Circuit breaker test failed: {e}")
        return False


async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Phase 4 Integration Tests")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        tests = [
            ("Conversation Service Health", test_service_health(client, "Conversation Service", CONVERSATION_SERVICE_URL)),
            ("Auth Service Health", test_service_health(client, "Auth Service", AUTH_SERVICE_URL)),
            ("Characters Service Health", test_service_health(client, "Characters Service", CHARACTERS_SERVICE_URL)),
            ("Auth Service Integration", test_auth_service_integration(client)),
            ("Characters Service Integration", test_characters_service_integration(client)),
            ("Authentication Requirements", test_conversation_service_without_auth(client)),
            ("Mock Authentication Test", test_conversation_service_with_mock_auth(client)),
            ("Circuit Breaker Behavior", test_circuit_breaker_behavior(client)),
        ]
        
        results = []
        for test_name, test_coro in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed - check failing tests")
    else:
        print("🚨 Many tests failed - review implementation")
    
    print("\n💡 Expected Results:")
    print("- Conversation Service should be healthy")
    print("- Auth/Characters services may be down (expected)")
    print("- Authentication should be required")
    print("- Circuit breaker should handle failures gracefully")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
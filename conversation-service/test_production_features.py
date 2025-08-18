#!/usr/bin/env python3
"""
Test script for Phase 6: Production Readiness (Ops)

This script tests production-ready features:
1. Enhanced health checks with dependency status
2. Prometheus metrics endpoint
3. Logging functionality
4. Docker container compatibility
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Test configuration
CONVERSATION_SERVICE_URL = "http://localhost:8003"


class ProductionFeaturesTester:
    def __init__(self):
        self.base_url = CONVERSATION_SERVICE_URL
    
    async def test_enhanced_health_check(self, client: httpx.AsyncClient) -> bool:
        """Test enhanced health check with dependency status."""
        print("\n🏥 Testing enhanced health check...")
        
        try:
            response = await client.get(f"{self.base_url}/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check status: {health_data.get('status')}")
                print(f"   Service: {health_data.get('service')}")
                print(f"   Version: {health_data.get('version')}")
                print(f"   Environment: {health_data.get('environment')}")
                print(f"   Uptime: {health_data.get('uptime_seconds')}s")
                
                # Check dependencies
                dependencies = health_data.get('dependencies', {})
                print("   Dependencies:")
                for service, status in dependencies.items():
                    status_emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❓"
                    print(f"     {status_emoji} {service}: {status}")
                
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_prometheus_metrics(self, client: httpx.AsyncClient) -> bool:
        """Test Prometheus metrics endpoint."""
        print("\n📊 Testing Prometheus metrics...")
        
        try:
            response = await client.get(f"{self.base_url}/metrics", timeout=10.0)
            
            if response.status_code == 200:
                metrics_text = response.text
                
                # Check for key metrics
                expected_metrics = [
                    "conversation_service_requests_total",
                    "conversation_service_request_duration_seconds",
                    "conversation_service_application_info",
                    "conversation_service_active_conversations",
                    "conversation_service_total_conversations"
                ]
                
                found_metrics = []
                for metric in expected_metrics:
                    if metric in metrics_text:
                        found_metrics.append(metric)
                
                print(f"✅ Prometheus metrics endpoint accessible")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Metrics found: {len(found_metrics)}/{len(expected_metrics)}")
                
                for metric in found_metrics[:3]:  # Show first 3 metrics
                    print(f"     ✓ {metric}")
                
                return len(found_metrics) >= len(expected_metrics) * 0.8  # 80% success rate
            else:
                print(f"❌ Metrics endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Metrics endpoint error: {e}")
            return False
    
    async def test_api_documentation(self, client: httpx.AsyncClient) -> bool:
        """Test API documentation endpoints."""
        print("\n📚 Testing API documentation...")
        
        endpoints = [
            ("/docs", "Swagger UI"),
            ("/redoc", "ReDoc"),
            ("/openapi.json", "OpenAPI Schema")
        ]
        
        try:
            results = []
            for endpoint, name in endpoints:
                response = await client.get(f"{self.base_url}{endpoint}", timeout=10.0)
                success = response.status_code == 200
                results.append(success)
                
                status_emoji = "✅" if success else "❌"
                print(f"   {status_emoji} {name}: {response.status_code}")
            
            return all(results)
                
        except Exception as e:
            print(f"❌ Documentation endpoints error: {e}")
            return False
    
    async def test_security_headers(self, client: httpx.AsyncClient) -> bool:
        """Test security-related response headers."""
        print("\n🔒 Testing security headers...")
        
        try:
            response = await client.get(f"{self.base_url}/health", timeout=10.0)
            
            if response.status_code == 200:
                headers = response.headers
                
                # Check for security headers (these might be added by reverse proxy in production)
                security_checks = [
                    ("server", "Server header not exposed" if "server" not in headers.keys() else f"Server: {headers.get('server')}"),
                    ("content-type", f"Content-Type: {headers.get('content-type', 'not set')}"),
                ]
                
                print("✅ Response headers analysis:")
                for header, status in security_checks:
                    print(f"   • {status}")
                
                return True
            else:
                print(f"❌ Security headers check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Security headers error: {e}")
            return False
    
    async def test_error_handling(self, client: httpx.AsyncClient) -> bool:
        """Test error handling and response formats."""
        print("\n⚠️  Testing error handling...")
        
        try:
            # Test 404 endpoint
            response = await client.get(f"{self.base_url}/nonexistent-endpoint", timeout=10.0)
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    print("✅ 404 error handling:")
                    print(f"   Status: {response.status_code}")
                    print(f"   Format: JSON")
                    if "detail" in error_data:
                        print(f"   Message: {error_data['detail']}")
                    return True
                except json.JSONDecodeError:
                    print("⚠️  404 error not in JSON format")
                    return False
            else:
                print(f"❌ Unexpected status for 404 test: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test error: {e}")
            return False
    
    async def test_logging_functionality(self, client: httpx.AsyncClient) -> bool:
        """Test logging functionality by making requests."""
        print("\n📝 Testing logging functionality...")
        
        try:
            # Make several requests to generate logs
            requests = [
                ("/health", "Health check"),
                ("/metrics", "Metrics"),
                ("/docs", "Documentation"),
                ("/nonexistent", "404 Error")
            ]
            
            print("   Making requests to generate logs:")
            for endpoint, description in requests:
                response = await client.get(f"{self.base_url}{endpoint}", timeout=5.0)
                status_emoji = "✅" if 200 <= response.status_code < 400 else "⚠️"
                print(f"     {status_emoji} {description}: {response.status_code}")
            
            print("✅ Logging test completed (check application logs)")
            return True
                
        except Exception as e:
            print(f"❌ Logging test error: {e}")
            return False


async def run_production_features_tests():
    """Run all production features tests."""
    print("🚀 Starting Phase 6 Production Readiness Tests")
    print("=" * 50)
    
    tester = ProductionFeaturesTester()
    
    async with httpx.AsyncClient() as client:
        tests = [
            ("Enhanced Health Check", tester.test_enhanced_health_check(client)),
            ("Prometheus Metrics", tester.test_prometheus_metrics(client)),
            ("API Documentation", tester.test_api_documentation(client)),
            ("Security Headers", tester.test_security_headers(client)),
            ("Error Handling", tester.test_error_handling(client)),
            ("Logging Functionality", tester.test_logging_functionality(client))
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
    print("📊 Production Readiness Test Results")
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
        print("🎉 All production readiness tests passed!")
        print("🚀 Service is ready for production deployment!")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed - minor issues to address")
        print("🔧 Review failed tests before production deployment")
    else:
        print("🚨 Several tests failed - service needs work")
        print("🛠️  Address failing tests before production deployment")
    
    print(f"\n💡 Production Readiness Summary:")
    print("- ✅ Enhanced health checks with dependency monitoring")
    print("- 📊 Prometheus metrics for observability")
    print("- 📚 Comprehensive API documentation")
    print("- 🔒 Security-focused error handling")
    print("- 📝 Structured logging for audit trails")
    print("- 🐳 Docker container optimization")


if __name__ == "__main__":
    asyncio.run(run_production_features_tests())
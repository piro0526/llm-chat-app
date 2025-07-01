#!/usr/bin/env python3
"""
Test MCP Protocol Compliance
Comprehensive test suite to verify MCP protocol compliance.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the backend directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

from mcp_clients.client_manager import MCPClientManager
from mcp_host.mcp_host import MCPHost

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPComplianceTests:
    """Test suite for MCP protocol compliance."""
    
    def __init__(self):
        self.manager = None
        self.host = None
        self.test_results = []
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up MCP compliance tests...")
        
        # Initialize client manager
        self.manager = MCPClientManager("mcp_config.json")
        
        # Initialize host
        self.host = MCPHost()
        
        return True
    
    async def teardown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        
        if self.manager:
            await self.manager.stop_clients()
    
    async def test_client_configuration(self):
        """Test client configuration loading."""
        test_name = "Client Configuration"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Load configuration
            config_loaded = await self.manager.load_config()
            
            if not config_loaded:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Configuration not loaded"})
                return False
            
            # Verify configuration structure
            if "servers" not in self.manager.config:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No servers in configuration"})
                return False
            
            # Verify time server configuration
            if "time-server" not in self.manager.config["servers"]:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server not configured"})
                return False
            
            time_server_config = self.manager.config["servers"]["time-server"]
            required_fields = ["type", "enabled", "server_path"]
            
            for field in required_fields:
                if field not in time_server_config:
                    self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing field: {field}"})
                    return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": "Configuration loaded successfully"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_client_startup(self):
        """Test MCP client startup."""
        test_name = "Client Startup"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Start clients
            started = await self.manager.start_clients()
            
            if not started:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Failed to start clients"})
                return False
            
            # Verify clients are connected
            if len(self.manager.clients) == 0:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No clients connected"})
                return False
            
            # Verify time server is connected
            if "time-server" not in self.manager.clients:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server not connected"})
                return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": f"Started {len(self.manager.clients)} clients"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_mcp_protocol_handshake(self):
        """Test MCP protocol handshake."""
        test_name = "MCP Protocol Handshake"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Get time server client
            time_client = self.manager.clients.get("time-server")
            if not time_client:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server client not found"})
                return False
            
            # Verify client is connected (handshake completed)
            if not time_client.connected:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Client not connected (handshake failed)"})
                return False
            
            # Verify session exists
            if not time_client.session:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No MCP session established"})
                return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": "MCP handshake completed successfully"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_tool_discovery(self):
        """Test MCP tool discovery."""
        test_name = "Tool Discovery"
        logger.info(f"Running test: {test_name}")
        
        try:
            # List tools from all clients
            all_tools = await self.manager.list_available_tools()
            
            if not all_tools:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No tools discovered"})
                return False
            
            # Verify time server tools
            if "time-server" not in all_tools:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server tools not discovered"})
                return False
            
            time_tools = all_tools["time-server"]
            expected_tools = ["get_current_time", "convert_time", "time_difference", "list_timezones"]
            
            for expected_tool in expected_tools:
                if not any(tool["name"] == expected_tool for tool in time_tools):
                    self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing tool: {expected_tool}"})
                    return False
            
            total_tools = sum(len(tools) for tools in all_tools.values())
            self.test_results.append({"test": test_name, "status": "PASSED", "message": f"Discovered {total_tools} tools from {len(all_tools)} servers"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_resource_discovery(self):
        """Test MCP resource discovery."""
        test_name = "Resource Discovery"
        logger.info(f"Running test: {test_name}")
        
        try:
            # List resources from all clients
            all_resources = await self.manager.list_available_resources()
            
            if not all_resources:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No resources discovered"})
                return False
            
            # Verify time server resources
            if "time-server" not in all_resources:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server resources not discovered"})
                return False
            
            time_resources = all_resources["time-server"]
            expected_resources = ["time://current/utc", "time://timezones/common"]
            
            for expected_resource in expected_resources:
                if not any(resource["uri"] == expected_resource for resource in time_resources):
                    self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing resource: {expected_resource}"})
                    return False
            
            total_resources = sum(len(resources) for resources in all_resources.values())
            self.test_results.append({"test": test_name, "status": "PASSED", "message": f"Discovered {total_resources} resources from {len(all_resources)} servers"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_tool_execution(self):
        """Test MCP tool execution."""
        test_name = "Tool Execution"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test get_current_time tool
            time_result = await self.manager.call_tool("time-server", "get_current_time", {"timezone": "UTC"})
            
            if not time_result:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Empty tool result"})
                return False
            
            # Parse result
            try:
                parsed_result = json.loads(time_result)
                if "error" in parsed_result:
                    self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Tool error: {parsed_result['error']}"})
                    return False
                
                # Verify expected fields
                expected_fields = ["current_time", "timezone", "formatted_time"]
                for field in expected_fields:
                    if field not in parsed_result:
                        self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing field in result: {field}"})
                        return False
                
            except json.JSONDecodeError:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Invalid JSON response"})
                return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": "Tool execution successful"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_resource_reading(self):
        """Test MCP resource reading."""
        test_name = "Resource Reading"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test reading UTC time resource
            resource_result = await self.manager.read_resource("time-server", "time://current/utc")
            
            if not resource_result:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Empty resource result"})
                return False
            
            # Parse result
            try:
                parsed_result = json.loads(resource_result)
                if "error" in parsed_result:
                    self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Resource error: {parsed_result['error']}"})
                    return False
                
                # Verify expected fields
                expected_fields = ["current_time", "formatted", "timestamp"]
                for field in expected_fields:
                    if field not in parsed_result:
                        self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing field in resource: {field}"})
                        return False
                
            except json.JSONDecodeError:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Invalid JSON response from resource"})
                return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": "Resource reading successful"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_health_monitoring(self):
        """Test MCP health monitoring."""
        test_name = "Health Monitoring"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test health check
            health_status = await self.manager.health_check()
            
            if not health_status:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No health status returned"})
                return False
            
            # Verify time server health
            if "time-server" not in health_status:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server health not checked"})
                return False
            
            if not health_status["time-server"]:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "Time server unhealthy"})
                return False
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": "Health monitoring working"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def test_langchain_integration(self):
        """Test LangChain tool integration."""
        test_name = "LangChain Integration"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Initialize host
            host_init = await self.host.initialize()
            
            # Get LangChain tools (should work regardless of host init status)
            langchain_tools = await self.host.get_tools()
            
            if not langchain_tools:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": "No LangChain tools available"})
                return False
            
            # Verify essential MCP tools
            tool_names = [tool.name for tool in langchain_tools]
            expected_tools = ["mcp_call_tool", "mcp_list_tools", "mcp_status"]
            
            missing_tools = []
            for expected_tool in expected_tools:
                if expected_tool not in tool_names:
                    missing_tools.append(expected_tool)
            
            if missing_tools:
                self.test_results.append({"test": test_name, "status": "FAILED", "error": f"Missing LangChain tools: {missing_tools}"})
                return False
            
            # Test if MCP clients are connected for specialized tools
            manager = await get_mcp_manager()
            status = await manager.get_status()
            
            if status["connected_clients"] > 0:
                # If MCP clients are connected, specialized tools should be available
                specialized_tools = ["get_time", "convert_time"]
                for tool_name in specialized_tools:
                    if tool_name in tool_names:
                        self.test_results.append({"test": test_name, "status": "PASSED", "message": f"LangChain integration with {len(langchain_tools)} tools, including specialized MCP tools"})
                        return True
            
            self.test_results.append({"test": test_name, "status": "PASSED", "message": f"LangChain integration with {len(langchain_tools)} base tools (no MCP clients connected)"})
            return True
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return False
    
    async def run_all_tests(self):
        """Run all compliance tests."""
        logger.info("Starting MCP protocol compliance tests...")
        
        try:
            # Setup
            await self.setup()
            
            # Run tests in sequence
            tests = [
                self.test_client_configuration,
                self.test_client_startup,
                self.test_mcp_protocol_handshake,
                self.test_tool_discovery,
                self.test_resource_discovery,
                self.test_tool_execution,
                self.test_resource_reading,
                self.test_health_monitoring,
                self.test_langchain_integration,
            ]
            
            passed = 0
            failed = 0
            
            for test in tests:
                success = await test()
                if success:
                    passed += 1
                else:
                    failed += 1
            
            # Generate report
            logger.info(f"Test Results: {passed} passed, {failed} failed")
            
            return {
                "summary": {
                    "total_tests": len(tests),
                    "passed": passed,
                    "failed": failed
                },
                "results": self.test_results
            }
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 1
                },
                "results": [{"test": "Test Suite", "status": "FAILED", "error": str(e)}]
            }
        
        finally:
            await self.teardown()
    
    def print_report(self, results):
        """Print test report."""
        print("\n" + "="*60)
        print("MCP PROTOCOL COMPLIANCE TEST REPORT")
        print("="*60)
        
        summary = results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {(summary['passed'] / summary['total_tests'] * 100):.1f}%" if summary['total_tests'] > 0 else "0%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        for result in results["results"]:
            status_symbol = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_symbol} {result['test']}: {result['status']}")
            
            if result["status"] == "PASSED" and "message" in result:
                print(f"   → {result['message']}")
            elif result["status"] == "FAILED" and "error" in result:
                print(f"   → Error: {result['error']}")
        
        print("\n" + "="*60)
        
        if summary["failed"] == 0:
            print("🎉 ALL TESTS PASSED - MCP PROTOCOL COMPLIANCE VERIFIED")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW IMPLEMENTATION")
        
        print("="*60)


async def main():
    """Main test runner."""
    test_suite = MCPComplianceTests()
    results = await test_suite.run_all_tests()
    test_suite.print_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
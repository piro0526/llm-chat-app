"""
MCP Host for LangGraph Integration
Provides MCP tool integration for LLM communication through LangGraph workflows.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from pydantic.v1 import BaseModel as BaseModelV1

from mcp_clients.client_manager import get_mcp_manager

logger = logging.getLogger(__name__)


class MCPToolInput(BaseModel):
    """Input schema for MCP tools."""
    server_name: str = Field(description="Name of the MCP server to use")
    tool_name: str = Field(description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(description="Arguments for the tool call")


class MCPResourceInput(BaseModel):
    """Input schema for MCP resources."""
    server_name: str = Field(description="Name of the MCP server to use")
    resource_uri: str = Field(description="URI of the resource to read")


class MCPToolCallTool(BaseTool):
    """LangChain tool for calling MCP tools."""
    
    name: str = "mcp_call_tool"
    description: str = (
        "Call a tool on an MCP server. This allows access to various external tools "
        "like time operations, file systems, web APIs, and more through the Model Context Protocol."
    )
    args_schema: Type[BaseModel] = MCPToolInput
    
    async def _arun(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute the MCP tool call asynchronously."""
        try:
            manager = await get_mcp_manager()
            result = await manager.call_tool(server_name, tool_name, arguments)
            return result
        except Exception as e:
            error_result = {
                "error": f"MCP tool call failed: {str(e)}",
                "server_name": server_name,
                "tool_name": tool_name
            }
            return json.dumps(error_result)
    
    def _run(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Synchronous version - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(server_name, tool_name, arguments))
        except Exception as e:
            error_result = {
                "error": f"MCP tool call failed: {str(e)}",
                "server_name": server_name,
                "tool_name": tool_name
            }
            return json.dumps(error_result)


class MCPResourceReadTool(BaseTool):
    """LangChain tool for reading MCP resources."""
    
    name: str = "mcp_read_resource"
    description: str = (
        "Read a resource from an MCP server. Resources can be files, configurations, "
        "data feeds, or any structured information provided by MCP servers."
    )
    args_schema: Type[BaseModel] = MCPResourceInput
    
    async def _arun(self, server_name: str, resource_uri: str) -> str:
        """Execute the MCP resource read asynchronously."""
        try:
            manager = await get_mcp_manager()
            result = await manager.read_resource(server_name, resource_uri)
            return result
        except Exception as e:
            error_result = {
                "error": f"MCP resource read failed: {str(e)}",
                "server_name": server_name,
                "resource_uri": resource_uri
            }
            return json.dumps(error_result)
    
    def _run(self, server_name: str, resource_uri: str) -> str:
        """Synchronous version - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(server_name, resource_uri))
        except Exception as e:
            error_result = {
                "error": f"MCP resource read failed: {str(e)}",
                "server_name": server_name,
                "resource_uri": resource_uri
            }
            return json.dumps(error_result)


class MCPListToolsTool(BaseTool):
    """LangChain tool for listing available MCP tools."""
    
    name: str = "mcp_list_tools"
    description: str = (
        "List all available tools from all connected MCP servers. "
        "Use this to discover what tools are available before calling them."
    )
    
    async def _arun(self) -> str:
        """List all available MCP tools asynchronously."""
        try:
            manager = await get_mcp_manager()
            tools = await manager.list_available_tools()
            
            # Format the response for better readability
            formatted_tools = {}
            for server_name, server_tools in tools.items():
                formatted_tools[server_name] = [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("inputSchema", {})
                    }
                    for tool in server_tools
                ]
            
            return json.dumps(formatted_tools, indent=2)
        except Exception as e:
            error_result = {"error": f"Failed to list MCP tools: {str(e)}"}
            return json.dumps(error_result)
    
    def _run(self) -> str:
        """Synchronous version - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun())
        except Exception as e:
            error_result = {"error": f"Failed to list MCP tools: {str(e)}"}
            return json.dumps(error_result)


class MCPListResourcesTool(BaseTool):
    """LangChain tool for listing available MCP resources."""
    
    name: str = "mcp_list_resources"
    description: str = (
        "List all available resources from all connected MCP servers. "
        "Resources are data sources that can be read using the mcp_read_resource tool."
    )
    
    async def _arun(self) -> str:
        """List all available MCP resources asynchronously."""
        try:
            manager = await get_mcp_manager()
            resources = await manager.list_available_resources()
            
            # Format the response for better readability
            formatted_resources = {}
            for server_name, server_resources in resources.items():
                formatted_resources[server_name] = [
                    {
                        "uri": resource["uri"],
                        "name": resource["name"],
                        "description": resource["description"],
                        "mime_type": resource.get("mimeType", "")
                    }
                    for resource in server_resources
                ]
            
            return json.dumps(formatted_resources, indent=2)
        except Exception as e:
            error_result = {"error": f"Failed to list MCP resources: {str(e)}"}
            return json.dumps(error_result)
    
    def _run(self) -> str:
        """Synchronous version - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun())
        except Exception as e:
            error_result = {"error": f"Failed to list MCP resources: {str(e)}"}
            return json.dumps(error_result)


class MCPStatusTool(BaseTool):
    """LangChain tool for checking MCP server status."""
    
    name: str = "mcp_status"
    description: str = (
        "Check the status and health of all MCP servers. "
        "Use this to verify which servers are available and working correctly."
    )
    
    async def _arun(self) -> str:
        """Get MCP status asynchronously."""
        try:
            manager = await get_mcp_manager()
            status = await manager.get_status()
            return json.dumps(status, indent=2)
        except Exception as e:
            error_result = {"error": f"Failed to get MCP status: {str(e)}"}
            return json.dumps(error_result)
    
    def _run(self) -> str:
        """Synchronous version - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun())
        except Exception as e:
            error_result = {"error": f"Failed to get MCP status: {str(e)}"}
            return json.dumps(error_result)


# Specialized tools for common MCP operations
class TimeServerTool(BaseTool):
    """Convenient tool for time server operations using MCP."""
    
    name: str = "get_time"
    description: str = (
        "Get current time in any timezone. Supports IANA timezone names like "
        "'America/New_York', 'Europe/London', 'Asia/Tokyo', etc. "
        "Requires MCP time server to be connected."
    )
    
    class InputSchema(BaseModel):
        timezone: str = Field(description="Timezone name (e.g., 'America/New_York', 'UTC')", default="UTC")
    
    args_schema: Type[BaseModel] = InputSchema
    
    async def _arun(self, timezone: str = "UTC") -> str:
        """Get current time asynchronously."""
        try:
            manager = await get_mcp_manager()
            status = await manager.get_status()
            
            if status["connected_clients"] == 0:
                raise RuntimeError("MCP time server not available")
            
            result = await manager.call_tool("time-server", "get_current_time", {"timezone": timezone})
            return result
        except Exception as e:
            error_result = {
                "error": f"Time query failed: {str(e)}",
                "timezone": timezone,
                "message": "MCP time server required for timezone operations"
            }
            return json.dumps(error_result)
    
    def _run(self, timezone: str = "UTC") -> str:
        """Synchronous version."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(timezone))
        except Exception as e:
            error_result = {
                "error": f"Time query failed: {str(e)}",
                "timezone": timezone,
                "message": "MCP time server required for timezone operations"
            }
            return json.dumps(error_result)


class ConvertTimeTool(BaseTool):
    """Convenient tool for time conversion using MCP."""
    
    name: str = "convert_time"
    description: str = (
        "Convert time from one timezone to another. Handles daylight saving time automatically. "
        "Requires MCP time server to be connected."
    )
    
    class InputSchema(BaseModel):
        time_str: str = Field(description="Time string in ISO format (e.g., '2024-01-15 14:30:00')")
        source_timezone: str = Field(description="Source timezone name")
        target_timezone: str = Field(description="Target timezone name")
    
    args_schema: Type[BaseModel] = InputSchema
    
    async def _arun(self, time_str: str, source_timezone: str, target_timezone: str) -> str:
        """Convert time asynchronously."""
        try:
            manager = await get_mcp_manager()
            status = await manager.get_status()
            
            if status["connected_clients"] == 0:
                raise RuntimeError("MCP time server not available")
            
            result = await manager.call_tool("time-server", "convert_time", {
                "time_str": time_str,
                "source_timezone": source_timezone,
                "target_timezone": target_timezone
            })
            return result
        except Exception as e:
            error_result = {
                "error": f"Time conversion failed: {str(e)}",
                "time_str": time_str,
                "source_timezone": source_timezone,
                "target_timezone": target_timezone,
                "message": "MCP time server required for timezone operations"
            }
            return json.dumps(error_result)
    
    def _run(self, time_str: str, source_timezone: str, target_timezone: str) -> str:
        """Synchronous version."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(time_str, source_timezone, target_timezone))
        except Exception as e:
            error_result = {
                "error": f"Time conversion failed: {str(e)}",
                "time_str": time_str,
                "source_timezone": source_timezone,
                "target_timezone": target_timezone,
                "message": "MCP time server required for timezone operations"
            }
            return json.dumps(error_result)


class MCPHost:
    """MCP Host for LangGraph integration."""
    
    def __init__(self):
        self.tools_cache = None
        self.last_cache_update = None
    
    async def get_tools(self, include_specialized: bool = True) -> List[BaseTool]:
        """Get all available MCP tools for LangGraph integration."""
        tools = [
            MCPToolCallTool(),
            MCPResourceReadTool(),
            MCPListToolsTool(),
            MCPListResourcesTool(),
            MCPStatusTool(),
        ]
        
        if include_specialized:
            # Add specialized tools for better UX
            tools.extend([
                TimeServerTool(),
                ConvertTimeTool(),
            ])
        
        return tools
    
    async def get_tools_with_discovery(self) -> List[BaseTool]:
        """Get tools with automatic discovery of available MCP capabilities."""
        base_tools = await self.get_tools()
        
        try:
            # Get available tools from all servers
            manager = await get_mcp_manager()
            status = await manager.get_status()
            
            # Only provide tools if MCP clients are connected
            if status["connected_clients"] == 0:
                logger.warning("No MCP clients connected, limited functionality available")
                return base_tools
            
            available_tools = await manager.list_available_tools()
            
            # Create dynamic tools based on discovered capabilities
            dynamic_tools = []
            for server_name, server_tools in available_tools.items():
                for tool_info in server_tools:
                    tool_name = tool_info["name"]
                    # Create specialized tools for discovered capabilities
                    if server_name == "time-server" and tool_name in ["get_current_time", "convert_time"]:
                        continue  # Already have specialized tools
                    
                    # Could create more dynamic specialized tools here
            
            return base_tools + dynamic_tools
            
        except Exception as e:
            logger.error(f"Error discovering MCP tools: {e}")
            return base_tools
    
    async def initialize(self) -> bool:
        """Initialize the MCP host."""
        try:
            manager = await get_mcp_manager()
            status = await manager.get_status()
            
            if status["connected_clients"] > 0:
                logger.info(f"MCP Host initialized with {status['connected_clients']} connected clients")
                return True
            else:
                logger.warning("MCP Host initialized but no clients connected")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing MCP Host: {e}")
            return False


# Global MCP host instance
mcp_host = MCPHost()


async def get_mcp_host() -> MCPHost:
    """Get the global MCP host instance."""
    return mcp_host


async def get_mcp_tools_for_llm() -> List[BaseTool]:
    """Get MCP tools formatted for LLM integration."""
    host = await get_mcp_host()
    return await host.get_tools_with_discovery()


# Test function
async def test_mcp_host():
    """Test the MCP host implementation."""
    print("=== Testing MCP Host ===")
    
    # Initialize MCP clients first
    from mcp_clients.client_manager import initialize_mcp_clients
    await initialize_mcp_clients()
    
    host = MCPHost()
    
    try:
        # Initialize host
        initialized = await host.initialize()
        print(f"Host initialized: {'✅ SUCCESS' if initialized else '❌ FAILED'}")
        
        # Get tools
        tools = await host.get_tools()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
        
        # Test tool execution
        time_tool = next((t for t in tools if t.name == "get_time"), None)
        if time_tool:
            result = await time_tool._arun("UTC")
            print(f"Time tool result: {result[:100]}...")
        
        # Test MCP status
        status_tool = next((t for t in tools if t.name == "mcp_status"), None)
        if status_tool:
            status = await status_tool._arun()
            print(f"MCP status: {status[:200]}...")
        
    except Exception as e:
        print(f"Test error: {e}")
    
    finally:
        # Cleanup
        from mcp_clients.client_manager import cleanup_mcp_clients
        await cleanup_mcp_clients()
        print("MCP Host test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_mcp_host())
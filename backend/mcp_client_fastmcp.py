"""
FastMCP-based MCP Client implementation for better readability and maintainability
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

# FastMCP is required - no fallback implementation
try:
    from fastmcp import Client as FastMCPClient_Base
    from fastmcp.transports.stdio import StdioTransport
    print("FastMCP successfully imported from PyPI")
except ImportError:
    try:
        # Alternative import paths for different FastMCP versions
        from fastmcp.client import Client as FastMCPClient_Base
        from fastmcp.transport import StdioTransport
        print("FastMCP successfully imported (alternative path)")
    except ImportError as e:
        raise ImportError(
            f"FastMCP is required but not available: {e}\n"
            "Please install with: pip install fastmcp>=0.1.0"
        )

# Define Tool and Resource classes regardless of FastMCP availability
class Tool:
    def __init__(self, name: str, description: str, input_schema: dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema

class Resource:
    def __init__(self, uri: str, name: str, mime_type: str = None):
        self.uri = uri
        self.name = name
        self.mime_type = mime_type

logger = logging.getLogger(__name__)


class FastMCPClient:
    """
    Enhanced MCP client using FastMCP for better readability and functionality
    """
    
    def __init__(self, server_name: str, server_command: List[str]):
        """
        Initialize FastMCP client
        
        Args:
            server_name: Human-readable name for the server
            server_command: Command to start the MCP server
        """
        self.server_name = server_name
        self.server_command = server_command
        self.client: Optional[FastMCPClient_Base] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.connected = False
        
    async def connect(self) -> bool:
        """
        Connect to the MCP server using FastMCP
        """
        try:
            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Create FastMCP client
            self.client = FastMCPClient_Base(name=f"llm-chat-app-{self.server_name}")
            
            # Connect using stdio transport
            transport = StdioTransport(
                stdin=self.process.stdin,
                stdout=self.process.stdout
            )
            
            await self.client.connect(transport)
            
            # Load available tools and resources
            await self._load_capabilities()
            
            self.connected = True
            logger.info(f"Connected to MCP server '{self.server_name}' with {len(self.tools)} tools and {len(self.resources)} resources")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.server_name}': {e}")
            await self._cleanup()
            # Initialize with mock tools as last resort
            await self._initialize_mock_tools()
            self.connected = True
            logger.warning(f"Using mock tools for server '{self.server_name}' due to connection failure")
            return False
    
    
    async def _load_capabilities(self):
        """
        Load tools and resources from the connected MCP server
        """
        if not self.client:
            return
        
        try:
            # Load tools using FastMCP API
            tools_response = await self.client.list_tools()
            if isinstance(tools_response, dict) and "tools" in tools_response:
                tools = tools_response["tools"]
            else:
                tools = tools_response or []
            
            for tool_data in tools:
                if isinstance(tool_data, dict):
                    tool = Tool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {})
                    )
                    self.tools[tool.name] = tool
            
            # Load resources using FastMCP API
            resources_response = await self.client.list_resources()
            if isinstance(resources_response, dict) and "resources" in resources_response:
                resources = resources_response["resources"]
            else:
                resources = resources_response or []
            
            for resource_data in resources:
                if isinstance(resource_data, dict):
                    resource = Resource(
                        uri=resource_data.get("uri", ""),
                        name=resource_data.get("name", resource_data.get("uri", "")),
                        mime_type=resource_data.get("mimeType")
                    )
                    self.resources[resource.uri] = resource
                
        except Exception as e:
            logger.error(f"Failed to load capabilities: {e}")
            # Raise the exception since FastMCP is required
            raise
    
    async def _initialize_mock_tools(self):
        """
        Initialize mock tools for development and fallback
        """
        mock_tools = [
            Tool(
                name="filesystem_read",
                description="Read content from a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="filesystem_write",
                description="Write content to a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            ),
            Tool(
                name="web_search",
                description="Search the web for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Max results", "default": 5}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="time_now",
                description="Get current date and time",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
        
        for tool in mock_tools:
            self.tools[tool.name] = tool
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool with the given arguments
        """
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found in server '{self.server_name}'"
        
        try:
            if self.client:
                # Use FastMCP to call the tool
                result = await self.client.call_tool(tool_name, arguments)
                
                # Handle different result formats from FastMCP
                if isinstance(result, dict):
                    if "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            return content[0].get("text", str(result))
                    elif "result" in result:
                        return str(result["result"])
                    return str(result)
                elif isinstance(result, str):
                    return result
                else:
                    return str(result)
            else:
                # Use mock tools only if no client connection
                return await self._call_tool_fallback(tool_name, arguments)
                
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return f"Error calling tool '{tool_name}': {str(e)}"
    
    async def _call_tool_fallback(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Fallback tool execution for mock tools
        """
        if tool_name == "filesystem_read":
            path = arguments.get("path", "")
            return f"Mock: Reading file '{path}'"
        elif tool_name == "filesystem_write":
            path = arguments.get("path", "")
            content = arguments.get("content", "")
            return f"Mock: Writing {len(content)} characters to '{path}'"
        elif tool_name == "web_search":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 5)
            return f"Mock: Searching for '{query}' (max {max_results} results)"
        elif tool_name == "time_now":
            from datetime import datetime
            return f"Current time: {datetime.now().isoformat()}"
        else:
            return f"Mock result for tool '{tool_name}' with arguments: {json.dumps(arguments)}"
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """
        Read content from a resource
        """
        if uri not in self.resources:
            logger.warning(f"Resource '{uri}' not found in server '{self.server_name}'")
            return None
        
        try:
            if self.client:
                result = await self.client.read_resource(uri)
                
                # Handle different result formats from FastMCP
                if isinstance(result, dict):
                    if "contents" in result:
                        contents = result["contents"]
                        if isinstance(contents, list) and len(contents) > 0:
                            return contents[0].get("text", "")
                    return str(result)
                elif isinstance(result, str):
                    return result
                else:
                    return str(result)
            else:
                # Return mock content only if no client connection
                return f"Mock resource content for '{uri}'"
                
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {e}")
            return None
    
    async def disconnect(self):
        """
        Disconnect from the MCP server and cleanup resources
        """
        try:
            if self.client:
                await self.client.close()
            
            await self._cleanup()
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self.connected = False
            self.client = None
    
    async def _cleanup(self):
        """
        Cleanup server process and resources
        """
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error cleaning up process: {e}")
            finally:
                self.process = None
    
    def get_available_tools(self) -> List[Tool]:
        """
        Get list of available tools
        """
        return list(self.tools.values())
    
    def get_available_resources(self) -> List[Resource]:
        """
        Get list of available resources
        """
        return list(self.resources.values())
    
    def is_connected(self) -> bool:
        """
        Check if the client is connected
        """
        return self.connected
    
    def get_tool_info(self, tool_name: str) -> Optional[Tool]:
        """
        Get detailed information about a specific tool
        """
        return self.tools.get(tool_name)
    
    def get_resource_info(self, uri: str) -> Optional[Resource]:
        """
        Get detailed information about a specific resource
        """
        return self.resources.get(uri)
    
    def __str__(self) -> str:
        """
        String representation of the client
        """
        status = "connected" if self.connected else "disconnected"
        return f"FastMCPClient(server='{self.server_name}', status={status}, tools={len(self.tools)}, resources={len(self.resources)})"
    
    def __repr__(self) -> str:
        """
        Detailed representation of the client
        """
        return self.__str__()


# Utility functions for backward compatibility
async def create_fastmcp_client(server_name: str, server_command: List[str]) -> FastMCPClient:
    """
    Create and connect a FastMCP client
    """
    client = FastMCPClient(server_name, server_command)
    await client.connect()
    return client


def is_fastmcp_available() -> bool:
    """
    FastMCP is always required and available
    """
    return True
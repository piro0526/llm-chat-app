import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResource(BaseModel):
    uri: str
    name: str
    mimeType: Optional[str] = None


class MCPClient:
    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize MCP client with optional server command
        
        Args:
            server_command: Command to start MCP server (e.g., ["uvx", "mcp-server-filesystem", "/path/to/allowed/dir"])
        """
        self.server_command = server_command
        self.process = None
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self._request_id = 0
        self.base_url = None
        
    async def start_server(self) -> bool:
        """Start the MCP server process"""
        if not self.server_command:
            logger.warning("No server command provided, using mock tools")
            await self._initialize_mock_tools()
            return True
            
        try:
            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize the connection
            await self._initialize_connection()
            await self._load_tools()
            await self._load_resources()
            
            logger.info(f"MCP server started with {len(self.tools)} tools and {len(self.resources)} resources")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            await self._initialize_mock_tools()
            return False
    
    async def _initialize_connection(self):
        """Initialize the MCP connection with capability negotiation"""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "llm-chat-app",
                    "version": "1.0.0"
                }
            }
        }
        
        await self._send_request(init_request)
    
    async def _load_tools(self):
        """Load available tools from the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list"
        }
        
        try:
            response = await self._send_request(request)
            if response and "result" in response and "tools" in response["result"]:
                for tool_data in response["result"]["tools"]:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {})
                    )
                    self.tools[tool.name] = tool
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")
    
    async def _load_resources(self):
        """Load available resources from the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/list"
        }
        
        try:
            response = await self._send_request(request)
            if response and "result" in response and "resources" in response["result"]:
                for resource_data in response["result"]["resources"]:
                    resource = MCPResource(
                        uri=resource_data["uri"],
                        name=resource_data.get("name", resource_data["uri"]),
                        mimeType=resource_data.get("mimeType")
                    )
                    self.resources[resource.uri] = resource
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to the MCP server"""
        if not self.process:
            return None
            
        try:
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.decode())
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
        
        return None
    
    def _get_next_id(self) -> int:
        """Get the next request ID"""
        self._request_id += 1
        return self._request_id
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool with the given arguments"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await self._send_request(request)
            if response and "result" in response:
                content = response["result"].get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "No response")
            return "No response from tool"
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """Read content from an MCP resource"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        try:
            response = await self._send_request(request)
            if response and "result" in response:
                contents = response["result"].get("contents", [])
                if contents and len(contents) > 0:
                    return contents[0].get("text", "")
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
        
        return None
    
    async def _initialize_mock_tools(self):
        """Initialize mock tools for development/fallback"""
        mock_tools = [
            MCPTool(
                name="filesystem_read",
                description="Read content from a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file to read"}
                    },
                    "required": ["path"]
                }
            ),
            MCPTool(
                name="filesystem_write",
                description="Write content to a file", 
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file to write"},
                        "content": {"type": "string", "description": "Content to write to the file"}
                    },
                    "required": ["path", "content"]
                }
            ),
            MCPTool(
                name="filesystem_list",
                description="List files and directories",
                input_schema={
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Path to list contents of"}
                    },
                    "required": ["path"]
                }
            ),
            MCPTool(
                name="web_search",
                description="Search the web for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                    },
                    "required": ["query"]
                }
            )
        ]
        
        for tool in mock_tools:
            self.tools[tool.name] = tool
        
        logger.info(f"Initialized {len(mock_tools)} mock tools")
    
    async def close(self):
        """Close the MCP client and terminate server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error closing MCP server: {e}")
    
    def get_available_tools(self) -> List[MCPTool]:
        """Get list of available tools"""
        return list(self.tools.values())
    
    def get_available_resources(self) -> List[MCPResource]:
        """Get list of available resources"""
        return list(self.resources.values())


# Global MCP client instance (deprecated - use server manager instead)
mcp_client = MCPClient()


async def initialize_mcp_client(server_config: Optional[Dict[str, Any]] = None):
    """Initialize MCP clients using the server manager with FastMCP"""
    from mcp_server_manager import mcp_server_manager
    from mcp_client_fastmcp import is_fastmcp_available
    
    try:
        print("MCP: Using FastMCP for enhanced functionality")
        
        # Start all enabled servers from configuration
        results = await mcp_server_manager.start_enabled_servers()
        active_count = sum(1 for success in results.values() if success)
        
        if active_count > 0:
            print(f"MCP: Started {active_count} servers successfully")
            return True
        else:
            print("MCP: No servers started, falling back to mock client")
            # Initialize mock client as fallback
            global mcp_client
            mcp_client = MCPClient()
            await mcp_client.start_server()
            return False
    except Exception as e:
        print(f"MCP: Error initializing servers: {e}")
        # Initialize mock client as fallback
        global mcp_client
        mcp_client = MCPClient()
        await mcp_client.start_server()
        return False


async def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance (deprecated - use server manager)"""
    global mcp_client
    if not mcp_client.tools:
        await initialize_mcp_client()
    return mcp_client


def get_mcp_server_manager():
    """Get the MCP server manager instance"""
    from mcp_server_manager import mcp_server_manager
    return mcp_server_manager
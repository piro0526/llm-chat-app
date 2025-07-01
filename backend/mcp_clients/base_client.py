"""
Base MCP Client Implementation
Provides 1:1 mapping between client and server with proper MCP protocol handling.
Uses official MCP library implementation.
"""

import asyncio
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import CallToolResult, ListResourcesResult, ListToolsResult, ReadResourceResult


class BaseMCPClient(ABC):
    """Base class for MCP clients with 1:1 server mapping using official MCP implementation."""
    
    def __init__(self, server_name: str, server_command: List[str]):
        self.server_name = server_name
        self.server_command = server_command
        self.session: Optional[ClientSession] = None
        self.connected = False
        self._stdio_context = None
        self._read_stream = None
        self._write_stream = None
    
    async def connect(self) -> bool:
        """Connect to the MCP server using official stdio_client."""
        try:
            # Create server configuration using official MCP parameters
            server_config = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else []
            )
            
            # Use official MCP stdio_client
            self._stdio_context = stdio_client(server_config)
            self._read_stream, self._write_stream = await self._stdio_context.__aenter__()
            
            # Create session with official streams
            self.session = ClientSession(self._read_stream, self._write_stream)
            
            # Perform MCP initialization handshake
            init_result = await self.session.initialize()
            
            if init_result:
                self.connected = True
                await self._on_connected()
                return True
            else:
                await self._cleanup_connection()
                return False
                
        except Exception as e:
            print(f"Error connecting to {self.server_name}: {e}")
            await self._cleanup_connection()
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self._cleanup_connection()
        self.connected = False
        await self._on_disconnected()
    
    async def _cleanup_connection(self):
        """Clean up MCP connection."""
        # Close MCP session if exists
        if self.session:
            try:
                # Session cleanup is handled by context manager
                pass
            except Exception as e:
                print(f"Error during session cleanup: {e}")
            finally:
                self.session = None
        
        # Close stdio context if exists
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing stdio context: {e}")
            finally:
                self._stdio_context = None
                self._read_stream = None
                self._write_stream = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        self._ensure_connected()
        
        try:
            result: ListToolsResult = await self.session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in result.tools
            ]
        except Exception as e:
            print(f"Error listing tools from {self.server_name}: {e}")
            return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the server."""
        self._ensure_connected()
        
        try:
            result: ListResourcesResult = await self.session.list_resources()
            return [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                }
                for resource in result.resources
            ]
        except Exception as e:
            print(f"Error listing resources from {self.server_name}: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the server."""
        self._ensure_connected()
        
        try:
            result: CallToolResult = await self.session.call_tool(tool_name, arguments)
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return '{"error": "No content returned"}'
                
        except Exception as e:
            return f'{{"error": "Tool call failed: {str(e)}"}}'
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the server."""
        self._ensure_connected()
        
        try:
            result: ReadResourceResult = await self.session.read_resource(uri)
            
            # Extract text content from result
            if result.contents and len(result.contents) > 0:
                return result.contents[0].text
            else:
                return '{"error": "No content returned"}'
                
        except Exception as e:
            return f'{{"error": "Resource read failed: {str(e)}"}}'
    
    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        if not self.connected or not self.session:
            return False
        
        try:
            # Try to list tools as a health check
            await self.list_tools()
            return True
        except Exception:
            return False
    
    def _ensure_connected(self):
        """Ensure the client is connected."""
        if not self.connected or not self.session:
            raise RuntimeError(f"{self.server_name} not connected")
    
    @abstractmethod
    def _get_server_cwd(self) -> Optional[str]:
        """Get the working directory for the server process."""
        pass
    
    async def _on_connected(self):
        """Called when successfully connected to server."""
        print(f"Connected to {self.server_name} server")
    
    async def _on_disconnected(self):
        """Called when disconnected from server."""
        print(f"Disconnected from {self.server_name} server")


class TimeServerClient(BaseMCPClient):
    """Client for the time server."""
    
    def __init__(self, server_path: str):
        super().__init__(
            server_name="time-server",
            server_command=[sys.executable, server_path]
        )
        self.server_path = server_path
    
    def _get_server_cwd(self) -> Optional[str]:
        """Get server working directory."""
        import os
        return os.path.dirname(self.server_path)
    
    async def get_current_time(self, timezone: str = "UTC") -> str:
        """Get current time using the time server."""
        return await self.call_tool("get_current_time", {"timezone": timezone})
    
    async def convert_time(self, time_str: str, source_tz: str, target_tz: str) -> str:
        """Convert time between timezones."""
        return await self.call_tool("convert_time", {
            "time_str": time_str,
            "source_timezone": source_tz,
            "target_timezone": target_tz
        })
    
    async def time_difference(self, tz1: str, tz2: str) -> str:
        """Calculate time difference between timezones."""
        return await self.call_tool("time_difference", {
            "timezone1": tz1,
            "timezone2": tz2
        })
    
    async def list_timezones(self, region: Optional[str] = None) -> str:
        """List available timezones."""
        args = {}
        if region:
            args["region"] = region
        return await self.call_tool("list_timezones", args)


def create_client(server_type: str, **kwargs) -> BaseMCPClient:
    """Factory function to create MCP clients."""
    if server_type == "time":
        return TimeServerClient(kwargs.get("server_path", "servers/time_server.py"))
    else:
        raise ValueError(f"Unknown server type: {server_type}")


async def test_client():
    """Test the MCP client implementation."""
    print("=== Testing MCP Client ===")
    
    # Create time server client
    client = create_client("time", server_path="/app/servers/time_server.py")
    
    try:
        # Connect to server
        connected = await client.connect()
        print(f"Connection: {'✅ SUCCESS' if connected else '❌ FAILED'}")
        
        if connected:
            # Test tools listing
            tools = await client.list_tools()
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            
            # Test resource listing
            resources = await client.list_resources()
            print(f"Available resources: {len(resources)}")
            for resource in resources:
                print(f"  - {resource['uri']}: {resource['name']}")
            
            # Test tool calls
            if isinstance(client, TimeServerClient):
                tokyo_time = await client.get_current_time("Asia/Tokyo")
                print(f"Tokyo time: {tokyo_time[:100]}...")
        
    except Exception as e:
        print(f"Test error: {e}")
    
    finally:
        await client.disconnect()
        print("Client disconnected")


if __name__ == "__main__":
    asyncio.run(test_client())
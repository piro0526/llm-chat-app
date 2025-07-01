#!/usr/bin/env python3
"""
Simple MCP Time Server
Minimal implementation to test MCP protocol.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import List

import pytz
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest


async def main():
    """Main server function."""
    # Create server
    server = Server("simple-time-server")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_time",
                description="Get current UTC time",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(request: CallToolRequest) -> List[TextContent]:
        """Handle tool calls."""
        tool_name = request.params.name
        if tool_name == "get_time":
            current_time = datetime.now(pytz.UTC)
            result = {
                "time": current_time.isoformat(),
                "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            return [TextContent(type="text", text=json.dumps(result))]
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {tool_name}"}))]
    
    # Run server with explicit error handling
    try:
        print("Starting MCP server...", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print("Server streams established", file=sys.stderr)
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    asyncio.run(main())
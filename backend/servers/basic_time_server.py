#!/usr/bin/env python3
"""
Basic MCP Time Server
Minimal working implementation based on MCP examples.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, List, Sequence

import pytz
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    TextContent,
    Tool,
)


def create_server():
    """Create and configure the MCP server."""
    server = Server("basic-time-server")

    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_current_time",
                description="Get the current time in UTC",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (default: UTC)",
                            "default": "UTC"
                        }
                    },
                    "additionalProperties": False
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(request: CallToolRequest) -> Sequence[TextContent]:
        """Handle tool calls."""
        tool_name = request.params.name
        arguments = request.params.arguments or {}
        
        if tool_name == "get_current_time":
            timezone_name = arguments.get("timezone", "UTC")
            
            try:
                if timezone_name.upper() == "UTC":
                    tz = pytz.UTC
                else:
                    tz = pytz.timezone(timezone_name)
                
                current_time = datetime.now(tz)
                
                result = {
                    "time": current_time.isoformat(),
                    "timezone": timezone_name,
                    "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                error_result = {"error": f"Failed to get time: {str(e)}"}
                return [TextContent(type="text", text=json.dumps(error_result))]
        
        else:
            error_result = {"error": f"Unknown tool: {tool_name}"}
            return [TextContent(type="text", text=json.dumps(error_result))]

    return server


async def main():
    """Run the server."""
    server = create_server()
    
    # Run the server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
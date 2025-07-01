#!/usr/bin/env python3
"""
MCP-Compliant Time Server
Implements proper Model Context Protocol for time operations.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import pytz
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
    Resource,
    TextContent,
    Tool,
)


class TimeServer:
    """MCP-compliant time server implementation."""
    
    def __init__(self):
        self.server = Server("time-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available time-related tools."""
            return [
                Tool(
                    name="get_current_time",
                    description="Get the current time in a specific timezone. Supports IANA timezone names.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "Timezone name (e.g., 'America/New_York', 'Asia/Tokyo')",
                                "default": "UTC"
                            }
                        }
                    }
                ),
                Tool(
                    name="convert_time",
                    description="Convert time from one timezone to another. Handles DST automatically.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "time_str": {
                                "type": "string",
                                "description": "Time string in ISO format (e.g., '2024-01-15 14:30:00')"
                            },
                            "source_timezone": {
                                "type": "string",
                                "description": "Source timezone name"
                            },
                            "target_timezone": {
                                "type": "string",
                                "description": "Target timezone name"
                            }
                        },
                        "required": ["time_str", "source_timezone", "target_timezone"]
                    }
                ),
                Tool(
                    name="time_difference",
                    description="Calculate the current time difference between two timezones.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timezone1": {
                                "type": "string",
                                "description": "First timezone name"
                            },
                            "timezone2": {
                                "type": "string",
                                "description": "Second timezone name"
                            }
                        },
                        "required": ["timezone1", "timezone2"]
                    }
                ),
                Tool(
                    name="list_timezones",
                    description="List available timezones, optionally filtered by region.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "Filter by region (e.g., 'America', 'Europe', 'Asia')"
                            }
                        }
                    }
                )
            ]
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available time-related resources."""
            return [
                Resource(
                    uri="time://current/utc",
                    name="Current UTC Time",
                    description="Current UTC time as a resource",
                    mimeType="application/json"
                ),
                Resource(
                    uri="time://timezones/common",
                    name="Common Timezones",
                    description="List of commonly used IANA timezones",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(request: ReadResourceRequest) -> str:
            """Read time-related resources."""
            uri = request.uri
            
            if uri == "time://current/utc":
                current_utc = datetime.now(pytz.UTC)
                return json.dumps({
                    "current_time": current_utc.isoformat(),
                    "formatted": current_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "timestamp": current_utc.timestamp(),
                    "day_of_week": current_utc.strftime("%A")
                }, indent=2)
            
            elif uri == "time://timezones/common":
                common_timezones = [
                    "UTC", "America/New_York", "America/Chicago", "America/Denver",
                    "America/Los_Angeles", "Europe/London", "Europe/Paris",
                    "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata",
                    "Australia/Sydney", "Pacific/Auckland"
                ]
                return json.dumps({
                    "common_timezones": common_timezones,
                    "total_available": len(pytz.all_timezones),
                    "note": "Use list_timezones tool for full listing with filtering"
                }, indent=2)
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> Sequence[TextContent]:
            """Handle tool calls following MCP specification."""
            tool_name = request.params.name
            arguments = request.params.arguments or {}
            
            try:
                if tool_name == "get_current_time":
                    result = await self._get_current_time(arguments.get("timezone", "UTC"))
                    
                elif tool_name == "convert_time":
                    result = await self._convert_time(
                        arguments["time_str"],
                        arguments["source_timezone"],
                        arguments["target_timezone"]
                    )
                    
                elif tool_name == "time_difference":
                    result = await self._time_difference(
                        arguments["timezone1"],
                        arguments["timezone2"]
                    )
                    
                elif tool_name == "list_timezones":
                    result = await self._list_timezones(arguments.get("region"))
                    
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                    
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                error_result = {"error": str(e), "tool": tool_name}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def _get_current_time(self, timezone: str = "UTC") -> Dict[str, Any]:
        """Get current time implementation."""
        try:
            if timezone.upper() == "UTC":
                tz = pytz.UTC
            else:
                tz = pytz.timezone(timezone)
            
            current_time = datetime.now(tz)
            
            return {
                "current_time": current_time.isoformat(),
                "timezone": timezone,
                "formatted_time": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "day_of_week": current_time.strftime("%A"),
                "is_dst": current_time.dst() is not None and current_time.dst().total_seconds() > 0,
                "utc_offset": current_time.strftime("%z"),
                "unix_timestamp": current_time.timestamp()
            }
        except Exception as e:
            raise Exception(f"Error getting current time: {str(e)}")
    
    async def _convert_time(self, time_str: str, source_timezone: str, target_timezone: str) -> Dict[str, Any]:
        """Convert time implementation."""
        try:
            # Parse the time string
            try:
                if "+" in time_str or time_str.endswith("Z"):
                    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(time_str)
                    source_tz = pytz.timezone(source_timezone)
                    dt = source_tz.localize(dt)
            except ValueError:
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"]:
                    try:
                        dt = datetime.strptime(time_str, fmt)
                        source_tz = pytz.timezone(source_timezone)
                        dt = source_tz.localize(dt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Unable to parse time string: {time_str}")

            # Convert to target timezone
            target_tz = pytz.timezone(target_timezone)
            converted_dt = dt.astimezone(target_tz)
            
            # Calculate time difference
            time_diff = converted_dt.utcoffset() - dt.utcoffset()
            
            return {
                "source": {
                    "time": dt.isoformat(),
                    "timezone": source_timezone,
                    "formatted": dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "is_dst": dt.dst() is not None and dt.dst().total_seconds() > 0
                },
                "target": {
                    "time": converted_dt.isoformat(),
                    "timezone": target_timezone,
                    "formatted": converted_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "is_dst": converted_dt.dst() is not None and converted_dt.dst().total_seconds() > 0
                },
                "time_difference_hours": time_diff.total_seconds() / 3600
            }
        except Exception as e:
            raise Exception(f"Error converting time: {str(e)}")
    
    async def _time_difference(self, timezone1: str, timezone2: str) -> Dict[str, Any]:
        """Time difference implementation."""
        try:
            tz1 = pytz.timezone(timezone1)
            tz2 = pytz.timezone(timezone2)
            
            now = datetime.now(pytz.UTC)
            time1 = now.astimezone(tz1)
            time2 = now.astimezone(tz2)
            
            offset_diff = time2.utcoffset() - time1.utcoffset()
            hours_diff = offset_diff.total_seconds() / 3600
            
            return {
                "timezone1": {
                    "name": timezone1,
                    "current_time": time1.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "utc_offset": time1.strftime("%z")
                },
                "timezone2": {
                    "name": timezone2,
                    "current_time": time2.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "utc_offset": time2.strftime("%z")
                },
                "difference_hours": hours_diff,
                "difference_description": f"{timezone2} is {hours_diff:+.1f} hours from {timezone1}"
            }
        except Exception as e:
            raise Exception(f"Error calculating time difference: {str(e)}")
    
    async def _list_timezones(self, region: Optional[str] = None) -> Dict[str, Any]:
        """List timezones implementation."""
        try:
            all_timezones = list(pytz.all_timezones)
            
            if region:
                filtered_timezones = [
                    tz for tz in all_timezones
                    if tz.lower().startswith(region.lower())
                ]
                timezones = sorted(filtered_timezones)[:50]  # Limit to 50
                result = {
                    "region": region,
                    "count": len(filtered_timezones),
                    "timezones": timezones,
                    "total_available": len(all_timezones)
                }
            else:
                common_timezones = [
                    "UTC", "America/New_York", "America/Chicago", "America/Denver",
                    "America/Los_Angeles", "Europe/London", "Europe/Paris",
                    "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata",
                    "Australia/Sydney", "Pacific/Auckland"
                ]
                result = {
                    "common_timezones": common_timezones,
                    "total_available": len(all_timezones),
                    "note": "Use region parameter to filter (e.g., 'America', 'Europe', 'Asia')"
                }
            
            return result
        except Exception as e:
            raise Exception(f"Error listing timezones: {str(e)}")
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for the time server."""
    server = TimeServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
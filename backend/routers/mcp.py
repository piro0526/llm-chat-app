from typing import Any, Dict, List

from auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models import User
from pydantic import BaseModel
from sqlalchemy.orm import Session

from mcp import get_mcp_tools

router = APIRouter()


class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class ToolExecutionResponse(BaseModel):
    result: str
    tool_name: str


class MCPToolSpec(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class MCPServerConfig(BaseModel):
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    enabled: bool = True


@router.get("/tools")
async def get_available_tools(current_user: User = Depends(get_current_user)):
    """Get all available MCP tools"""
    try:
        tools = get_mcp_tools()

        # Convert LangChain tools to API format
        all_tools = []
        for tool in tools:
            all_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": (
                        getattr(tool, "args_schema", {}).schema()
                        if hasattr(tool, "args_schema") and tool.args_schema
                        else {}
                    ),
                    "server": "mcp",
                }
            )

        return all_tools
    except Exception as e:
        return []


@router.get("/tools/{tool_name}")
def get_tool_details(tool_name: str, current_user: User = Depends(get_current_user)):
    """Get details for a specific tool"""
    tools = get_mcp_tools()
    tool = next((t for t in tools if t.name == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": (
            getattr(tool, "args_schema", {}).schema() if hasattr(tool, "args_schema") and tool.args_schema else {}
        ),
    }


@router.post("/tools/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest, current_user: User = Depends(get_current_user)):
    """Execute an MCP tool"""
    try:
        tools = get_mcp_tools()
        tool = next((t for t in tools if t.name == request.tool_name), None)

        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        # Execute the LangChain tool
        result = await tool.arun(**request.parameters)

        return ToolExecutionResponse(result=result, tool_name=request.tool_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")


@router.post("/server/configure")
async def configure_mcp_server(config: MCPServerConfig, current_user: User = Depends(get_current_user)):
    """Configure MCP server (placeholder for future implementation)"""
    return {"message": "MCP server configuration not yet implemented"}


@router.get("/servers/status")
async def get_mcp_servers_status(current_user: User = Depends(get_current_user)):
    """Get status of MCP servers"""
    tools = get_mcp_tools()
    return {
        "summary": {"total_servers": 0, "running_servers": 0, "enabled_servers": 0, "total_tools": len(tools)},
        "servers": {},
        "message": "No MCP servers configured",
    }


@router.post("/servers/{server_name}/start")
async def start_mcp_server(server_name: str, current_user: User = Depends(get_current_user)):
    """Start MCP server (placeholder)"""
    return {"message": f"MCP server management not yet implemented"}


@router.post("/servers/{server_name}/stop")
async def stop_mcp_server(server_name: str, current_user: User = Depends(get_current_user)):
    """Stop MCP server (placeholder)"""
    return {"message": f"MCP server management not yet implemented"}


@router.post("/servers/reload-config")
async def reload_mcp_config(current_user: User = Depends(get_current_user)):
    """Reload MCP configuration (placeholder)"""
    return {"message": "MCP configuration management not yet implemented"}


@router.get("/resources")
async def get_available_resources(current_user: User = Depends(get_current_user)):
    """Get MCP resources (placeholder)"""
    return []


@router.post("/tools/register")
def register_custom_tool(tool: MCPToolSpec, current_user: User = Depends(get_current_user)):
    """Register custom MCP tool (placeholder)"""
    return {"message": "Custom tool registration not yet implemented", "tool_name": tool.name}

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user
from mcp_tools import mcp_registry, MCPToolSpec
from mcp_client import get_mcp_client, initialize_mcp_client, get_mcp_server_manager
from pydantic import BaseModel

router = APIRouter()


class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class ToolExecutionResponse(BaseModel):
    result: str
    tool_name: str


class MCPServerConfig(BaseModel):
    type: str
    allowed_directory: str = None
    api_key: str = None


@router.get("/tools")
async def get_available_tools(current_user: User = Depends(get_current_user)):
    """Get all available MCP tools from all servers"""
    try:
        server_manager = get_mcp_server_manager()
        mcp_tools = server_manager.get_all_tools()
        legacy_tools = mcp_registry.get_all_tools()
        
        # Convert MCP tools to MCPToolSpec format
        all_tools = []
        for tool in mcp_tools:
            all_tools.append({
                "name": tool["full_name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
                "server": tool["server"]
            })
        
        # Add legacy tools
        for tool in legacy_tools:
            all_tools.append({
                "name": f"legacy_{tool.name}",
                "description": tool.description,
                "parameters": tool.parameters,
                "server": "legacy"
            })
        
        return all_tools
    except Exception as e:
        # Fallback to legacy tools
        legacy_tools = mcp_registry.get_all_tools()
        return [{"name": f"legacy_{tool.name}", "description": tool.description, "parameters": tool.parameters, "server": "legacy"} for tool in legacy_tools]


@router.get("/tools/{tool_name}", response_model=MCPToolSpec)
def get_tool_details(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get details for a specific tool"""
    tool = mcp_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.post("/tools/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute an MCP tool"""
    try:
        # Check if it's a legacy tool
        if request.tool_name.startswith("legacy_"):
            actual_tool_name = request.tool_name[7:]  # Remove "legacy_" prefix
            tool = mcp_registry.get_tool(actual_tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail="Legacy tool not found")
            
            result = mcp_registry.execute_tool(actual_tool_name, request.parameters)
        else:
            # Parse server:tool format
            if ":" in request.tool_name:
                server_name, tool_name = request.tool_name.split(":", 1)
            else:
                # Fallback: find the tool in any server
                server_manager = get_mcp_server_manager()
                all_tools = server_manager.get_all_tools()
                matching_tools = [t for t in all_tools if t["name"] == request.tool_name]
                
                if not matching_tools:
                    raise HTTPException(status_code=404, detail="MCP tool not found")
                
                server_name = matching_tools[0]["server"]
                tool_name = request.tool_name
            
            # Execute tool on specific server
            server_manager = get_mcp_server_manager()
            result = await server_manager.call_tool(server_name, tool_name, request.parameters)
        
        return ToolExecutionResponse(
            result=result,
            tool_name=request.tool_name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing tool: {str(e)}"
        )


@router.post("/server/configure")
async def configure_mcp_server(
    config: MCPServerConfig,
    current_user: User = Depends(get_current_user)
):
    """Configure MCP server with specific settings"""
    try:
        # Initialize MCP client with new configuration
        await initialize_mcp_client(config.dict())
        return {"message": f"MCP server configured successfully with type: {config.type}"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring MCP server: {str(e)}"
        )


@router.get("/servers/status")
async def get_mcp_servers_status(current_user: User = Depends(get_current_user)):
    """Get status of all MCP servers"""
    try:
        server_manager = get_mcp_server_manager()
        status = server_manager.get_server_status()
        
        # Add summary information
        total_servers = len(status)
        running_servers = sum(1 for s in status.values() if s["running"])
        enabled_servers = sum(1 for s in status.values() if s["enabled"])
        total_tools = sum(s["tools_count"] for s in status.values())
        total_resources = sum(s["resources_count"] for s in status.values())
        
        return {
            "summary": {
                "total_servers": total_servers,
                "running_servers": running_servers,
                "enabled_servers": enabled_servers,
                "total_tools": total_tools,
                "total_resources": total_resources
            },
            "servers": status
        }
    except Exception as e:
        return {
            "summary": {
                "total_servers": 0,
                "running_servers": 0,
                "enabled_servers": 0,
                "total_tools": 0,
                "total_resources": 0
            },
            "servers": {},
            "error": str(e)
        }


@router.post("/servers/{server_name}/start")
async def start_mcp_server(
    server_name: str,
    current_user: User = Depends(get_current_user)
):
    """Start a specific MCP server"""
    try:
        server_manager = get_mcp_server_manager()
        success = await server_manager.start_server(server_name)
        
        if success:
            return {"message": f"Server '{server_name}' started successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start server '{server_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting server '{server_name}': {str(e)}"
        )


@router.post("/servers/{server_name}/stop")
async def stop_mcp_server(
    server_name: str,
    current_user: User = Depends(get_current_user)
):
    """Stop a specific MCP server"""
    try:
        server_manager = get_mcp_server_manager()
        success = await server_manager.stop_server(server_name)
        
        if success:
            return {"message": f"Server '{server_name}' stopped successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop server '{server_name}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping server '{server_name}': {str(e)}"
        )


@router.post("/servers/reload-config")
async def reload_mcp_config(current_user: User = Depends(get_current_user)):
    """Reload MCP server configuration from file"""
    try:
        server_manager = get_mcp_server_manager()
        server_manager.reload_config()
        return {"message": "MCP configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reloading configuration: {str(e)}"
        )


@router.get("/resources")
async def get_available_resources(current_user: User = Depends(get_current_user)):
    """Get all available MCP resources from all servers"""
    try:
        server_manager = get_mcp_server_manager()
        resources = server_manager.get_all_resources()
        return resources
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting resources: {str(e)}"
        )


@router.post("/tools/register")
def register_custom_tool(
    tool: MCPToolSpec,
    current_user: User = Depends(get_current_user)
):
    """Register a custom MCP tool (placeholder for future implementation)"""
    # In a full implementation, you might want to:
    # 1. Validate the tool specification
    # 2. Store it in the database per user
    # 3. Implement sandboxed execution
    
    mcp_registry.register_tool(tool)
    return {"message": f"Tool '{tool.name}' registered successfully"}
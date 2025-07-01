from typing import List

from langchain_core.tools import BaseTool


def get_mcp_tools() -> List[BaseTool]:
    """
    Get available MCP tools.

    Returns empty list until MCP servers are configured.
    """
    return []


def initialize_mcp() -> bool:
    """
    Initialize MCP integration.

    Returns True as placeholder until MCP servers are implemented.
    """
    return True


def cleanup_mcp():
    """
    Cleanup MCP connections.

    Placeholder until MCP servers are implemented.
    """
    pass

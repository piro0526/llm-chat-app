import yaml
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel
from mcp_client_fastmcp import FastMCPClient, is_fastmcp_available

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    command: List[str]
    args: List[str] = []
    description: str = ""
    enabled: bool = True
    env: Dict[str, str] = {}


class MCPServerManager:
    def __init__(self, config_file: str = "mcp_servers.yaml"):
        self.config_file = config_file
        self.servers: Dict[str, FastMCPClient] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.global_settings: Dict[str, Any] = {}
        self._load_config()
        
        # FastMCP is required
        logger.info("Using FastMCP for MCP server management")
    
    def _load_config(self):
        """Load MCP server configuration from YAML file"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.warning(f"MCP config file not found: {self.config_file}")
                self._create_default_config()
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load server configurations
            if 'mcp_servers' in config:
                for server_name, server_config in config['mcp_servers'].items():
                    try:
                        self.server_configs[server_name] = MCPServerConfig(**server_config)
                    except Exception as e:
                        logger.error(f"Invalid config for server {server_name}: {e}")
            
            # Load global settings
            self.global_settings = config.get('global_settings', {})
            
            logger.info(f"Loaded {len(self.server_configs)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            'mcp_servers': {
                'filesystem': {
                    'command': ['uvx', 'mcp-server-filesystem'],
                    'args': ['/tmp/mcp-workspace'],
                    'description': 'File system operations',
                    'enabled': True,
                    'env': {}
                },
                'time': {
                    'command': ['uvx', 'mcp-server-time'],
                    'args': [],
                    'description': 'Time and date operations',
                    'enabled': True,
                    'env': {}
                }
            },
            'global_settings': {
                'max_servers': 5,
                'timeout_seconds': 30,
                'workspace_directory': '/tmp/mcp-workspace'
            }
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Created default MCP config file: {self.config_file}")
            
            # Load the default config
            for server_name, server_config in default_config['mcp_servers'].items():
                self.server_configs[server_name] = MCPServerConfig(**server_config)
            self.global_settings = default_config['global_settings']
            
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
    
    async def start_server(self, server_name: str) -> bool:
        """Start a specific MCP server"""
        if server_name not in self.server_configs:
            logger.error(f"Server config not found: {server_name}")
            return False
        
        config = self.server_configs[server_name]
        if not config.enabled:
            logger.info(f"Server {server_name} is disabled")
            return False
        
        if server_name in self.servers:
            logger.warning(f"Server {server_name} is already running")
            return True
        
        try:
            # Prepare server command
            full_command = config.command + config.args
            
            # Create FastMCP client for this server
            client = FastMCPClient(server_name=server_name, server_command=full_command)
            
            # Set environment variables
            if config.env:
                for key, value in config.env.items():
                    os.environ[key] = value
            
            # Connect to the server
            success = await client.connect()
            if success:
                self.servers[server_name] = client
                logger.info(f"Started MCP server: {server_name}")
                return True
            else:
                logger.error(f"Failed to start MCP server: {server_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server {server_name}: {e}")
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server"""
        if server_name not in self.servers:
            logger.warning(f"Server {server_name} is not running")
            return True
        
        try:
            await self.servers[server_name].disconnect()
            del self.servers[server_name]
            logger.info(f"Stopped MCP server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping server {server_name}: {e}")
            return False
    
    async def start_enabled_servers(self) -> Dict[str, bool]:
        """Start all enabled MCP servers"""
        results = {}
        
        # Ensure workspace directory exists
        workspace_dir = self.global_settings.get('workspace_directory', '/tmp/mcp-workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        
        for server_name, config in self.server_configs.items():
            if config.enabled:
                results[server_name] = await self.start_server(server_name)
            else:
                results[server_name] = False
        
        active_servers = sum(1 for success in results.values() if success)
        logger.info(f"Started {active_servers} MCP servers")
        return results
    
    async def stop_all_servers(self):
        """Stop all running MCP servers"""
        for server_name in list(self.servers.keys()):
            await self.stop_server(server_name)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all running servers"""
        all_tools = []
        
        for server_name, client in self.servers.items():
            try:
                tools = client.get_available_tools()
                for tool in tools:
                    all_tools.append({
                        "server": server_name,
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "full_name": f"{server_name}:{tool.name}"
                    })
            except Exception as e:
                logger.error(f"Error getting tools from {server_name}: {e}")
        
        return all_tools
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get all resources from all running servers"""
        all_resources = []
        
        for server_name, client in self.servers.items():
            try:
                resources = client.get_available_resources()
                for resource in resources:
                    all_resources.append({
                        "server": server_name,
                        "uri": resource.uri,
                        "name": resource.name,
                        "mime_type": getattr(resource, 'mime_type', None),
                        "full_name": f"{server_name}:{resource.name}"
                    })
            except Exception as e:
                logger.error(f"Error getting resources from {server_name}: {e}")
        
        return all_resources
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on a specific server"""
        if server_name not in self.servers:
            return f"Server {server_name} not found or not running"
        
        try:
            client = self.servers[server_name]
            return await client.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return f"Error calling tool: {str(e)}"
    
    async def read_resource(self, server_name: str, uri: str) -> Optional[str]:
        """Read a resource from a specific server"""
        if server_name not in self.servers:
            return None
        
        try:
            client = self.servers[server_name]
            return await client.read_resource(uri)
        except Exception as e:
            logger.error(f"Error reading resource {uri} from {server_name}: {e}")
            return None
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured servers"""
        status = {}
        
        for server_name, config in self.server_configs.items():
            is_running = server_name in self.servers
            tool_count = 0
            resource_count = 0
            
            if is_running:
                try:
                    tools = self.servers[server_name].get_available_tools()
                    resources = self.servers[server_name].get_available_resources()
                    tool_count = len(tools)
                    resource_count = len(resources)
                except Exception:
                    pass
            
            status[server_name] = {
                "enabled": config.enabled,
                "running": is_running,
                "description": config.description,
                "tools_count": tool_count,
                "resources_count": resource_count,
                "command": " ".join(config.command + config.args)
            }
        
        return status
    
    def reload_config(self):
        """Reload configuration from file"""
        old_configs = self.server_configs.copy()
        self._load_config()
        
        # Check for changes and log them
        for server_name in set(old_configs.keys()) | set(self.server_configs.keys()):
            if server_name not in old_configs:
                logger.info(f"New server config added: {server_name}")
            elif server_name not in self.server_configs:
                logger.info(f"Server config removed: {server_name}")
            elif old_configs[server_name] != self.server_configs[server_name]:
                logger.info(f"Server config changed: {server_name}")


# Global server manager instance
mcp_server_manager = MCPServerManager()
"""
MCP Client Manager
Manages multiple MCP clients with configuration-based startup and lifecycle management.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_client import BaseMCPClient, TimeServerClient

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manager for multiple MCP clients with configuration-based startup."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "mcp_config.json"
        self.clients: Dict[str, BaseMCPClient] = {}
        self.config: Dict[str, Any] = {}
        self.running = False
        self._health_monitor_task: Optional[asyncio.Task] = None
    
    async def load_config(self) -> bool:
        """Load MCP configuration from file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Create default configuration
                default_config = {
                    "servers": {
                        "time-server": {
                            "type": "time",
                            "enabled": True,
                            "server_path": "/app/servers/time_server.py",
                            "description": "Time operations server with timezone support"
                        }
                    },
                    "global_settings": {
                        "startup_timeout": 10,
                        "health_check_interval": 60,
                        "max_retries": 3
                    }
                }
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default MCP configuration at {config_file}")
            
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                logger.info(f"Loaded MCP configuration from {config_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {e}")
            return False
    
    async def start_clients(self) -> bool:
        """Start all enabled MCP clients based on configuration."""
        if not self.config:
            if not await self.load_config():
                return False
        
        self.running = True
        success_count = 0
        
        servers = self.config.get("servers", {})
        global_settings = self.config.get("global_settings", {})
        startup_timeout = global_settings.get("startup_timeout", 10)
        
        for server_name, server_config in servers.items():
            if not server_config.get("enabled", True):
                logger.info(f"Skipping disabled server: {server_name}")
                continue
            
            try:
                # Create client based on type
                client = self._create_client(server_name, server_config)
                if not client:
                    logger.error(f"Failed to create client for {server_name}")
                    continue
                
                # Start client with timeout
                connected = await asyncio.wait_for(
                    client.connect(),
                    timeout=startup_timeout
                )
                
                if connected:
                    self.clients[server_name] = client
                    success_count += 1
                    logger.info(f"Successfully started MCP client: {server_name}")
                else:
                    logger.error(f"Failed to connect MCP client: {server_name}")
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout connecting to MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error starting MCP client {server_name}: {e}")
        
        logger.info(f"Started {success_count}/{len(servers)} MCP clients")
        return success_count > 0
    
    async def stop_clients(self):
        """Stop all running MCP clients."""
        self.running = False
        
        # Stop health monitoring
        if self._health_monitor_task and not self._health_monitor_task.done():
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all clients
        for server_name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Stopped MCP client: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping MCP client {server_name}: {e}")
        
        self.clients.clear()
        logger.info("All MCP clients stopped")
    
    async def restart_client(self, server_name: str) -> bool:
        """Restart a specific MCP client."""
        if server_name not in self.config.get("servers", {}):
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        # Stop existing client if running
        if server_name in self.clients:
            try:
                await self.clients[server_name].disconnect()
                del self.clients[server_name]
            except Exception as e:
                logger.error(f"Error stopping client {server_name}: {e}")
        
        # Start new client
        server_config = self.config["servers"][server_name]
        if not server_config.get("enabled", True):
            logger.info(f"Server {server_name} is disabled")
            return False
        
        try:
            client = self._create_client(server_name, server_config)
            if client and await client.connect():
                self.clients[server_name] = client
                logger.info(f"Restarted MCP client: {server_name}")
                return True
        except Exception as e:
            logger.error(f"Error restarting client {server_name}: {e}")
        
        return False
    
    async def get_client(self, server_name: str) -> Optional[BaseMCPClient]:
        """Get a specific MCP client by name."""
        return self.clients.get(server_name)
    
    async def list_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools from all connected clients."""
        all_tools = {}
        
        for server_name, client in self.clients.items():
            try:
                if await client.health_check():
                    tools = await client.list_tools()
                    all_tools[server_name] = tools
                else:
                    logger.warning(f"Health check failed for {server_name}")
                    all_tools[server_name] = []
            except Exception as e:
                logger.error(f"Error listing tools from {server_name}: {e}")
                all_tools[server_name] = []
        
        return all_tools
    
    async def list_available_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available resources from all connected clients."""
        all_resources = {}
        
        for server_name, client in self.clients.items():
            try:
                if await client.health_check():
                    resources = await client.list_resources()
                    all_resources[server_name] = resources
                else:
                    logger.warning(f"Health check failed for {server_name}")
                    all_resources[server_name] = []
            except Exception as e:
                logger.error(f"Error listing resources from {server_name}: {e}")
                all_resources[server_name] = []
        
        return all_resources
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on a specific server."""
        client = self.clients.get(server_name)
        if not client:
            return json.dumps({"error": f"Server {server_name} not connected"})
        
        try:
            return await client.call_tool(tool_name, arguments)
        except Exception as e:
            return json.dumps({"error": f"Tool call failed: {str(e)}"})
    
    async def read_resource(self, server_name: str, resource_uri: str) -> str:
        """Read a resource from a specific server."""
        client = self.clients.get(server_name)
        if not client:
            return json.dumps({"error": f"Server {server_name} not connected"})
        
        try:
            return await client.read_resource(resource_uri)
        except Exception as e:
            return json.dumps({"error": f"Resource read failed: {str(e)}"})
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health status of all connected clients."""
        health_status = {}
        
        for server_name, client in self.clients.items():
            try:
                health_status[server_name] = await client.health_check()
            except Exception as e:
                logger.error(f"Health check error for {server_name}: {e}")
                health_status[server_name] = False
        
        return health_status
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the MCP client manager."""
        health_status = await self.health_check()
        
        return {
            "running": self.running,
            "total_servers": len(self.config.get("servers", {})),
            "connected_clients": len(self.clients),
            "healthy_clients": sum(1 for status in health_status.values() if status),
            "clients": {
                name: {
                    "connected": name in self.clients,
                    "healthy": health_status.get(name, False),
                    "config": self.config.get("servers", {}).get(name, {})
                }
                for name in self.config.get("servers", {}).keys()
            }
        }
    
    def _create_client(self, server_name: str, server_config: Dict[str, Any]) -> Optional[BaseMCPClient]:
        """Create MCP client based on configuration."""
        try:
            server_type = server_config.get("type", "")
            
            if server_type == "time":
                server_path = server_config.get("server_path", "/app/servers/time_server.py")
                return TimeServerClient(server_path)
            else:
                logger.error(f"Unknown server type: {server_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating client {server_name}: {e}")
            return None
    
    async def start_health_monitoring(self):
        """Start background health monitoring task."""
        if not self.running or self._health_monitor_task:
            return
        
        async def _monitor():
            global_settings = self.config.get("global_settings", {})
            interval = global_settings.get("health_check_interval", 60)
            
            while self.running:
                try:
                    health_status = await self.health_check()
                    unhealthy_clients = [
                        name for name, healthy in health_status.items() 
                        if not healthy
                    ]
                    
                    if unhealthy_clients:
                        logger.warning(f"Unhealthy MCP clients detected: {unhealthy_clients}")
                        
                        # Attempt to restart unhealthy clients
                        for client_name in unhealthy_clients:
                            logger.info(f"Attempting to restart unhealthy client: {client_name}")
                            await self.restart_client(client_name)
                    
                    await asyncio.sleep(interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
                    await asyncio.sleep(interval)
        
        self._health_monitor_task = asyncio.create_task(_monitor())


# Global MCP client manager instance
mcp_manager = MCPClientManager()


async def get_mcp_manager() -> MCPClientManager:
    """Get the global MCP client manager instance."""
    return mcp_manager


# Initialization function
async def initialize_mcp_clients():
    """Initialize MCP clients on startup."""
    logger.info("Initializing MCP clients...")
    
    success = await mcp_manager.start_clients()
    if success:
        # Start health monitoring in background
        await mcp_manager.start_health_monitoring()
        logger.info("MCP clients initialized successfully")
    else:
        logger.warning("Failed to initialize MCP clients - continuing without MCP functionality")
    
    return success


# Cleanup function
async def cleanup_mcp_clients():
    """Cleanup MCP clients on shutdown."""
    logger.info("Cleaning up MCP clients...")
    await mcp_manager.stop_clients()
    logger.info("MCP clients cleanup completed")


# Test function
async def test_client_manager():
    """Test the MCP client manager implementation."""
    print("=== Testing MCP Client Manager ===")
    
    manager = MCPClientManager()
    
    try:
        # Load configuration
        config_loaded = await manager.load_config()
        print(f"Configuration loaded: {'✅ SUCCESS' if config_loaded else '❌ FAILED'}")
        
        # Start clients
        started = await manager.start_clients()
        print(f"Clients started: {'✅ SUCCESS' if started else '❌ FAILED'}")
        
        if started:
            # Get status
            status = await manager.get_status()
            print(f"Manager status: {json.dumps(status, indent=2)}")
            
            # List tools
            tools = await manager.list_available_tools()
            print(f"Available tools from all servers:")
            for server_name, server_tools in tools.items():
                print(f"  {server_name}: {len(server_tools)} tools")
                for tool in server_tools[:2]:  # Show first 2 tools
                    print(f"    - {tool['name']}: {tool['description'][:50]}...")
            
            # Test tool call
            if "time-server" in manager.clients:
                result = await manager.call_tool("time-server", "get_current_time", {"timezone": "UTC"})
                print(f"Tool call result: {result[:100]}...")
        
    except Exception as e:
        print(f"Test error: {e}")
    
    finally:
        await manager.stop_clients()
        print("Manager test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_client_manager())
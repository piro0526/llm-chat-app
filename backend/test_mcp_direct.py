#!/usr/bin/env python3
"""
Direct MCP Implementation Test
Test MCP using the exact patterns from official documentation.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_official_mcp_client():
    """Test using official MCP client patterns."""
    print("=== Testing Official MCP Client Implementation ===")
    
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        import subprocess
        
        # Start the server process
        server_path = Path(__file__).parent / "servers" / "time_server.py"
        
        # Create server configuration
        server_config = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)]
        )
        
        # Use stdio_client with server config
        async with stdio_client(server_config) as streams:
            read, write = streams
            
            # Create session
            session = ClientSession(read, write)
            
            # Initialize
            init_result = await session.initialize()
            print(f"Initialization: {'✅ SUCCESS' if init_result else '❌ FAILED'}")
            
            if init_result:
                # List tools
                tools_result = await session.list_tools()
                print(f"Tools: {len(tools_result.tools)} available")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Call a tool
                if tools_result.tools:
                    result = await session.call_tool("get_current_time", {"timezone": "UTC"})
                    print(f"Tool call result: {result.content[0].text[:100]}...")
                    print("✅ MCP client working correctly!")
                    return True
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    print("Direct MCP Implementation Test")
    print("=" * 50)
    
    success = await test_official_mcp_client()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Official MCP implementation working!")
        sys.exit(0)
    else:
        print("⚠️  MCP implementation needs fixing")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
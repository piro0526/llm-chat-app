#!/usr/bin/env python3
"""
Test Simple MCP Server
Test the simplified MCP server implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_simple_server():
    """Test the simple MCP server."""
    print("=== Testing Simple MCP Server ===")
    
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        
        # Use basic server
        server_path = Path(__file__).parent / "servers" / "basic_time_server.py"
        
        server_config = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)]
        )
        
        print("Starting server connection...")
        async with stdio_client(server_config) as streams:
            read, write = streams
            print("✅ Connected to server")
            
            # Create session
            session = ClientSession(read, write)
            
            # Initialize with timeout
            print("Initializing session...")
            init_result = await asyncio.wait_for(session.initialize(), timeout=5.0)
            print(f"✅ Session initialized: {init_result}")
            
            if init_result:
                # List tools
                print("Listing tools...")
                tools_result = await session.list_tools()
                print(f"✅ Found {len(tools_result.tools)} tools")
                
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Call tool
                if tools_result.tools:
                    print("Calling tool...")
                    result = await session.call_tool("get_current_time", {"timezone": "UTC"})
                    print(f"✅ Tool result: {result.content[0].text}")
                
                return True
        
        return False
        
    except asyncio.TimeoutError:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    print("Simple MCP Server Test")
    print("=" * 30)
    
    success = await test_simple_server()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 Simple server test PASSED!")
        sys.exit(0)
    else:
        print("❌ Simple server test FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
MCP Debug Script
Systematically debug MCP implementation step by step.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_step1_server_startup():
    """Step 1: Test if server starts correctly."""
    print("=== Step 1: Server Startup Test ===")
    
    try:
        server_path = Path(__file__).parent / "servers" / "time_server.py"
        
        # Start server process directly
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment
        await asyncio.sleep(0.5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server process started successfully")
            
            # Try to send a simple message and see what happens
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "debug-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            process.stdin.write(json.dumps(init_msg) + '\n')
            process.stdin.flush()
            
            # Try to read response with timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                    timeout=5.0
                )
                print(f"✅ Server responded: {response.strip()}")
                result = True
            except asyncio.TimeoutError:
                print("❌ Server did not respond within timeout")
                result = False
            
        else:
            # Process exited
            stderr = process.stderr.read()
            stdout = process.stdout.read()
            print(f"❌ Server process exited immediately")
            print(f"STDERR: {stderr}")
            print(f"STDOUT: {stdout}")
            result = False
        
        # Cleanup
        if process.poll() is None:
            process.terminate()
            process.wait()
        
        return result
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_step2_mcp_library():
    """Step 2: Test MCP library components individually."""
    print("\n=== Step 2: MCP Library Test ===")
    
    try:
        # Test imports
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        print("✅ MCP imports successful")
        
        # Test StdioServerParameters creation
        server_path = Path(__file__).parent / "servers" / "time_server.py"
        server_config = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)]
        )
        print("✅ StdioServerParameters created successfully")
        print(f"   Command: {server_config.command}")
        print(f"   Args: {server_config.args}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP library test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_step3_stdio_client():
    """Step 3: Test stdio_client in isolation."""
    print("\n=== Step 3: stdio_client Test ===")
    
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters
        
        server_path = Path(__file__).parent / "servers" / "time_server.py"
        server_config = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)]
        )
        
        print("Creating stdio_client...")
        stdio_ctx = stdio_client(server_config)
        print("✅ stdio_client created")
        
        print("Entering context...")
        try:
            streams = await asyncio.wait_for(
                stdio_ctx.__aenter__(),
                timeout=10.0
            )
            print("✅ stdio_client context entered")
            read, write = streams
            print(f"✅ Got streams: read={type(read)}, write={type(write)}")
            
            # Exit context
            await stdio_ctx.__aexit__(None, None, None)
            print("✅ stdio_client context exited")
            return True
            
        except asyncio.TimeoutError:
            print("❌ stdio_client context entry timed out")
            return False
        
    except Exception as e:
        print(f"❌ stdio_client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_step4_session():
    """Step 4: Test ClientSession initialization."""
    print("\n=== Step 4: ClientSession Test ===")
    
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        
        server_path = Path(__file__).parent / "servers" / "time_server.py"
        server_config = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)]
        )
        
        async with stdio_client(server_config) as streams:
            read, write = streams
            print("✅ stdio_client streams acquired")
            
            # Create session
            session = ClientSession(read, write)
            print("✅ ClientSession created")
            
            # Try initialization with timeout
            print("Attempting session initialization...")
            init_result = await asyncio.wait_for(
                session.initialize(),
                timeout=10.0
            )
            print(f"✅ Session initialized: {init_result}")
            
            if init_result:
                # Try listing tools
                print("Attempting to list tools...")
                tools_result = await asyncio.wait_for(
                    session.list_tools(),
                    timeout=5.0
                )
                print(f"✅ Tools listed: {len(tools_result.tools)} tools")
                return True
            else:
                print("❌ Session initialization returned False")
                return False
        
    except asyncio.TimeoutError:
        print("❌ Session test timed out")
        return False
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all debug tests."""
    print("MCP Debug Script")
    print("=" * 50)
    
    tests = [
        ("Server Startup", test_step1_server_startup),
        ("MCP Library", test_step2_mcp_library),
        ("stdio_client", test_step3_stdio_client),
        ("ClientSession", test_step4_session),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'✅ PASS' if result else '❌ FAIL'}")
        except Exception as e:
            print(f"{test_name}: ❌ ERROR - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️  SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Inspect A2A server to find correct method names
"""

try:
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.apps.jsonrpc.jsonrpc_app import JSONRPCApplication
    import inspect

    print("Inspecting A2A server structure...")
    print("=" * 50)

    # Try to find method names in JSONRPCApplication
    jsonrpc_methods = [attr for attr in dir(JSONRPCApplication) if not attr.startswith('_')]
    print(f"JSONRPCApplication methods: {jsonrpc_methods}")

    # Look for any method that might handle requests
    for method in jsonrpc_methods:
        attr = getattr(JSONRPCApplication, method)
        if callable(attr):
            sig = inspect.signature(attr)
            print(f"Method {method}: {sig}")

    print("\n" + "=" * 50)
    print("Looking for request handler patterns...")

    # Check if we can find how requests are handled
    from a2a.server.request_handlers import DefaultRequestHandler
    handler_methods = [attr for attr in dir(DefaultRequestHandler) if not attr.startswith('_')]
    print(f"DefaultRequestHandler methods: {handler_methods}")

except Exception as e:
    print(f"Error inspecting A2A: {e}")
    import traceback
    traceback.print_exc()
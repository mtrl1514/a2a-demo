#!/usr/bin/env python3
"""
Find the exact JSON-RPC method names from A2A
"""

try:
    from a2a.server.apps.jsonrpc.jsonrpc_app import JSONRPCApplication

    print("A2A JSON-RPC Method Mapping:")
    print("=" * 50)

    # Get the METHOD_TO_MODEL mapping
    method_mapping = getattr(JSONRPCApplication, 'METHOD_TO_MODEL', {})

    if method_mapping:
        for method_name, model_class in method_mapping.items():
            print(f"Method: '{method_name}' -> Model: {model_class}")
    else:
        print("No METHOD_TO_MODEL found, trying to find it elsewhere...")

        # Try to create an instance and inspect it
        try:
            app = JSONRPCApplication()
            if hasattr(app, 'METHOD_TO_MODEL'):
                method_mapping = app.METHOD_TO_MODEL
                for method_name, model_class in method_mapping.items():
                    print(f"Method: '{method_name}' -> Model: {model_class}")
        except Exception as e:
            print(f"Could not create JSONRPCApplication instance: {e}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
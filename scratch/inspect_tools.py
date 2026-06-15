import json

from windows_computer_use_mcp.app import app


def inspect_tools():
    print(f"Inspecting {len(app._tools)} tools registered with FastMCP:")
    for name, tool in app._tools.items():
        print(f"\nTool: {name}")
        print(f"Description: {tool.description[:100]}...")
        # Accessing schema (FastMCP internal)
        try:
            # FastMCP usually stores the function and its parameters
            # We want to see the JSON schema it would expose
            import inspect

            sig = inspect.signature(tool.fn)
            for param_name, param in sig.parameters.items():
                if hasattr(param.annotation, "model_json_schema"):
                    print(f"  Parameter '{param_name}' schema:")
                    print(json.dumps(param.annotation.model_json_schema(), indent=4))
        except Exception as e:
            print(f"  Could not extract schema for {name}: {e}")


if __name__ == "__main__":
    inspect_tools()

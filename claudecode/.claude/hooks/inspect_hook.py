#!/usr/bin/env python3
import json
import sys

def main():
    # 1. Read JSON data from stdin provided by Claude Code
    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        print(f"Error parsing hook input: {e}", file=sys.stderr)
        sys.exit(0)  # Pass-through on structural errors

    # 2. Extract context information
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # 3. Inspect specific tools
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Guardrail example: Block dangerous commands
        dangerous_tokens = ["rm -rf", "DROP TABLE", "prod-db"]
        if any(token in command for token in dangerous_tokens):
            # Print error to stderr so Claude can read it
            print(f"CRITICAL ERROR: Destructive command blocked by security hook. Do not use dangerous commands.", file=sys.stderr)
            # Exit code 2 forces Claude Code to block execution and pass stderr back to the model
            sys.exit(2)

    elif tool_name in ["WriteFile", "EditFile", "ViewFile"]:
        file_path = tool_input.get("file_path", "")

        # Guardrail example: Protect environment and secret storage files
        if ".env" in file_path or "secrets" in file_path:
            print(
                f"SECURITY ERROR: Access to credential files ({file_path}) is strictly forbidden by policy.",
                file=sys.stderr,
            )
            sys.exit(2)
        elif 'db.ts' in file_path and tool_name in ["WriteFile", "EditFile"]:
            sys.exit(0)
        elif tool_name in ["WriteFile", "EditFile"]:
            sys.exit(2)
        else:
            # Allow read-only access to other files
            sys.exit(0)
    # Allow execution to proceed normally for all other operations
sys.exit(0)

if __name__ == "__main__":
    main()
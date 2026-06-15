#!/usr/bin/env python3
"""Portable workflow runner — executes YAML/JSON workflow files.

Usage:
  uv run python scripts/run-workflow.py path/to/workflow.yaml
  uv run python scripts/run-workflow.py presets/notepad_demo.json
"""

import asyncio, json, os, sys, time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL"] = "1"

from windows_computer_use_mcp.tools.portmanteau_mission import _call_tool, _run_steps


def load_workflow(path: str) -> dict:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(raw)
    return json.loads(raw)


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/run-workflow.py <workflow.json|yaml>")
        sys.exit(1)

    wf = load_workflow(sys.argv[1])
    steps = wf.get("steps", [])
    name = wf.get("name", Path(sys.argv[1]).stem)

    print(f"Running workflow: {name} ({len(steps)} steps)")
    result = await _run_steps(steps, None, f"wf_{int(time.time())}", name)

    print(f"\nResult: {result.status}")
    print(f"Message: {result.message}")
    if result.data:
        steps_data = result.data.get("steps", [])
        for s in steps_data:
            icon = "OK" if s["success"] else "XX"
            print(f"  {icon} {s['label']} ({s['attempts']} attempts)")
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    asyncio.run(main())

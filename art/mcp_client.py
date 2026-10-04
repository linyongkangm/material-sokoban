"""Reusable MCP client for the aseprite server: call tools in one connection.

Usage:
  python mcp_client.py schemas tool1 tool2 ...   # dump input schemas
  python mcp_client.py call tool '<json args>'   # one call
  python mcp_client.py script file.json          # many calls, [[tool, args], ...]
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PY = r"D:\Program Files\Aseprite\aseprite-mcp\.venv\Scripts\python.exe"
ART = r"D:\Materials\sokoban\art"


def _text(res):
    sc = getattr(res, "structured_content", None) or getattr(res, "structuredContent", None)
    if sc is not None:
        return json.dumps(sc)[:2000]
    out = []
    for c in res.content:
        out.append(getattr(c, "text", repr(c)))
    return " | ".join(out) if out else "<empty>"


async def run(mode: str, payload) -> None:
    # cwd=ART so relative filenames from the MCP tools land in the art folder.
    params = StdioServerParameters(command=PY, args=["-m", "aseprite_mcp"], cwd=ART)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if mode == "schemas":
                tools = (await session.list_tools()).tools
                by_name = {t.name: t for t in tools}
                for name in payload:
                    t = by_name.get(name)
                    if t is None:
                        print(f"!! unknown tool: {name}")
                        continue
                    req = t.inputSchema.get("required", [])
                    props = t.inputSchema.get("properties", {})
                    lines = []
                    for k, v in props.items():
                        ty = v.get("type", "?")
                        d = v.get("default", "<none>")
                        star = "*" if k in req else " "
                        lines.append(f"   {star}{k}: {ty} default={json.dumps(d)}")
                    print(f"{name}({', '.join(props)})")
                    print("\n".join(lines))
                    print(f"   desc: {t.description.strip().splitlines()[0]}")
            else:
                calls = payload
                for item in calls:
                    name, args = item[0], item[1] if len(item) > 1 else {}
                    res = await session.call_tool(name, args)
                    err = getattr(res, "is_error", None)
                    if err is None:
                        err = getattr(res, "isError", None)
                    flag = "ERR" if err else "ok "
                    print(f"[{flag}] {name} -> {_text(res)}", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "schemas":
        data = sys.argv[2:]
    elif mode == "call":
        data = [[sys.argv[2], json.loads(sys.argv[3])]]
    else:
        data = json.load(open(sys.argv[2], encoding="utf-8"))
    asyncio.run(run(mode, data))

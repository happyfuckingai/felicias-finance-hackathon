import json
from .server import MCPServerSse, MCPServerStdio
from .agent_tools import CryptoMCPServer

def load_mcp_servers_from_config(config_path="mcp_client/mcp.config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
    servers = []
    for entry in config.get("servers", []):
        if entry["type"] == "sse":
            params = {
                "url": entry["url"],
                "headers": entry.get("headers"),
                "timeout": entry.get("timeout", 5),
                "sse_read_timeout": entry.get("sse_read_timeout", 300)
            }
            servers.append(MCPServerSse(params, name=entry.get("name")))
        elif entry["type"] == "stdio":
            params = {
                "command": entry["command"]
            }
            servers.append(MCPServerStdio(params, name=entry.get("name")))
        elif entry["type"] == "crypto":
            # Create crypto MCP server
            cache_tools = entry.get("cache_tools_list", True)
            name = entry.get("name", "Crypto MCP Server")
            servers.append(CryptoMCPServer(cache_tools_list=cache_tools, name=name))
    return servers
"""
MCP Server for Xray + Caddy Automated Deployment.

This server exposes tools for:
- Checking environment (Caddy/Xray installation status)
- Installing dependencies
- Generating configurations
- Deploying configurations
- Getting subscription links
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from config_generator import ConfigGenerator
from installer import Installer
from subscription import subscription_service

# Initialize MCP server
mcp = FastMCP(
    name="xray-deploy",
    instructions="MCP server for automated Xray + Caddy deployment with XHTTP protocol"
)

# Global state
_current_config: Optional[ConfigGenerator] = None


@mcp.tool()
def check_environment() -> dict:
    """
    Check the current environment status.
    
    Returns installation status of Caddy and Xray,
    along with system information.
    """
    installer = Installer()
    return installer.check_environment()


@mcp.tool()
def install_dependencies() -> dict:
    """
    Install missing Caddy and Xray components.
    
    Requires root privileges. Will skip already installed components.
    """
    installer = Installer()
    return installer.install_missing()


@mcp.tool()
def generate_configs(
    domains: list[str],
    xray_path: str = "/xray",
    xray_port: int = 10000
) -> dict:
    """
    Generate Xray and Caddy configurations.
    
    Args:
        domains: List of domain names (e.g., ["proxy1.example.com", "proxy2.example.com"])
        xray_path: URL path for Xray XHTTP endpoint (default: "/xray")
        xray_port: Local port for Xray to listen on (default: 10000)
    
    Returns:
        Generated configurations and client UUID.
    """
    global _current_config
    
    if not domains:
        return {"error": "At least one domain is required"}
    
    _current_config = ConfigGenerator(
        domains=domains,
        xray_port=xray_port,
        xray_path=xray_path
    )
    
    # Update subscription service
    subscription_service.update_config(
        uuid=_current_config.client_uuid,
        domains=domains,
        path=xray_path
    )
    
    return {
        "success": True,
        "uuid": _current_config.client_uuid,
        "domains": domains,
        "xray_config": _current_config.xray_config.to_dict(),
        "caddyfile": _current_config.generate_caddyfile()
    }


@mcp.tool()
def deploy_configs(
    xray_config_path: str = "/usr/local/etc/xray/config.json",
    caddy_config_path: str = "/etc/caddy/Caddyfile"
) -> dict:
    """
    Deploy generated configurations and restart services.
    
    Args:
        xray_config_path: Path to save Xray config (default: /usr/local/etc/xray/config.json)
        caddy_config_path: Path to save Caddyfile (default: /etc/caddy/Caddyfile)
    
    Returns:
        Deployment status and service restart results.
    """
    global _current_config
    
    if not _current_config:
        return {"error": "No configuration generated. Call generate_configs first."}
    
    results = {"xray": {}, "caddy": {}}
    
    try:
        # Save Xray config
        xray_path = Path(xray_config_path)
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        xray_path.write_text(_current_config.generate_xray_json())
        results["xray"]["config_saved"] = str(xray_path)
        
        # Restart Xray
        xray_restart = subprocess.run(
            ["systemctl", "restart", "xray"],
            capture_output=True,
            text=True
        )
        results["xray"]["restart"] = {
            "success": xray_restart.returncode == 0,
            "message": xray_restart.stderr if xray_restart.returncode != 0 else "OK"
        }
    except Exception as e:
        results["xray"]["error"] = str(e)
    
    try:
        # Save Caddy config
        caddy_path = Path(caddy_config_path)
        caddy_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_path.write_text(_current_config.generate_caddyfile())
        results["caddy"]["config_saved"] = str(caddy_path)
        
        # Reload Caddy
        caddy_reload = subprocess.run(
            ["systemctl", "reload", "caddy"],
            capture_output=True,
            text=True
        )
        results["caddy"]["reload"] = {
            "success": caddy_reload.returncode == 0,
            "message": caddy_reload.stderr if caddy_reload.returncode != 0 else "OK"
        }
    except Exception as e:
        results["caddy"]["error"] = str(e)
    
    return results


@mcp.tool()
def get_subscription(format: str = "base64") -> dict:
    """
    Get subscription link for clients.
    
    Args:
        format: "base64" for Base64 encoded content, "plain" for raw VLESS URIs
    
    Returns:
        Subscription content and node list.
    """
    content = subscription_service.get_subscription(format)
    
    if not content:
        return {"error": "No configuration generated. Call generate_configs first."}
    
    return {
        "format": format,
        "subscription": content,
        "nodes": subscription_service.get_nodes()
    }


@mcp.tool()
def get_status() -> dict:
    """
    Get current service status.
    
    Returns status of Xray and Caddy services.
    """
    status = {}
    
    for service in ["xray", "caddy"]:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True
        )
        status[service] = {
            "active": result.stdout.strip() == "active",
            "status": result.stdout.strip()
        }
    
    return status


# Resource: Current configuration
@mcp.resource("config://current")
def get_current_config() -> str:
    """Get the current configuration as JSON."""
    global _current_config
    
    if not _current_config:
        return json.dumps({"error": "No configuration generated"})
    
    return json.dumps({
        "uuid": _current_config.client_uuid,
        "domains": _current_config.domains,
        "xray_port": _current_config.xray_port,
        "xray_path": _current_config.xray_path
    }, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

"""
Configuration generator for Xray and Caddy.

Generates XHTTP (packet-up mode) configurations for Xray and
corresponding Caddyfile for reverse proxy setup.
"""

import json
import secrets
import string
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def generate_random_path(length: int = 16) -> str:
    """
    Generate a random URL path for obfuscation.
    
    Uses alphanumeric characters to create an inconspicuous path.
    Example: /a7kRmQ2xJ9vN4pL
    """
    chars = string.ascii_letters + string.digits
    random_str = ''.join(secrets.choice(chars) for _ in range(length))
    return f"/{random_str}"


@dataclass
class XrayConfig:
    """Xray server configuration."""
    
    domains: list[str]
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    listen_port: int = 10000
    path: str = "/xray"
    
    def to_dict(self) -> dict:
        """Generate Xray config.json content."""
        return {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [{
                "listen": "127.0.0.1",
                "port": self.listen_port,
                "protocol": "vless",
                "settings": {
                    "clients": [{
                        "id": self.uuid,
                        "flow": ""
                    }],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "xhttp",
                    "xhttpSettings": {
                        "path": self.path,
                        "mode": "auto"
                    }
                }
            }],
            "outbounds": [{
                "protocol": "freedom",
                "tag": "direct"
            }]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Generate JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class CaddyConfig:
    """Caddy reverse proxy configuration."""
    
    domains: list[str]
    xray_port: int = 10000
    xray_path: str = "/xray"
    cdn_host: Optional[str] = None
    
    def to_caddyfile(self) -> str:
        """Generate Caddyfile content for auto-generated xray config.
        
        This is the content for /etc/caddy/conf.d/xray-auto.caddy
        which will be included by the main Caddyfile.
        """
        blocks = []
        
        for domain in self.domains:
            block = f"""{domain} {{
    # XHTTP reverse proxy to Xray
    @xhttp path {self.xray_path}*
    reverse_proxy @xhttp 127.0.0.1:{self.xray_port} {{
        flush_interval -1
        header_up X-Forwarded-For {{remote_host}}
    }}
    
    # Default response for camouflage
    respond "Welcome to {domain}" 200
}}
"""
            blocks.append(block)
        
        # Add CDN info as comment if provided
        if self.cdn_host:
            blocks.insert(0, f"# CDN Host: {self.cdn_host}\n")
        
        return "\n".join(blocks)
    
    def to_main_caddyfile(self) -> str:
        """Generate main Caddyfile that includes auto-generated configs.
        
        This is the content for /etc/caddy/Caddyfile (main config)
        """
        return """{
    # Global config
    admin off
}

# Include all auto-generated configurations
import /etc/caddy/conf.d/*.caddy
"""


class ConfigGenerator:
    """Main configuration generator."""
    
    def __init__(
        self,
        domains: list[str],
        xray_port: int = 10000,
        xray_path: Optional[str] = None,
        client_uuid: Optional[str] = None,
        cdn_host: Optional[str] = None
    ):
        self.domains = domains
        self.xray_port = xray_port
        # Auto-generate random path if not provided, for obfuscation
        self.xray_path = xray_path or generate_random_path()
        self.cdn_host = cdn_host
        self.client_uuid = client_uuid or str(uuid.uuid4())
        
        self._xray_config = XrayConfig(
            domains=domains,
            uuid=self.client_uuid,
            listen_port=xray_port,
            path=self.xray_path
        )
        
        self._caddy_config = CaddyConfig(
            domains=domains,
            xray_port=xray_port,
            xray_path=self.xray_path,
            cdn_host=cdn_host
        )
    
    @property
    def xray_config(self) -> XrayConfig:
        return self._xray_config
    
    @property
    def caddy_config(self) -> CaddyConfig:
        return self._caddy_config
    
    def generate_xray_json(self) -> str:
        """Generate Xray config.json content."""
        return self._xray_config.to_json()
    
    def generate_caddyfile(self) -> str:
        """Generate auto-generated Caddy config for xray."""
        return self._caddy_config.to_caddyfile()
    
    def generate_main_caddyfile(self) -> str:
        """Generate main Caddyfile with include directive."""
        return self._caddy_config.to_main_caddyfile()
    
    def save_configs(
        self,
        xray_path: Optional[Path] = None,
        caddy_main_path: Optional[Path] = None,
        caddy_conf_d_path: Optional[Path] = None
    ) -> tuple[Path, Path, Path]:
        """Save configurations to files.
        
        Args:
            xray_path: Path to Xray config.json (auto-detects if None)
            caddy_main_path: Path to main Caddyfile (auto-detects if None)
            caddy_conf_d_path: Path to auto-generated xray Caddy config (auto-detects if None)
        
        Returns:
            Tuple of (xray_path, caddy_main_path, caddy_conf_d_path)
        """
        import os
        # Auto-detect paths based on deployment mode
        is_docker = os.getenv("DEPLOYMENT_MODE") == "container"
        
        if xray_path is None:
            xray_path = Path("/etc/xray/config.json") if is_docker else Path("/usr/local/etc/xray/config.json")
        if caddy_main_path is None:
            caddy_main_path = Path("/etc/caddy/Caddyfile")
        if caddy_conf_d_path is None:
            caddy_conf_d_path = Path("/etc/caddy/conf.d/xray-auto.caddy")
        
        # Ensure parent directories exist
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_main_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_conf_d_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configs
        xray_path.write_text(self.generate_xray_json())
        caddy_main_path.write_text(self.generate_main_caddyfile())
        caddy_conf_d_path.write_text(self.generate_caddyfile())
        
        return xray_path, caddy_main_path, caddy_conf_d_path


if __name__ == "__main__":
    # Example usage
    gen = ConfigGenerator(
        domains=["proxy1.example.com", "proxy2.example.com"],
        xray_path="/secret-path"
    )
    
    print("=== Xray config.json ===")
    print(gen.generate_xray_json())
    print()
    print("=== Caddyfile ===")
    print(gen.generate_caddyfile())

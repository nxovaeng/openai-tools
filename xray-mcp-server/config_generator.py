"""
Configuration generator for Xray and Caddy.

Generates XHTTP (packet-up mode) configurations for Xray and
corresponding Caddyfile for reverse proxy setup.
"""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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
                        "mode": "packet-up"
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
    
    def to_caddyfile(self) -> str:
        """Generate Caddyfile content."""
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
        
        return "\n".join(blocks)


class ConfigGenerator:
    """Main configuration generator."""
    
    def __init__(
        self,
        domains: list[str],
        xray_port: int = 10000,
        xray_path: str = "/xray",
        client_uuid: Optional[str] = None
    ):
        self.domains = domains
        self.xray_port = xray_port
        self.xray_path = xray_path
        self.client_uuid = client_uuid or str(uuid.uuid4())
        
        self._xray_config = XrayConfig(
            domains=domains,
            uuid=self.client_uuid,
            listen_port=xray_port,
            path=xray_path
        )
        
        self._caddy_config = CaddyConfig(
            domains=domains,
            xray_port=xray_port,
            xray_path=xray_path
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
        """Generate Caddyfile content."""
        return self._caddy_config.to_caddyfile()
    
    def save_configs(
        self,
        xray_path: Path = Path("/usr/local/etc/xray/config.json"),
        caddy_path: Path = Path("/etc/caddy/Caddyfile")
    ) -> tuple[Path, Path]:
        """Save configurations to files."""
        # Ensure parent directories exist
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configs
        xray_path.write_text(self.generate_xray_json())
        caddy_path.write_text(self.generate_caddyfile())
        
        return xray_path, caddy_path


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

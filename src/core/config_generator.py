"""
Xray configuration generator with Nginx reverse proxy.

生成 Xray VLESS+XHTTP 配置，配合 Nginx 反向代理使用。
架构：Client (443) --> Nginx TLS --> Xray (127.0.0.1:port)
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
    生成随机 URL 路径用于混淆
    
    示例: /a7kRmQ2xJ9vN4pL
    """
    chars = string.ascii_letters + string.digits
    random_str = ''.join(secrets.choice(chars) for _ in range(length))
    return f"/{random_str}"


@dataclass
class XrayConfig:
    """Xray 服务器配置"""
    
    domains: list[str]
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    listen_port: int = 10000
    path: str = "/xray"
    
    def to_dict(self) -> dict:
        """生成 Xray config.json 内容"""
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
        """生成 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent)


class ConfigGenerator:
    """配置生成器 - Xray + Nginx"""
    
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
        self.xray_path = xray_path or generate_random_path()
        self.cdn_host = cdn_host
        self.client_uuid = client_uuid or str(uuid.uuid4())
        
        self._xray_config = XrayConfig(
            domains=domains,
            uuid=self.client_uuid,
            listen_port=xray_port,
            path=self.xray_path
        )
    
    @property
    def xray_config(self) -> XrayConfig:
        return self._xray_config
    
    def generate_xray_json(self) -> str:
        """生成 Xray config.json 内容"""
        return self._xray_config.to_json()
    
    def save_xray_config(self, xray_path: Optional[Path] = None) -> Path:
        """保存 Xray 配置到文件
        
        Args:
            xray_path: Xray 配置文件路径（默认自动检测）
        
        Returns:
            配置文件路径
        """
        import os
        
        if xray_path is None:
            is_docker = os.getenv("DEPLOYMENT_MODE") == "container"
            xray_path = Path("/etc/xray/config.json") if is_docker else Path("/usr/local/etc/xray/config.json")
        
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        xray_path.write_text(self.generate_xray_json())
        
        return xray_path


if __name__ == "__main__":
    # 示例用法
    gen = ConfigGenerator(
        domains=["proxy1.example.com", "proxy2.example.com"],
        xray_path="/secret-path"
    )
    
    print("=== Xray config.json ===")
    print(gen.generate_xray_json())

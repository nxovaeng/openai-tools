"""
Subscription link generator.

Generates VLESS subscription links in various formats
for client applications like v2rayN, Clash, etc.
"""

import base64
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote


@dataclass
class VlessNode:
    """VLESS node configuration."""
    
    uuid: str
    domain: str
    port: int = 443
    path: str = "/xray"
    security: str = "tls"
    network: str = "xhttp"
    sni: Optional[str] = None
    
    @property
    def name(self) -> str:
        """Node display name."""
        return self.domain
    
    def to_uri(self) -> str:
        """Generate VLESS URI."""
        # vless://uuid@host:port?params#name
        params = [
            f"type={self.network}",
            f"security={self.security}",
            f"path={quote(self.path, safe='')}",
        ]
        
        if self.sni:
            params.append(f"sni={self.sni}")
        
        param_str = "&".join(params)
        name = quote(self.name, safe='')
        
        return f"vless://{self.uuid}@{self.domain}:{self.port}?{param_str}#{name}"


class SubscriptionGenerator:
    """Generate subscription content."""
    
    def __init__(
        self,
        uuid: str,
        domains: list[str],
        port: int = 443,
        path: str = "/xray"
    ):
        self.uuid = uuid
        self.domains = domains
        self.port = port
        self.path = path
        
        self._nodes = [
            VlessNode(
                uuid=uuid,
                domain=domain,
                port=port,
                path=path
            )
            for domain in domains
        ]
    
    @property
    def nodes(self) -> list[VlessNode]:
        return self._nodes
    
    def generate_uris(self) -> list[str]:
        """Generate list of VLESS URIs."""
        return [node.to_uri() for node in self._nodes]
    
    def generate_base64(self) -> str:
        """Generate Base64 encoded subscription content."""
        uris = self.generate_uris()
        content = "\n".join(uris)
        return base64.b64encode(content.encode()).decode()
    
    def generate_plain(self) -> str:
        """Generate plain text subscription content."""
        return "\n".join(self.generate_uris())


class SubscriptionService:
    """
    Subscription service for dynamic API.
    
    Stores configuration and provides subscription content
    via HTTP API endpoint.
    """
    
    def __init__(self):
        self._generator: Optional[SubscriptionGenerator] = None
    
    def update_config(
        self,
        uuid: str,
        domains: list[str],
        port: int = 443,
        path: str = "/xray"
    ):
        """Update subscription configuration."""
        self._generator = SubscriptionGenerator(
            uuid=uuid,
            domains=domains,
            port=port,
            path=path
        )
    
    def get_subscription(self, format: str = "base64") -> Optional[str]:
        """
        Get subscription content.
        
        Args:
            format: "base64" or "plain"
        
        Returns:
            Subscription content or None if not configured.
        """
        if not self._generator:
            return None
        
        if format == "plain":
            return self._generator.generate_plain()
        return self._generator.generate_base64()
    
    def get_nodes(self) -> list[dict]:
        """Get list of node information."""
        if not self._generator:
            return []
        
        return [
            {
                "name": node.name,
                "domain": node.domain,
                "port": node.port,
                "uri": node.to_uri()
            }
            for node in self._generator.nodes
        ]


# Global subscription service instance
subscription_service = SubscriptionService()


if __name__ == "__main__":
    # Example usage
    gen = SubscriptionGenerator(
        uuid="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        domains=["proxy1.example.com", "proxy2.example.com"],
        path="/secret"
    )
    
    print("=== VLESS URIs ===")
    for uri in gen.generate_uris():
        print(uri)
    
    print("\n=== Base64 Subscription ===")
    print(gen.generate_base64())

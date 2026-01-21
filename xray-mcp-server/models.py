"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


class EnvironmentResponse(BaseModel):
    """Environment check response."""
    distro: str
    is_root: bool
    caddy: dict
    xray: dict


class InstallResponse(BaseModel):
    """Installation response."""
    caddy: Optional[dict] = None
    xray: Optional[dict] = None


class DeployRequest(BaseModel):
    """Deployment request schema."""
    domains: list[str] = Field(..., description="域名列表，例如 ['proxy1.example.com', 'proxy2.example.com']")
    xray_path: Optional[str] = Field(None, description="XHTTP URL 路径，如不指定会自动生成随机路径")
    xray_port: int = Field(10000, description="Xray 本地监听端口")
    cdn_host: Optional[str] = Field(None, description="CDN 反代地址，用于 CNAME 指向")


class DeployResponse(BaseModel):
    """Deployment response schema."""
    success: bool
    uuid: str
    domains: list[str]
    xray_config: dict
    caddyfile: str
    deployment_status: Optional[dict] = None


class SubscriptionRequest(BaseModel):
    """Subscription request schema."""
    format: str = Field("base64", description="订阅格式: 'base64' 或 'plain'")


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""
    format: str
    subscription: str
    nodes: list[dict]


class StatusResponse(BaseModel):
    """Service status response."""
    xray: dict
    caddy: dict


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None

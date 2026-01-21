"""
FastAPI server for Xray + Caddy automated deployment.

This OpenAPI-compatible server provides REST endpoints for:
- Checking environment (Caddy/Xray installation)
- Installing dependencies
- Deploying Xray configurations
- Getting subscription links
"""

from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

from auth import verify_api_key
from config import config

from models import (
    EnvironmentResponse,
    InstallResponse,
    DeployRequest,
    DeployResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    StatusResponse,
    ErrorResponse
)
from installer import Installer
from config_generator import ConfigGenerator
from subscription import subscription_service

# Initialize FastAPI app
app = FastAPI(
    title="Xray Deployment API",
    description="Automated Xray + Caddy deployment with XHTTP protocol support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_current_config: Optional[ConfigGenerator] = None


@app.get("/", summary="Health check")
async def root():
    """Root endpoint - health check."""
    return {"status": "ok", "service": "Xray Deployment API"}


@app.get("/health", summary="Health check")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get(
    "/environment",
    response_model=EnvironmentResponse,
    summary="Check environment"
)
async def check_environment():
    """
    Check installation status of Caddy and Xray.
    
    Returns system information and whether dependencies are installed.
    """
    installer = Installer()
    env_status = installer.check_environment()
    return EnvironmentResponse(**env_status)


@app.post(
    "/install",
    response_model=InstallResponse,
    summary="Install dependencies"
)
async def install_dependencies(api_key: str = Depends(verify_api_key)):
    """
    Install missing Caddy and Xray components.
    
    Requires root privileges. Skips already installed components.
    """
    installer = Installer()
    result = installer.install_missing()
    
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    
    return InstallResponse(**result)


@app.post(
    "/deploy",
    response_model=DeployResponse,
    summary="Deploy Xray + Caddy"
)
async def deploy(
    request: DeployRequest = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    One-click deployment: generate configs and deploy.
    
    This endpoint:
    1. Generates Xray config.json with XHTTP protocol
    2. Generates Caddyfile for reverse proxy
    3. Optionally deploys to system paths and restarts services
    
    Returns generated configurations and deployment status.
    """
    global _current_config
    
    if not request.domains:
        raise HTTPException(status_code=400, detail="At least one domain is required")
    
    # Generate configurations
    _current_config = ConfigGenerator(
        domains=request.domains,
        xray_port=request.xray_port,
        xray_path=request.xray_path
    )
    
    # Update subscription service
    subscription_service.update_config(
        uuid=_current_config.client_uuid,
        domains=request.domains,
        path=request.xray_path,
        port=443
    )
    
    # Try to deploy (may fail if not root)
    deployment_status = None
    try:
        import subprocess
        from pathlib import Path
        
        # Save configs
        xray_path = Path("/usr/local/etc/xray/config.json")
        
        # Use snippet file to avoid overwriting existing Caddyfile
        caddy_snippet_dir = Path("/etc/caddy/conf.d")
        caddy_snippet_path = caddy_snippet_dir / "xray-auto.caddy"
        caddy_main_path = Path("/etc/caddy/Caddyfile")
        
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_snippet_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Xray config
        xray_path.write_text(_current_config.generate_xray_json())
        
        # Save Caddy snippet (won't overwrite main Caddyfile)
        caddy_snippet_path.write_text(_current_config.generate_caddyfile())
        
        # Check if main Caddyfile has import directive
        import_line = f"import {caddy_snippet_dir}/*.caddy"
        if caddy_main_path.exists():
            caddy_content = caddy_main_path.read_text()
            if import_line not in caddy_content:
                # Add import directive at the beginning
                new_content = f"{import_line}\n\n{caddy_content}"
                caddy_main_path.write_text(new_content)
        
        # Restart services
        xray_restart = subprocess.run(
            ["systemctl", "restart", "xray"],
            capture_output=True,
            text=True
        )
        caddy_reload = subprocess.run(
            ["systemctl", "reload", "caddy"],
            capture_output=True,
            text=True
        )
        
        deployment_status = {
            "xray": {
                "config_saved": str(xray_path),
                "restart_success": xray_restart.returncode == 0
            },
            "caddy": {
                "snippet_saved": str(caddy_snippet_path),
                "main_caddyfile": str(caddy_main_path),
                "reload_success": caddy_reload.returncode == 0,
                "note": "Xray config saved to snippet file, existing Caddyfile preserved"
            }
        }
    except Exception as e:
        deployment_status = {"error": str(e), "note": "Configs generated but not deployed (requires root)"}
    
    return DeployResponse(
        success=True,
        uuid=_current_config.client_uuid,
        domains=request.domains,
        xray_config=_current_config.xray_config.to_dict(),
        caddyfile=_current_config.generate_caddyfile(),
        deployment_status=deployment_status
    )


@app.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get subscription link"
)
async def get_subscription(format: str = "base64"):
    """
    Get VLESS subscription link.
    
    Supports two formats:
    - base64: Base64 encoded subscription (compatible with v2rayN/v2rayNG)
    - plain: Plain text VLESS URIs
    """
    content = subscription_service.get_subscription(format)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="No configuration generated. Call /deploy first."
        )
    
    nodes = subscription_service.get_nodes()
    
    return SubscriptionResponse(
        format=format,
        subscription=content,
        nodes=nodes
    )


@app.get(
    "/status",
    response_model=StatusResponse,
    summary="Get service status"
)
async def get_status(api_key: str = Depends(verify_api_key)):
    """
    Get current status of Xray and Caddy services.
    """
    import subprocess
    
    status = {}
    
    for service in ["xray", "caddy"]:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                timeout=5
            )
            status[service] = {
                "active": result.stdout.strip() == "active",
                "status": result.stdout.strip()
            }
        except Exception as e:
            status[service] = {
                "active": False,
                "status": "unknown",
                "error": str(e)
            }
    
    return StatusResponse(**status)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

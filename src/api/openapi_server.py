"""
FastAPI server for Xray + Nginx automated deployment.

OpenAPI-compatible server for Open WebUI integration.
Provides REST endpoints for:
- Nginx configuration management
- Xray service deployment
- SSL certificate management
- Service status monitoring
"""

import os
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

from src.api.auth import verify_api_key
from src.api.config import config

from src.models.models import (
    EnvironmentResponse,
    InstallResponse,
    DeployRequest,
    DeployResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    StatusResponse,
    ErrorResponse
)
from src.core.installer import Installer
from src.core.config_generator import ConfigGenerator
from src.core.nginx_generator import NginxServiceManager
from src.core.subscription import subscription_service

# Initialize FastAPI app with OpenAPI docs enabled
app = FastAPI(
    title="Xray + Nginx Deployment API",
    description="""
    OpenAPI Tool Server for automated Xray + Nginx deployment.
    
    Compatible with Open WebUI and other OpenAPI-based AI platforms.
    
    Features:
    - Nginx reverse proxy configuration
    - Xray VLESS+XHTTP service deployment
    - SSL certificate management
    - Multi-domain support
    - Service monitoring
    """,
    version="2.0.0",
    docs_url="/docs",  # OpenAPI documentation
    redoc_url="/redoc",  # Alternative documentation
    openapi_url="/openapi.json"  # OpenAPI schema
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
_service_manager = NginxServiceManager()


@app.get("/", summary="API Information")
async def root():
    """
    Root endpoint - API information and health check.
    
    Returns basic information about the API and available endpoints.
    """
    return {
        "name": "Xray + Nginx Deployment API",
        "version": "2.0.0",
        "status": "operational",
        "description": "OpenAPI Tool Server for automated Xray + Nginx deployment",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "endpoints": {
            "nginx": {
                "add_xray_service": "POST /nginx/xray",
                "add_web_service": "POST /nginx/web",
                "list_services": "GET /nginx/services",
                "remove_service": "DELETE /nginx/services/{config_name}",
                "test_config": "GET /nginx/test",
                "reload": "POST /nginx/reload"
            },
            "subscription": "GET /subscription",
            "status": "GET /status"
        }
    }


@app.get("/health", summary="Health check")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "xray-nginx-api"}


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
async def install_dependencies(
    api_key: str = Depends(verify_api_key) if os.getenv("REQUIRE_AUTH", "true").lower() == "true" else None
):
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
        xray_path=request.xray_path,
        cdn_host=request.cdn_host
    )
    
    # Update subscription service - CDN host for subscription output
    subscription_service.update_config(
        uuid=_current_config.client_uuid,
        domains=request.domains,
        path=_current_config.xray_path,
        port=443,
        cdn_host=request.cdn_host
    )
    
    # Try to deploy (may fail if not root or in Docker)
    deployment_status = None
    
    # Check deployment mode (for Docker containers)
    import os
    from pathlib import Path
    deployment_mode = os.getenv("DEPLOYMENT_MODE", "full")
    
    if deployment_mode == "config_only":
        # Docker mode: only generate configs, don't deploy
        config_dir = Path("/app/generated_configs")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        (config_dir / "xray-config.json").write_text(_current_config.generate_xray_json())
        (config_dir / "Caddyfile").write_text(_current_config.generate_main_caddyfile())
        (config_dir / "xray-auto.caddy").write_text(_current_config.generate_caddyfile())
        
        deployment_status = {
            "mode": "config_only",
            "note": "Configs generated in /app/generated_configs. Deploy manually or use host-mode.",
            "xray_config": str(config_dir / "xray-config.json"),
            "caddy_main": str(config_dir / "Caddyfile"),
            "caddy_xray_auto": str(config_dir / "xray-auto.caddy")
        }

    elif deployment_mode == "container":
        # All-in-one container mode: deploy and restart via supervisord
        import subprocess
        
        # Use environment-specified paths or defaults
        xray_path = Path(os.getenv("XRAY_CONFIG_PATH", "/app/data/xray/config.json"))
        caddy_main_path = Path(os.getenv("CADDY_CONFIG_PATH", "/app/data/caddy/Caddyfile"))
        caddy_conf_d_path = Path(os.getenv("CADDY_CONF_D_PATH", "/app/data/caddy/conf.d/xray-auto.caddy"))
        
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_main_path.parent.mkdir(parents=True, exist_ok=True)
        caddy_conf_d_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configs with proper structure
        xray_path.write_text(_current_config.generate_xray_json())
        caddy_main_path.write_text(_current_config.generate_main_caddyfile())
        caddy_conf_d_path.write_text(_current_config.generate_caddyfile())
        
        # Restart services via supervisorctl
        xray_restart = subprocess.run(
            ["supervisorctl", "restart", "xray"],
            capture_output=True,
            text=True
        )
        caddy_restart = subprocess.run(
            ["supervisorctl", "restart", "caddy"],
            capture_output=True,
            text=True
        )
        
        deployment_status = {
            "mode": "container",
            "xray": {
                "config_saved": str(xray_path),
                "restart_success": xray_restart.returncode == 0,
                "message": xray_restart.stdout if xray_restart.returncode == 0 else xray_restart.stderr
            },
            "caddy": {
                "main_config": str(caddy_main_path),
                "xray_auto_config": str(caddy_conf_d_path),
                "restart_success": caddy_restart.returncode == 0,
                "message": caddy_restart.stdout if caddy_restart.returncode == 0 else caddy_restart.stderr
            },
            "note": "Services managed by supervisord in container"
        }
    else:
        # Host mode: actually deploy to system
        pass
    
    try:
        import subprocess
        from pathlib import Path
        
        # Save configs with environment-aware paths
        deployment_mode = os.getenv("DEPLOYMENT_MODE", "full")
        is_docker = deployment_mode == "container"
        
        xray_path = Path("/etc/xray/config.json") if is_docker else Path("/usr/local/etc/xray/config.json")
        
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
    summary="Get subscription link",
    description="Get VLESS subscription link for Xray clients",
    tags=["Subscription"]
)
async def get_subscription(
    format: str = "base64",
    domain: Optional[str] = None
):
    """
    Get VLESS subscription link compatible with v2rayN, v2rayNG, Shadowrocket, etc.
    
    Args:
        format: Output format - "base64" (default) or "plain"
        domain: Filter by specific domain (optional)
    
    Returns:
        Subscription content and node list
    """
    content = subscription_service.get_subscription(format)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="No Xray service configured. Use POST /nginx/xray to add a service first."
        )
    
    nodes = subscription_service.get_nodes()
    
    if domain:
        nodes = [n for n in nodes if n.get("domain") == domain]
    
    return SubscriptionResponse(
        format=format,
        subscription=content,
        nodes=nodes
    )


@app.get(
    "/status",
    response_model=StatusResponse,
    summary="Get service status",
    description="Check status of Nginx and Xray services",
    tags=["Monitoring"]
)
async def get_status(api_key: str = Depends(verify_api_key)):
    """
    Get current status of Nginx and Xray services.
    
    Returns whether services are active and running.
    """
    import subprocess
    
    status = {}
    
    for service in ["nginx", "xray"]:
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


# ============================================================================
# Nginx Configuration Endpoints
# ============================================================================

@app.post(
    "/nginx/xray",
    summary="Add Xray Service",
    description="Deploy a new Xray VLESS+XHTTP service with Nginx reverse proxy",
    tags=["Nginx Configuration"]
)
async def add_xray_service(
    domain: str = Body(..., description="Domain name (e.g., proxy.example.com)"),
    xray_port: int = Body(10000, description="Xray listening port"),
    xray_path: Optional[str] = Body(None, description="XHTTP path (auto-generated if not specified)"),
    cdn_host: Optional[str] = Body(None, description="CDN domain for reverse proxy"),
    ssl_cert_path: Optional[str] = Body(None, description="Custom SSL certificate path"),
    ssl_key_path: Optional[str] = Body(None, description="Custom SSL key path"),
    api_key: str = Depends(verify_api_key)
):
    """
    Add a new Xray VLESS+XHTTP service with Nginx configuration.
    
    This endpoint:
    1. Generates Xray configuration with VLESS protocol
    2. Creates Nginx reverse proxy configuration
    3. Sets up SSL/TLS termination
    4. Generates subscription link
    """
    try:
        # Generate Xray configuration
        xray_gen = ConfigGenerator(
            domains=[domain],
            xray_port=xray_port,
            xray_path=xray_path,
            cdn_host=cdn_host
        )
        
        # Save Xray config
        xray_config_path = xray_gen.save_xray_config()
        
        # Generate Nginx config
        nginx_config_path = _service_manager.add_xray_service(
            domain=domain,
            xray_port=xray_port,
            xray_path=xray_gen.xray_path,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path
        )
        
        # Update subscription
        subscription_service.update_config(
            uuid=xray_gen.client_uuid,
            domains=[domain],
            path=xray_gen.xray_path,
            cdn_host=cdn_host
        )
        
        return {
            "success": True,
            "service_type": "xray",
            "domain": domain,
            "xray_port": xray_port,
            "xray_path": xray_gen.xray_path,
            "uuid": xray_gen.client_uuid,
            "cdn_host": cdn_host,
            "xray_config_path": str(xray_config_path),
            "nginx_config_path": str(nginx_config_path),
            "next_steps": [
                f"Apply SSL certificate: certbot --nginx -d {domain}",
                "Test configuration: nginx -t",
                "Reload Nginx: nginx -s reload",
                "Start Xray: systemctl start xray"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/nginx/web",
    summary="Add Web Service",
    description="Add a generic web service or API with Nginx reverse proxy",
    tags=["Nginx Configuration"]
)
async def add_web_service(
    domain: str = Body(..., description="Domain name"),
    backend_port: int = Body(..., description="Backend service port"),
    service_name: str = Body(..., description="Service name"),
    enable_websocket: bool = Body(False, description="Enable WebSocket support"),
    enable_gzip: bool = Body(True, description="Enable Gzip compression"),
    client_max_body_size: str = Body("50M", description="Maximum request body size"),
    ssl_cert_path: Optional[str] = Body(None, description="Custom SSL certificate path"),
    ssl_key_path: Optional[str] = Body(None, description="Custom SSL key path"),
    api_key: str = Depends(verify_api_key)
):
    """
    Add a generic web service, API, or application with Nginx reverse proxy.
    
    Supports:
    - REST APIs
    - Web applications
    - WebSocket services
    - Admin panels
    """
    try:
        extra_config = []
        
        if enable_websocket:
            extra_config.append("""
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";""")
        
        if enable_gzip:
            extra_config.append("""
        # Gzip compression
        gzip on;
        gzip_types text/plain application/json application/javascript text/css;""")
        
        if client_max_body_size:
            extra_config.append(f"""
        # Maximum request body size
        client_max_body_size {client_max_body_size};""")
        
        nginx_config_path = _service_manager.add_generic_service(
            domain=domain,
            backend_port=backend_port,
            service_name=service_name,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
            extra_config="\n".join(extra_config)
        )
        
        return {
            "success": True,
            "service_type": "web",
            "domain": domain,
            "backend_port": backend_port,
            "service_name": service_name,
            "features": {
                "websocket": enable_websocket,
                "gzip": enable_gzip,
                "max_body_size": client_max_body_size
            },
            "nginx_config_path": str(nginx_config_path),
            "next_steps": [
                f"Apply SSL certificate: certbot --nginx -d {domain}",
                "Test configuration: nginx -t",
                "Reload Nginx: nginx -s reload",
                f"Ensure backend service is running on 127.0.0.1:{backend_port}"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/nginx/services",
    summary="List Services",
    description="List all configured Nginx services",
    tags=["Nginx Configuration"]
)
async def list_services(api_key: str = Depends(verify_api_key)):
    """
    List all configured Nginx services.
    
    Returns a list of all service configuration files in /etc/nginx/conf.d/
    """
    try:
        services = _service_manager.list_services()
        return {
            "success": True,
            "total": len(services),
            "services": services,
            "config_directory": str(_service_manager.conf_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/nginx/services/{config_name}",
    summary="Remove Service",
    description="Remove a service configuration",
    tags=["Nginx Configuration"]
)
async def remove_service(
    config_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Remove a service configuration file.
    
    Args:
        config_name: Configuration filename (e.g., "xray-proxy-example-com.conf")
    """
    try:
        success = _service_manager.remove_service(config_name)
        
        if success:
            return {
                "success": True,
                "message": f"Configuration {config_name} removed",
                "next_steps": [
                    "Test configuration: nginx -t",
                    "Reload Nginx: nginx -s reload"
                ]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Configuration {config_name} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/nginx/test",
    summary="Test Configuration",
    description="Test Nginx configuration syntax",
    tags=["Nginx Configuration"]
)
async def test_nginx_config(api_key: str = Depends(verify_api_key)):
    """
    Test Nginx configuration syntax without applying changes.
    """
    import subprocess
    
    try:
        result = subprocess.run(
            ["nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stderr,
            "message": "Configuration is valid" if result.returncode == 0 else "Configuration has errors"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/nginx/reload",
    summary="Reload Nginx",
    description="Reload Nginx configuration without downtime",
    tags=["Nginx Configuration"]
)
async def reload_nginx(api_key: str = Depends(verify_api_key)):
    """
    Reload Nginx configuration gracefully without interrupting active connections.
    
    Automatically tests configuration before reloading.
    """
    import subprocess
    
    try:
        # Test configuration first
        test_result = subprocess.run(
            ["nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        if test_result.returncode != 0:
            return {
                "success": False,
                "error": "Configuration test failed, reload aborted",
                "test_output": test_result.stderr
            }
        
        # Reload configuration
        reload_result = subprocess.run(
            ["nginx", "-s", "reload"],
            capture_output=True,
            text=True
        )
        
        return {
            "success": reload_result.returncode == 0,
            "message": "Nginx reloaded successfully" if reload_result.returncode == 0 else "Reload failed",
            "output": reload_result.stderr if reload_result.returncode != 0 else "OK"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Load environment variables from config/.env
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent / "config" / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)

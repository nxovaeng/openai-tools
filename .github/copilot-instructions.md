# Xray Deployment MCP Server - Copilot Instructions

## Project Overview

**Purpose**: MCP tool server for automated Xray + Caddy deployment with XHTTP protocol support. Integrates with AI platforms (Open WebUI, Dify) for natural language deployment control.

**Architecture**: 
- `main.py` - FastAPI REST API (optional, for direct HTTP access)
- `server.py` - FastMCP tool server (primary interface for AI integration)
- `config_generator.py` - Generates Xray (VLESS/XHTTP packet-up) and Caddy configurations with SNI/CDN support
- `installer.py` - Cross-distro package detection and installation (Debian/RHEL/Arch)
- `auth.py` - API key authentication (X-API-Key header or Bearer token)

**Data Flow**: Request → Pydantic validation → Config generation → File output/CLI commands → Subscription link generation

## Key Patterns & Conventions

### Configuration Management
- **API Key**: Auto-generated on first run, stored in `.env` file
- **Random Path Generation**: `xray_path` auto-generates random obfuscated paths if not provided (e.g., `/a7kRmQ2xJ9vN4pL`)
- **SNI Auto-Configuration**: SNI automatically set to first domain - no user input needed
- **State Management**: Global `_current_config` in `server.py` tracks generated configs for subscription access
- **Subscription Service**: `subscription.py` maintains UUID → domains mapping
- **Pydantic Models** in `models.py`: DeployRequest/DeployResponse with auto-generated paths

### SNI and CDN Support
- **SNI**: Each domain has its own SNI (domain itself) for Caddy routing
- **CDN Host**: Optional CDN reverse proxy address used in subscription output
- **Multi-Domain Nodes**: Multiple domains generate multiple VLESS nodes
- **Domain vs CDN**: Domain for Caddy routing/SNI, CDN host for subscription URI
- Subscription example: `vless://uuid@cdn.example.com:443?...&sni=proxy.example.com`
  - Client connects to `cdn.example.com`
  - SNI sends `proxy.example.com` for Caddy routing

### Caddy Configuration Modularization
- **Main Caddyfile**: Stores global config and `import` directive
  - Path: `/etc/caddy/Caddyfile` (main config file)
  - Content: `import /etc/caddy/conf.d/*.caddy`
  - User can manually add other service proxies here
- **Auto-Generated Config**: Xray-specific reverse proxy rules
  - Path: `/etc/caddy/conf.d/xray-auto.caddy` (auto-generated)
  - Content: Domain blocks with XHTTP path matching and reverse proxy
  - Automatically included by main Caddyfile import directive
- **Benefits**:
  - Prevents overwriting user-configured services
  - Supports multi-service deployments (Open WebUI, etc.)
  - Easy to extend without modifying auto-generated sections

### Docker Network Architecture
- **Host Network Mode**: Docker container uses `network_mode: host`
  - Eliminates port mapping complexity
  - Container ports directly accessible from host
  - Enables easy integration with other services
  - Reduces NAT overhead
- **Volume Mounts**:
  - `caddy_conf_d`: Maps `/etc/caddy/conf.d` for auto-generated configs
  - `xray_data`: Maps `/etc/xray` for Xray configuration
  - `.env`: API key persistence
- **Service Integration Example**:
  ```
  Host network allows containers and host services to coexist:
  - Xray container: 127.0.0.1:10000
  - Open WebUI: 127.0.0.1:8111
  - Caddy container: 127.0.0.1:80/443
  ```

### Installation Workflow
Cross-distro support pattern:
1. Detect distro family via `/etc/os-release`
2. Route to appropriate package manager (apt/dnf/pacman)
3. Check if root; gracefully skip already-installed components
4. Return status as dataclass → dict for serialization

## Developer Workflows

### Running & Testing
```bash
# MCP Server (AI integration - recommended)
./start.sh          # Auto venv + MCP server

# Manual MCP server
source venv/bin/activate
pip install -r requirements.txt
python server.py    # Starts MCP tool server

# REST API (optional, requires authentication)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment
- **All-in-One**: `docker-compose.allinone.yaml` - Complete stack with supervisord process management
- Only recommended deployment method alongside systemd services

### MCP Tools Available
- `check_environment()` - Check Caddy/Xray installation
- `install_dependencies()` - Auto-install missing packages
- `generate_configs(domains, xray_port, xray_path, cdn_host)` - Generate configurations
  - domains: List of domain names (each with own SNI)
  - xray_port: Optional, default 10000
  - xray_path: Optional, auto-generates random path if not provided (returns actual value)
  - cdn_host: Optional CDN host for subscription output
  - Returns: UUID, domains, xray_path (actual generated), cdn_host, configs dict, caddyfile string
- `deploy_configs()` - Deploy to system paths with 3-file structure
  - Creates: `/etc/xray/config.json`, `/etc/caddy/Caddyfile`, `/etc/caddy/conf.d/xray-auto.caddy`
- `get_subscription(format)` - Return subscription links (v2ray or clash format)
- `restart_services()` - Restart Xray/Caddy via supervisorctl

### Adding Features
1. Add Pydantic model to `models.py` with new request/response fields
2. Implement logic in business module (e.g., `config_generator.py`)
3. Add MCP tool in `server.py` (primary interface)
4. Optionally add FastAPI route in `main.py` for REST access
5. Update `requirements.txt` for new dependencies

## Integration Points & Dependencies

- **FastMCP**: MCP server protocol bindings (primary interface)
- **FastAPI + Uvicorn**: Optional REST API (for direct HTTP access)
- **Pydantic v2+**: Request/response validation (strict mode assumed)
- **External Tools**: Requires `caddy`, `xray` binaries in PATH or installed via installer
- **Configuration Files**: Outputs to `configs/` dir or system paths (`/etc/xray/`, `/etc/caddy/`)

## Critical Patterns

### XHTTP Protocol (Packet-Up Mode)
Xray config template in `XrayConfig.to_dict()`:
```json
{
  "inbounds": [{
    "protocol": "vless",
    "streamSettings": {
      "network": "xhttp",
      "xhttpSettings": {"path": "/a7kRmQ2xJ9vN4pL", "mode": "packet-up"}
    }
  }]
}
```
- Inbound: VLESS + XHTTP transport with packet-up mode
- Outbound: Freedom protocol for direct proxy
- **Path**: Auto-generated random path for obfuscation via `generate_random_path()`
- Client identified by UUID (stored in subscription service)
- Configuration follows [Xray official documentation](https://xtls.github.io/)

### SNI and CDN Configuration
- **SNI**: Each domain has its own SNI (domain itself), no unified SNI
  - Each domain in the list gets individual SNI for TLS handshake
  - Example: domain "proxy1.example.com" has SNI = "proxy1.example.com"
- **CDN Host**: Optional, used only in subscription output as connection address
  - Replaces domain in subscription URI for client connection
  - Client connects to CDN host, but SNI still identifies original domain
  - Example subscription: `vless://uuid@cdn.example.com:443?...&sni=proxy1.example.com`
- **Caddy Routing**: Main config includes auto-generated xray-auto.caddy via `import` directive
  - Each domain block contains XHTTP path matching rules
  - SNI determines which domain block handles the connection
- **Subscription URIs**: Automatically include both CDN host (for connection) and SNI (for routing)

### Secure Defaults
- API key verification on protected endpoints (check `REQUIRE_AUTH` env var)
- Support both X-API-Key header and Bearer token authentication
- Distro detection prevents unsupported system installation attempts
- FastAPI docs disabled for security (no `/docs` or `/redoc` endpoints)

### State Persistence
- `subscription_service.update_config()` called after config generation with SNI
- Global state in `server.py` enables subscription link retrieval without re-generation
- `.env` file for persistent API key across restarts


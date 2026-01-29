"""
MCP Server for Nginx Configuration Management.

通过自然语言交互来生成和管理 Nginx 反向代理配置。
支持 Xray、API、Web 应用等各种服务的配置生成。

Merged from legacy MCP server to provide unified interface.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Literal

from fastmcp import FastMCP

from src.core.config_generator import ConfigGenerator
from src.core.nginx_generator import (
    NginxServiceManager,
    generate_xray_config,
    generate_service_config,
    generate_main_nginx_conf
)
from src.core.subscription import subscription_service
from src.core.installer import Installer

# 初始化 MCP 服务器
mcp = FastMCP(
    name="nginx-config-manager",
    instructions="""
    Nginx 配置管理 MCP 服务器
    
    功能：
    - 通过自然语言生成 Nginx 反向代理配置
    - 支持 Xray VLESS+XHTTP 服务配置
    - 支持通用 Web 服务、API 服务配置
    - 自动管理 SSL 证书
    - 服务配置的增删改查
    - 系统环境检查和依赖安装
    
    架构：Client (443) --> Nginx (TLS) --> Backend (127.0.0.1:port)
    """
)

# 全局状态
_service_manager = NginxServiceManager()
_current_xray_configs: dict[str, ConfigGenerator] = {}
_installer = Installer()


@mcp.tool()
def add_xray_service(
    domain: str,
    xray_port: int = 10000,
    xray_path: Optional[str] = None,
    cdn_host: Optional[str] = None,
    ssl_cert_path: Optional[str] = None,
    ssl_key_path: Optional[str] = None
) -> dict:
    """
    添加 Xray VLESS+XHTTP 服务配置
    
    自然语言示例：
    - "为 proxy.example.com 添加 Xray 服务，端口 10000"
    - "部署一个代理服务到 proxy1.example.com"
    - "创建 Xray 配置，域名 vpn.example.com，使用 CDN cdn.example.com"
    
    Args:
        domain: 域名（如 proxy.example.com）
        xray_port: Xray 监听端口（默认 10000）
        xray_path: XHTTP 路径（不指定则自动生成随机路径）
        cdn_host: CDN 域名（用于 CDN 反代场景）
        ssl_cert_path: SSL 证书路径（可选，默认使用 Let's Encrypt）
        ssl_key_path: SSL 私钥路径（可选）
    
    Returns:
        配置信息，包括 UUID、路径、配置文件位置等
    """
    try:
        # 生成 Xray 配置
        xray_gen = ConfigGenerator(
            domains=[domain],
            xray_port=xray_port,
            xray_path=xray_path,
            cdn_host=cdn_host
        )
        
        # 保存 Xray 配置
        xray_config_path = xray_gen.save_xray_config()
        
        # 生成 Nginx 配置
        nginx_config_path = _service_manager.add_xray_service(
            domain=domain,
            xray_port=xray_port,
            xray_path=xray_gen.xray_path,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path
        )
        
        # 保存配置引用
        _current_xray_configs[domain] = xray_gen
        
        # 更新订阅服务
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
                f"申请 SSL 证书: certbot --nginx -d {domain}",
                "测试配置: nginx -t",
                "重载 Nginx: nginx -s reload",
                "启动 Xray: systemctl start xray"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def add_web_service(
    domain: str,
    backend_port: int,
    service_name: str,
    service_type: Literal["api", "web", "admin", "custom"] = "web",
    enable_websocket: bool = False,
    enable_gzip: bool = True,
    client_max_body_size: str = "50M",
    ssl_cert_path: Optional[str] = None,
    ssl_key_path: Optional[str] = None
) -> dict:
    """
    添加通用 Web 服务配置（API、Web 应用、管理面板等）
    
    自然语言示例：
    - "为 api.example.com 添加 API 服务，后端端口 3000"
    - "部署 Web 应用到 app.example.com，端口 8080"
    - "创建管理面板配置，域名 admin.example.com，端口 9000"
    - "添加支持 WebSocket 的服务到 ws.example.com，端口 5000"
    
    Args:
        domain: 域名（如 api.example.com）
        backend_port: 后端服务端口（如 3000）
        service_name: 服务名称（如 "API Service"）
        service_type: 服务类型（api/web/admin/custom）
        enable_websocket: 是否启用 WebSocket 支持
        enable_gzip: 是否启用 Gzip 压缩
        client_max_body_size: 最大请求体大小（如 "50M"）
        ssl_cert_path: SSL 证书路径（可选）
        ssl_key_path: SSL 私钥路径（可选）
    
    Returns:
        配置信息和后续步骤
    """
    try:
        # 构建额外配置
        extra_config = []
        
        if enable_websocket:
            extra_config.append("""
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";""")
        
        if enable_gzip:
            extra_config.append("""
        # Gzip 压缩
        gzip on;
        gzip_types text/plain application/json application/javascript text/css;""")
        
        if client_max_body_size:
            extra_config.append(f"""
        # 最大请求体大小
        client_max_body_size {client_max_body_size};""")
        
        extra_config_str = "\n".join(extra_config)
        
        # 生成 Nginx 配置
        nginx_config_path = _service_manager.add_generic_service(
            domain=domain,
            backend_port=backend_port,
            service_name=service_name,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
            extra_config=extra_config_str
        )
        
        return {
            "success": True,
            "service_type": service_type,
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
                f"申请 SSL 证书: certbot --nginx -d {domain}",
                "测试配置: nginx -t",
                "重载 Nginx: nginx -s reload",
                f"确保后端服务运行在 127.0.0.1:{backend_port}"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def add_static_site(
    domain: str,
    root_path: str,
    index_files: list[str] = None,
    enable_directory_listing: bool = False,
    ssl_cert_path: Optional[str] = None,
    ssl_key_path: Optional[str] = None
) -> dict:
    """
    添加静态网站配置
    
    自然语言示例：
    - "为 blog.example.com 添加静态网站，根目录 /var/www/blog"
    - "部署静态文件到 static.example.com，路径 /var/www/static"
    
    Args:
        domain: 域名
        root_path: 网站根目录路径
        index_files: 索引文件列表（默认 ["index.html", "index.htm"]）
        enable_directory_listing: 是否启用目录列表
        ssl_cert_path: SSL 证书路径（可选）
        ssl_key_path: SSL 私钥路径（可选）
    
    Returns:
        配置信息
    """
    if index_files is None:
        index_files = ["index.html", "index.htm"]
    
    try:
        # 构建静态站点配置
        index_str = " ".join(index_files)
        extra_config = f"""
        root {root_path};
        index {index_str};
        
        # 静态文件缓存
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {{
            expires 30d;
            add_header Cache-Control "public, immutable";
        }}"""
        
        if enable_directory_listing:
            extra_config += "\n        autoindex on;"
        
        nginx_config_path = _service_manager.add_generic_service(
            domain=domain,
            backend_port=0,  # 静态站点不需要后端端口
            service_name=f"Static Site - {domain}",
            location_path="/",
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
            extra_config=extra_config
        )
        
        # 手动修改配置移除 proxy_pass
        config_content = nginx_config_path.read_text()
        config_content = config_content.replace(
            "proxy_pass http://127.0.0.1:0;",
            "# Static site - no proxy needed"
        )
        nginx_config_path.write_text(config_content)
        
        return {
            "success": True,
            "service_type": "static",
            "domain": domain,
            "root_path": root_path,
            "index_files": index_files,
            "directory_listing": enable_directory_listing,
            "nginx_config_path": str(nginx_config_path),
            "next_steps": [
                f"确保目录存在: mkdir -p {root_path}",
                f"申请 SSL 证书: certbot --nginx -d {domain}",
                "测试配置: nginx -t",
                "重载 Nginx: nginx -s reload"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def list_services() -> dict:
    """
    列出所有已配置的服务
    
    自然语言示例：
    - "列出所有服务"
    - "显示当前配置"
    - "有哪些服务在运行"
    
    Returns:
        所有服务配置文件列表
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
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def remove_service(config_filename: str) -> dict:
    """
    删除服务配置
    
    自然语言示例：
    - "删除 proxy.example.com 的配置"
    - "移除 api-service-api-example-com.conf"
    
    Args:
        config_filename: 配置文件名（如 "xray-proxy-example-com.conf"）
    
    Returns:
        删除结果
    """
    try:
        success = _service_manager.remove_service(config_filename)
        
        if success:
            return {
                "success": True,
                "message": f"配置文件 {config_filename} 已删除",
                "next_steps": [
                    "测试配置: nginx -t",
                    "重载 Nginx: nginx -s reload"
                ]
            }
        else:
            return {
                "success": False,
                "error": f"配置文件 {config_filename} 不存在"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_subscription(domain: Optional[str] = None, format: str = "base64") -> dict:
    """
    获取 Xray 订阅链接
    
    自然语言示例：
    - "获取订阅链接"
    - "生成 proxy.example.com 的订阅"
    - "显示所有节点"
    
    Args:
        domain: 指定域名（可选，不指定则返回所有）
        format: 格式（"base64" 或 "plain"）
    
    Returns:
        订阅内容和节点列表
    """
    try:
        content = subscription_service.get_subscription(format)
        nodes = subscription_service.get_nodes()
        
        if domain:
            nodes = [n for n in nodes if n.get("domain") == domain]
        
        if not content and not nodes:
            return {
                "success": False,
                "error": "没有配置的 Xray 服务，请先使用 add_xray_service 添加"
            }
        
        return {
            "success": True,
            "format": format,
            "subscription": content,
            "nodes": nodes,
            "total_nodes": len(nodes)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def test_nginx_config() -> dict:
    """
    测试 Nginx 配置语法
    
    自然语言示例：
    - "测试配置"
    - "检查 Nginx 配置是否正确"
    - "验证配置文件"
    
    Returns:
        测试结果
    """
    try:
        result = subprocess.run(
            ["nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stderr,  # nginx -t 输出到 stderr
            "message": "配置正确" if result.returncode == 0 else "配置有误"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def reload_nginx() -> dict:
    """
    重载 Nginx 配置（不中断服务）
    
    自然语言示例：
    - "重载 Nginx"
    - "应用新配置"
    - "刷新 Nginx"
    
    Returns:
        重载结果
    """
    try:
        # 先测试配置
        test_result = subprocess.run(
            ["nginx", "-t"],
            capture_output=True,
            text=True
        )
        
        if test_result.returncode != 0:
            return {
                "success": False,
                "error": "配置测试失败，未执行重载",
                "test_output": test_result.stderr
            }
        
        # 重载配置
        reload_result = subprocess.run(
            ["nginx", "-s", "reload"],
            capture_output=True,
            text=True
        )
        
        return {
            "success": reload_result.returncode == 0,
            "message": "Nginx 已重载" if reload_result.returncode == 0 else "重载失败",
            "output": reload_result.stderr if reload_result.returncode != 0 else "OK"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_service_status() -> dict:
    """
    获取服务状态
    
    自然语言示例：
    - "查看服务状态"
    - "Nginx 运行正常吗"
    - "检查 Xray 状态"
    
    Returns:
        Nginx 和 Xray 服务状态
    """
    status = {}
    
    for service in ["nginx", "xray"]:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True
            )
            
            status[service] = {
                "active": result.stdout.strip() == "active",
                "status": result.stdout.strip()
            }
            
        except Exception as e:
            status[service] = {
                "active": False,
                "error": str(e)
            }
    
    return {
        "success": True,
        "services": status,
        "all_active": all(s.get("active", False) for s in status.values())
    }


@mcp.tool()
def request_ssl_certificate(domain: str, email: Optional[str] = None) -> dict:
    """
    申请 SSL 证书（使用 Certbot）
    
    自然语言示例：
    - "为 proxy.example.com 申请证书"
    - "获取 SSL 证书，域名 api.example.com"
    
    Args:
        domain: 域名
        email: 邮箱地址（可选，用于证书通知）
    
    Returns:
        申请结果
    """
    try:
        cmd = ["certbot", "--nginx", "-d", domain, "--non-interactive", "--agree-tos"]
        
        if email:
            cmd.extend(["--email", email])
        else:
            cmd.append("--register-unsafely-without-email")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "domain": domain,
            "message": "证书申请成功" if result.returncode == 0 else "证书申请失败",
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 资源：当前配置
@mcp.resource("config://services")
def get_all_services() -> str:
    """获取所有服务配置的 JSON 表示"""
    services = _service_manager.list_services()
    
    return json.dumps({
        "total": len(services),
        "services": services,
        "config_directory": str(_service_manager.conf_dir)
    }, indent=2)


@mcp.resource("config://xray")
def get_xray_configs() -> str:
    """获取所有 Xray 配置的 JSON 表示"""
    configs = {}
    
    for domain, gen in _current_xray_configs.items():
        configs[domain] = {
            "uuid": gen.client_uuid,
            "port": gen.xray_port,
            "path": gen.xray_path,
            "cdn_host": gen.cdn_host
        }
    
    return json.dumps(configs, indent=2)


# ============================================================================
# Legacy MCP Tools (merged from mcp_server_legacy.py)
# ============================================================================

@mcp.tool()
def check_environment() -> dict:
    """
    检查当前环境状态
    
    自然语言示例：
    - "检查系统环境"
    - "查看 Xray 和 Nginx 是否已安装"
    - "显示系统信息"
    
    Returns:
        系统信息和软件安装状态
    """
    return _installer.check_environment()


@mcp.tool()
def install_dependencies() -> dict:
    """
    安装缺失的 Xray 和 Nginx 组件
    
    自然语言示例：
    - "安装依赖"
    - "安装 Xray 和 Nginx"
    - "自动安装缺失的软件"
    
    注意：需要 root 权限。已安装的组件会被跳过。
    
    Returns:
        安装结果
    """
    return _installer.install_missing()


@mcp.tool()
def generate_configs(
    domains: list[str],
    xray_port: int = 10000,
    xray_path: Optional[str] = None,
    cdn_host: Optional[str] = None
) -> dict:
    """
    生成 Xray 和 Nginx 配置（批量模式）
    
    自然语言示例：
    - "为 proxy1.example.com 和 proxy2.example.com 生成配置"
    - "批量生成多个域名的 Xray 配置"
    
    Args:
        domains: 域名列表（如 ["proxy1.example.com", "proxy2.example.com"]）
        xray_port: Xray 监听端口（默认 10000）
        xray_path: XHTTP 路径（不指定则自动生成）
        cdn_host: CDN 反代地址
    
    Returns:
        生成的配置和客户端 UUID
    """
    if not domains:
        return {"error": "至少需要一个域名"}
    
    config_gen = ConfigGenerator(
        domains=domains,
        xray_port=xray_port,
        xray_path=xray_path,
        cdn_host=cdn_host
    )
    
    # 保存到全局状态
    for domain in domains:
        _current_xray_configs[domain] = config_gen
    
    # 更新订阅服务
    subscription_service.update_config(
        uuid=config_gen.client_uuid,
        domains=domains,
        path=config_gen.xray_path,
        cdn_host=cdn_host
    )
    
    # 生成 Nginx 配置内容（不保存文件）
    nginx_configs = {}
    for domain in domains:
        nginx_configs[domain] = generate_xray_config(
            domain=domain,
            xray_port=xray_port,
            xray_path=config_gen.xray_path
        )
    
    return {
        "success": True,
        "uuid": config_gen.client_uuid,
        "domains": domains,
        "xray_path": config_gen.xray_path,
        "cdn_host": cdn_host,
        "xray_config": config_gen.xray_config.to_dict(),
        "nginx_configs": nginx_configs
    }


@mcp.tool()
def deploy_configs(
    xray_config_path: str = "/usr/local/etc/xray/config.json",
    nginx_config_dir: str = "/etc/nginx/conf.d"
) -> dict:
    """
    部署生成的配置并重启服务
    
    自然语言示例：
    - "部署配置"
    - "应用配置并重启服务"
    
    Args:
        xray_config_path: Xray 配置文件路径
        nginx_config_dir: Nginx 配置目录
    
    Returns:
        部署状态和服务重启结果
    """
    if not _current_xray_configs:
        return {"error": "没有生成配置。请先调用 generate_configs 或 add_xray_service"}
    
    results = {"xray": {}, "nginx": {}}
    
    # 获取任意一个配置（用于保存 Xray config.json）
    any_config = next(iter(_current_xray_configs.values()))
    
    try:
        # 保存 Xray 配置
        xray_path = Path(xray_config_path)
        xray_path.parent.mkdir(parents=True, exist_ok=True)
        xray_path.write_text(any_config.generate_xray_json())
        results["xray"]["config_saved"] = str(xray_path)
        
        # 重启 Xray
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
        # 保存 Nginx 配置（每个域名一个文件）
        nginx_dir = Path(nginx_config_dir)
        nginx_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for domain, config_gen in _current_xray_configs.items():
            config_content = generate_xray_config(
                domain=domain,
                xray_port=config_gen.xray_port,
                xray_path=config_gen.xray_path
            )
            config_file = nginx_dir / f"xray-{domain.replace('.', '-')}.conf"
            config_file.write_text(config_content)
            saved_files.append(str(config_file))
        
        results["nginx"]["configs_saved"] = saved_files
        
        # 重载 Nginx
        nginx_reload = subprocess.run(
            ["systemctl", "reload", "nginx"],
            capture_output=True,
            text=True
        )
        results["nginx"]["reload"] = {
            "success": nginx_reload.returncode == 0,
            "message": nginx_reload.stderr if nginx_reload.returncode != 0 else "OK"
        }
    except Exception as e:
        results["nginx"]["error"] = str(e)
    
    return results


if __name__ == "__main__":
    # 运行 MCP 服务器
    mcp.run()

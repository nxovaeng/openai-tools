"""
Nginx configuration generator - 模块化配置，每个服务独立配置文件

架构：Client (443) --> Nginx TLS --> Backend (127.0.0.1:port)
特点：一个服务一个配置文件，互不影响，方便手动添加新服务
"""

from pathlib import Path
from typing import Optional


def generate_service_config(
    domain: str,
    backend_port: int,
    service_name: str,
    location_path: str = "/",
    ssl_cert_path: Optional[str] = None,
    ssl_key_path: Optional[str] = None,
    extra_config: str = ""
) -> str:
    """
    生成单个服务的 Nginx 配置
    
    Args:
        domain: 域名或子域名
        backend_port: 后端服务端口
        service_name: 服务名称（用于注释）
        location_path: 路径匹配（默认 /）
        ssl_cert_path: SSL 证书路径（可选，默认使用 Let's Encrypt）
        ssl_key_path: SSL 私钥路径（可选）
        extra_config: 额外的 location 配置
    
    Returns:
        Nginx 配置内容
    """
    # 确定证书路径
    if ssl_cert_path and ssl_key_path:
        cert = ssl_cert_path
        key = ssl_key_path
    else:
        cert = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        key = f"/etc/letsencrypt/live/{domain}/privkey.pem"
    
    return f"""# {service_name} - {domain}
# Backend: 127.0.0.1:{backend_port}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain};
    
    # SSL 证书
    ssl_certificate {cert};
    ssl_certificate_key {key};
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 反向代理到后端服务
    location {location_path} {{
        proxy_pass http://127.0.0.1:{backend_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        {extra_config}
    }}
}}

# HTTP 重定向到 HTTPS
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    
    location /.well-known/acme-challenge/ {{
        root /var/www/html;
    }}
    
    location / {{
        return 301 https://$host$request_uri;
    }}
}}
"""


def generate_xray_config(
    domain: str,
    xray_port: int,
    xray_path: str,
    ssl_cert_path: Optional[str] = None,
    ssl_key_path: Optional[str] = None
) -> str:
    """生成 Xray 服务的 Nginx 配置"""
    
    # 确定证书路径
    if ssl_cert_path and ssl_key_path:
        cert = ssl_cert_path
        key = ssl_key_path
    else:
        cert = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        key = f"/etc/letsencrypt/live/{domain}/privkey.pem"
    
    return f"""# Xray VLESS+XHTTP - {domain}
# Backend: 127.0.0.1:{xray_port}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain};
    
    # SSL 证书
    ssl_certificate {cert};
    ssl_certificate_key {key};
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Xray XHTTP 路径
    location ~ ^{xray_path} {{
        proxy_pass http://127.0.0.1:{xray_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 禁用缓冲
        proxy_buffering off;
        proxy_cache off;
    }}
    
    # 伪装页面
    location / {{
        return 200 "Welcome";
        add_header Content-Type text/plain;
    }}
}}

# HTTP 重定向
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    
    location /.well-known/acme-challenge/ {{
        root /var/www/html;
    }}
    
    location / {{
        return 301 https://$host$request_uri;
    }}
}}
"""


def generate_main_nginx_conf() -> str:
    """生成主 nginx.conf"""
    return """user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';
    
    access_log /var/log/nginx/access.log main;
    
    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 50M;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # 包含所有服务配置（每个服务一个文件）
    include /etc/nginx/conf.d/*.conf;
}
"""


class NginxServiceManager:
    """Nginx 服务配置管理器"""
    
    def __init__(self, conf_dir: str = "/etc/nginx/conf.d"):
        self.conf_dir = Path(conf_dir)
        self.conf_dir.mkdir(parents=True, exist_ok=True)
    
    def add_xray_service(
        self,
        domain: str,
        xray_port: int,
        xray_path: str,
        ssl_cert_path: Optional[str] = None,
        ssl_key_path: Optional[str] = None
    ) -> Path:
        """添加 Xray 服务配置"""
        config = generate_xray_config(domain, xray_port, xray_path, ssl_cert_path, ssl_key_path)
        config_file = self.conf_dir / f"xray-{domain.replace('.', '-')}.conf"
        config_file.write_text(config)
        return config_file
    
    def add_generic_service(
        self,
        domain: str,
        backend_port: int,
        service_name: str,
        location_path: str = "/",
        ssl_cert_path: Optional[str] = None,
        ssl_key_path: Optional[str] = None,
        extra_config: str = ""
    ) -> Path:
        """添加通用服务配置"""
        config = generate_service_config(
            domain, backend_port, service_name, location_path,
            ssl_cert_path, ssl_key_path, extra_config
        )
        config_file = self.conf_dir / f"{service_name.lower().replace(' ', '-')}-{domain.replace('.', '-')}.conf"
        config_file.write_text(config)
        return config_file
    
    def remove_service(self, config_filename: str) -> bool:
        """删除服务配置"""
        config_file = self.conf_dir / config_filename
        if config_file.exists():
            config_file.unlink()
            return True
        return False
    
    def list_services(self) -> list[str]:
        """列出所有服务配置"""
        return [f.name for f in self.conf_dir.glob("*.conf")]


if __name__ == "__main__":
    # 示例：生成 Xray 配置
    print("=== Xray 服务配置 ===")
    print(generate_xray_config("proxy.example.com", 10000, "/a7kRmQ2xJ9vN4pL"))
    
    print("\n=== 通用服务配置示例 ===")
    print(generate_service_config("api.example.com", 3000, "API Service"))
    
    print("\n=== 主配置文件 ===")
    print(generate_main_nginx_conf())

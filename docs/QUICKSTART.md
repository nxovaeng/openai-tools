# OpenAPI Server 快速入门

5 分钟快速开始使用 Xray + Nginx OpenAPI Server！


## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  Client (HTTPS:443)                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Nginx (TLS 终止 + 反向代理)                             │
│  - 统一处理所有域名的 HTTPS                              │
│  - 每个服务一个独立配置文件                              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ↓            ↓            ↓
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Xray    │  │ API     │  │ Web App │
   │ :10000  │  │ :3000   │  │ :8080   │
   └─────────┘  └─────────┘  └─────────┘
```


## 📋 前提条件

- Python 3.8+
- Nginx (可选，用于实际部署)
- Xray (可选，用于实际部署)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd xray-nginx-openapi
```

### 2. 配置环境

```bash
cd mcp-server
cp .env.example .env
```

编辑 `.env` 文件，设置你的 API Key：

```bash
API_KEY=your-secure-random-key-here
```

### 3. 启动服务器

```bash
./start_openapi.sh
```

或手动启动：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python main.py
```

### 4. 验证服务器

打开浏览器访问：

- **API 文档**: http://localhost:8000/docs
- **API 信息**: http://localhost:8000/

## 🔌 集成到 Open WebUI

### 方法 1: 通过 UI 添加

1. 打开 Open WebUI
2. 点击右上角 **⚙️ Settings**
3. 在左侧菜单选择 **Tools**
4. 点击 **➕ Add Tool Server**
5. 输入以下信息：
   - **Name**: Xray Nginx Manager
   - **URL**: `http://localhost:8000`
   - **API Key**: (你在 .env 中设置的 API_KEY)
6. 点击 **Save**

### 方法 2: 通过配置文件

编辑 Open WebUI 配置文件，添加：

```json
{
  "tools": {
    "servers": [
      {
        "name": "Xray Nginx Manager",
        "url": "http://localhost:8000",
        "api_key": "your-api-key-here"
      }
    ]
  }
}
```

## 💬 使用示例

在 Open WebUI 中与 AI 对话：

### 示例 1: 添加 Xray 服务

```
You: 为 proxy.example.com 添加一个 Xray 服务

AI: 我将为你添加 Xray 服务...
    
    ✅ 已成功添加 Xray 服务
    - 域名: proxy.example.com
    - UUID: 12345678-1234-1234-1234-123456789abc
    - 路径: /a7kRmQ2xJ9vN4pL
    - 端口: 10000
    
    下一步操作：
    1. 申请 SSL 证书: certbot --nginx -d proxy.example.com
    2. 重载 Nginx: nginx -s reload
    3. 启动 Xray: systemctl start xray
```

### 示例 2: 添加 Web 服务

```
You: 部署一个 API 服务到 api.example.com，后端端口 3000

AI: 我将为你配置 API 服务...
    
    ✅ 已成功添加 Web 服务
    - 域名: api.example.com
    - 后端端口: 3000
    - 服务名称: API Service
    
    功能：
    - WebSocket: 否
    - Gzip 压缩: 是
    - 最大请求体: 50M
```

### 示例 3: 查看所有服务

```
You: 列出所有配置的服务

AI: 当前配置的服务：
    
    1. xray-proxy-example-com.conf
       - 类型: Xray VLESS+XHTTP
       - 域名: proxy.example.com
    
    2. api-service-api-example-com.conf
       - 类型: Web Service
       - 域名: api.example.com
    
    总计: 2 个服务
```

### 示例 4: 获取订阅链接

```
You: 生成订阅链接

AI: 订阅链接已生成：
    
    Base64 格式:
    dmxlc3M6Ly8xMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODlhYmNAcHJveHkuZXhhbXBsZS5jb206NDQzP3R5cGU9eGh0dHAmcGF0aD0vYTdrUm1RMnhKOXZONHBMJnNlY3VyaXR5PXRscyZzbmk9cHJveHkuZXhhbXBsZS5jb20jcHJveHkuZXhhbXBsZS5jb20=
    
    节点列表:
    - proxy.example.com (VLESS+XHTTP)
```

## 🧪 测试 API

### 使用测试脚本

```bash
# 编辑 test_openapi.py，设置你的 API_KEY
python test_openapi.py
```

### 使用 curl

```bash
# 获取 API 信息
curl http://localhost:8000/

# 查看 OpenAPI 文档
curl http://localhost:8000/openapi.json

# 列出服务（需要 API Key）
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/nginx/services

# 添加 Xray 服务
curl -X POST http://localhost:8000/nginx/xray \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{
       "domain": "proxy.example.com",
       "xray_port": 10000
     }'

# 测试 Nginx 配置
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/nginx/test

# 重载 Nginx
curl -X POST http://localhost:8000/nginx/reload \
     -H "X-API-Key: your-api-key"
```

### 使用 Python

```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# 添加 Xray 服务
response = requests.post(
    f"{BASE_URL}/nginx/xray",
    json={
        "domain": "proxy.example.com",
        "xray_port": 10000
    },
    headers=headers
)

print(response.json())
```


## 🌐 公网部署

### 使用 Cloudflare Tunnel

```bash
# 安装 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# 创建隧道
./cloudflared tunnel --url http://localhost:8000
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 安全建议

1. **使用强 API Key**
   ```bash
   # 生成随机 API Key
   openssl rand -hex 32
   ```

2. **启用 HTTPS**
   - 在生产环境中始终使用 HTTPS
   - 使用 Let's Encrypt 免费证书

3. **限制访问**
   - 使用防火墙限制访问
   - 配置 Nginx 速率限制

4. **定期更新**
   - 保持依赖包更新
   - 定期更新 Xray 和 Nginx

## 📚 更多资源

- [Open WebUI 文档](https://docs.openwebui.com/)
- [Xray 文档](https://xtls.github.io/)
- [Nginx 文档](https://nginx.org/en/docs/)

## ❓ 常见问题

### Q: 如何更改端口？

A: 编辑 `.env` 文件中的 `PORT` 变量：

```bash
PORT=9000
```

### Q: 如何禁用认证？

A: 编辑 `.env` 文件：

```bash
REQUIRE_AUTH=false
```

### Q: 如何查看日志？

A: 服务器日志会输出到控制台。使用 systemd 或 Docker 查看：

```bash
# Systemd
journalctl -u xray-nginx-api -f

```

### Q: 如何备份配置？

A: 备份以下目录：

```bash
tar -czf backup.tar.gz \
  /etc/nginx/conf.d \
  /etc/xray \
  mcp-server/.env
```

## 📄 许可证

MIT License

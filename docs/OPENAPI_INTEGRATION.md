# Open WebUI 集成指南

本项目现已完全兼容 [Open WebUI OpenAPI Servers](https://github.com/open-webui/openapi-servers) 标准。

## 🎯 什么是 OpenAPI Tool Server？

OpenAPI Tool Server 是一种标准化的工具服务器，使用广泛采用的 OpenAPI 规范作为协议。它可以轻松集成到 LLM 代理和工作流中，无需专有协议或复杂配置。

## ✨ 特性

- ✅ **标准 OpenAPI 规范** - 完全兼容 OpenAPI 3.0
- ✅ **自动文档生成** - 访问 `/docs` 查看交互式 API 文档
- ✅ **Open WebUI 集成** - 一键添加到 Open WebUI
- ✅ **RESTful API** - 标准 HTTP/HTTPS 通信
- ✅ **安全认证** - 支持 API Key 认证

## 🚀 快速开始

### 1. 启动服务器

```bash
cd mcp-server
python main.py
```

服务器将在 `http://localhost:8000` 启动。

### 2. 查看 API 文档

在浏览器中打开：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 3. 集成到 Open WebUI

1. 打开 Open WebUI
2. 进入 **⚙️ Settings**
3. 点击 **➕ Tools** 添加新工具服务器
4. 输入服务器 URL: `http://localhost:8000`
5. 如果启用了认证，添加 API Key
6. 点击 **Save**

## 📡 API 端点

### Nginx 配置管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/nginx/xray` | POST | 添加 Xray VLESS+XHTTP 服务 |
| `/nginx/web` | POST | 添加 Web 服务或 API |
| `/nginx/services` | GET | 列出所有服务 |
| `/nginx/services/{name}` | DELETE | 删除服务配置 |
| `/nginx/test` | GET | 测试 Nginx 配置 |
| `/nginx/reload` | POST | 重载 Nginx |

### 订阅和监控

| 端点 | 方法 | 描述 |
|------|------|------|
| `/subscription` | GET | 获取 VLESS 订阅链接 |
| `/status` | GET | 查看服务状态 |

## 💡 使用示例

### 在 Open WebUI 中使用

与 AI 对话时，可以直接使用自然语言：

```
User: 为 proxy.example.com 添加一个 Xray 服务

AI: 我将为你添加 Xray 服务...
    [调用 POST /nginx/xray]
    
    ✅ 已成功添加 Xray 服务
    - 域名: proxy.example.com
    - UUID: xxx-xxx-xxx
    - 路径: /a7kRmQ2xJ9vN4pL
    
    下一步：
    1. 申请 SSL 证书: certbot --nginx -d proxy.example.com
    2. 重载 Nginx: nginx -s reload
```

### 使用 curl 测试

```bash
# 添加 Xray 服务
curl -X POST http://localhost:8000/nginx/xray \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "domain": "proxy.example.com",
    "xray_port": 10000
  }'

# 列出所有服务
curl http://localhost:8000/nginx/services \
  -H "X-API-Key: your-api-key"

# 获取订阅链接
curl http://localhost:8000/subscription

# 测试 Nginx 配置
curl http://localhost:8000/nginx/test \
  -H "X-API-Key: your-api-key"

# 重载 Nginx
curl -X POST http://localhost:8000/nginx/reload \
  -H "X-API-Key: your-api-key"
```

## 🔒 安全配置

### 启用 API Key 认证

在 `.env` 文件中配置：

```bash
# 启用认证
REQUIRE_AUTH=true

# 设置 API Key
API_KEY=your-secure-api-key-here
```

### 使用 HTTPS

建议在生产环境中使用 HTTPS：

```bash
# 使用 Nginx 反向代理
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐳 Docker 部署

### 使用 Docker Compose

```yaml
version: '3.8'

services:
  xray-nginx-api:
    build: ./mcp-server
    ports:
      - "8000:8000"
    environment:
      - REQUIRE_AUTH=true
      - API_KEY=${API_KEY}
    volumes:
      - /etc/nginx:/etc/nginx
      - /etc/xray:/etc/xray
    restart: unless-stopped
```

启动：

```bash
docker compose up -d
```

## 📚 与 MCP 的区别

| 特性 | MCP Server | OpenAPI Server |
|------|-----------|----------------|
| 协议 | 专有 MCP 协议 | 标准 HTTP/REST |
| 文档 | 需要手动编写 | 自动生成 |
| 集成 | 需要 MCP 客户端 | 任何 HTTP 客户端 |
| 认证 | 自定义 | 标准 HTTP 认证 |
| 部署 | 需要特殊配置 | 标准 Web 服务 |

## 🔄 从 MCP 迁移

如果你之前使用 MCP Server (`nginx_mcp_server.py`)，现在可以切换到 OpenAPI Server：

1. **停止 MCP Server**:
   ```bash
   # 停止 nginx_mcp_server.py
   ```

2. **启动 OpenAPI Server**:
   ```bash
   python main.py
   ```

3. **更新客户端配置**:
   - 从 MCP 客户端切换到 HTTP 客户端
   - 或在 Open WebUI 中添加工具服务器

## 🌐 公网部署

### 使用 Cloudflare Tunnel

```bash
# 安装 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# 创建隧道
./cloudflared tunnel --url http://localhost:8000
```

### 使用 Ngrok

```bash
ngrok http 8000
```

然后在 Open WebUI 中使用生成的公网 URL。

## 📖 更多资源

- [Open WebUI 文档](https://docs.openwebui.com/)
- [OpenAPI 规范](https://www.openapis.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

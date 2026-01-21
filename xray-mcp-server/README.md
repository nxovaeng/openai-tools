# Xray Deployment API

**OpenAPI-compatible** tool server for automated Xray + Caddy deployment with XHTTP protocol.

## Features

- ✅ **One-click deployment** via REST API
- ✅ **XHTTP protocol** (packet-up mode, maximum compatibility)
- ✅ **Automatic configuration** generation for Xray + Caddy
- ✅ **Subscription links** (Base64 VLESS URI)
- ✅ **Natural language interaction** via Open WebUI
- ✅ **Docker support** for easy deployment

---

## Quick Start

### Step 0: Configure API Key (Important!)

首次启动时，服务器会自动生成 API Key 并保存到 `.env` 文件。

**手动设置 API Key** (可选):
```bash
cd xray-mcp-server
echo "API_KEY=your-secret-key-here" > .env
```

> ⚠️ **安全提示**: 请妥善保管 API Key，不要泄露！

**快速启动（推荐）：**
```bash
./start.sh  # 自动创建 venv 并启动服务
```

### Option 1: Virtual Environment (推荐)

**适用于 Debian/Ubuntu 等启用了 PEP 668 保护的系统**

```bash
cd xray-mcp-server

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行服务器
uvicorn main:app --host 0.0.0.0 --port 8000
```

**后续启动：**
```bash
cd xray-mcp-server
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 2: System-wide (需要 root)

```bash
cd xray-mcp-server
sudo pip3 install -r requirements.txt --break-system-packages
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 3: Docker All-in-One (推荐容器化)

**完整的容器化方案**：API + Xray + Caddy 都在容器中，自动部署和重启。

```bash
cd xray-mcp-server
docker compose -f docker-compose.allinone.yaml up -d
```

**功能：**
- ✅ 完全自动化部署
- ✅ API 可以自动重启 Xray/Caddy
- ✅ supervisord 管理进程
- ✅ 配置持久化

详细文档：[docker/README.md](file:///home/yimeng/tools/xray-mcp-server/docker/README.md)

### Option 4: Docker (仅配置) (仅生成配置)

**重要说明**: Docker 模式仅会生成配置文件，不会实际部署  Xray/Caddy 服务。

```bash
cd xray-mcp-server
docker compose up -d
```

**使用流程：**
1. API 生成配置文件到 `./configs/` 目录
2. 手动将配置复制到系统目录：
   ```bash
   sudo cp configs/xray-config.json /usr/local/etc/xray/config.json
   sudo cp configs/Caddyfile /etc/caddy/conf.d/xray-auto.caddy
   sudo systemctl restart xray
   sudo systemctl reload caddy
   ```

**为什么不能自动部署？**
- Docker 容器无法安装宿主机软件
- 容器内 `systemctl` 无法控制宿主机服务

> 如需完全自动部署，请使用 **Option 1 (虚拟环境)** 或 **Option 4 (systemd)**

### Option 4: Production (systemd + venv)

```bash
# Create service file
sudo tee /etc/systemd/system/xray-api.service > /dev/null << 'EOF'
[Unit]
Description=Xray Deployment API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/xray-mcp-server
ExecStart=/path/to/xray-mcp-server/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable xray-api
sudo systemctl start xray-api
```

---

## API Endpoints

访问 **OpenAPI 文档**: `http://your-server:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/environment` | Check Caddy/Xray installation status |
| POST | `/install` | Install dependencies |
| POST | `/deploy` | Deploy Xray + Caddy (one-click) |
| GET | `/subscription` | Get subscription link |
| GET | `/status` | Service status |

---

## Usage Examples

**所有受保护的 API 都需要在请求头中包含 X-API-Key！**

### 0. 获取 API Key

```bash
cat .env
# API_KEY=iKt-qkjps0oP3-jewhv6V-CQGOx9nhry1ODkjOXii48
```

### 1. Check Environment (无需认证)

```bash
curl http://localhost:8000/environment
```

### 2. One-Click Deploy (需要认证)

```bash
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "domains": ["proxy.example.com"],
    "xray_path": "/xray",
    "xray_port": 10000
  }'
```

Returns:
```json
{
  "success": true,
  "uuid": "a1b2c3d4-...",
  "domains": ["proxy.example.com"],
  "xray_config": {...},
  "caddyfile": "...",
  "deployment_status": {...}
}
```

### 3. Get Subscription

```bash
curl http://localhost:8000/subscription?format=base64
```

Returns:
```json
{
  "format": "base64",
  "subscription": "dmxlc3M6Ly8uLi4=",
  "nodes": [...]
}
```

---

## Open WebUI Integration

### Step 1: Deploy API Server

```bash
# VPS 上运行
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 2: Add to Open WebUI

在 Open WebUI 设置中添加工具服务器：

```
URL: http://your-vps-ip:8000
```

### Step 3: Natural Language Interaction

```
User: 帮我部署一个代理，域名是 proxy.example.com
AI:   好的，我来帮你部署...
      [调用 /deploy 接口]
      已成功部署！订阅链接：vmxlc3M6Ly8...
```

---

## Configuration Management

### 不会覆盖现有配置！

本工具采用 **配置片段 (snippet)** 方式部署，**不会覆盖**您手动添加的 Caddy 配置。

**工作原理：**

1. Xray 配置写入：`/etc/caddy/conf.d/xray-auto.caddy`
2. 主配置文件自动添加 import 指令：`import /etc/caddy/conf.d/*.caddy`
3. 您的其他配置保持不变

**文件结构：**
```
/etc/caddy/
├── Caddyfile         # 您的主配置（不会被覆盖）
└── conf.d/
    └── xray-auto.caddy  # 自动生成的 Xray 配置
```

**手动管理：**
- 编辑其他配置：直接修改 `/etc/caddy/Caddyfile`
- 查看 Xray 配置：`cat /etc/caddy/conf.d/xray-auto.caddy`
- 删除 Xray 配置：`rm /etc/caddy/conf.d/xray-auto.caddy && systemctl reload caddy`

---

## Configuration

生成的 Xray 配置示例：

```json
{
  "inbounds": [{
    "protocol": "vless",
    "settings": {
      "clients": [{"id": "uuid", "flow": ""}]
    },
    "streamSettings": {
      "network": "xhttp",
      "xhttpSettings": {"path": "/xray", "mode": "packet-up"}
    }
  }]
}
```

生成的 Caddyfile 示例：

```caddyfile
proxy.example.com {
    reverse_proxy /xray 127.0.0.1:10000 {
        flush_interval -1
    }
    respond "Welcome" 200
}
```

---

## Architecture

```
Open WebUI → HTTP → FastAPI → Config Generator → Deploy
                                      ↓
                              Xray + Caddy Configs
                                      ↓
                              systemctl restart
```

---

## Security

### Reverse Proxy (推荐)

使用 Caddy 反向代理并添加认证：

```caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
    
    basicauth {
        admin $2a$14$...  # bcrypt hash
    }
}
```

### Firewall

```bash
# 只允许特定 IP 访问
sudo ufw allow from YOUR_IP to any port 8000
```

---

## Project Structure

```
xray-mcp-server/
├── main.py                # FastAPI application
├── models.py              # Pydantic schemas
├── config_generator.py    # Xray/Caddy config generator
├── installer.py           # Auto-installer
├── subscription.py        # Subscription link generator
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker image
└── docker-compose.yaml    # Docker Compose
```

---

## Support

- Xray Protocol: **VLESS + XHTTP (packet-up)**
- Client Compatibility: v2rayN, v2rayNG, Shadowrocket
- Platform Integration: Open WebUI, Dify, custom clients

---

## License

MIT

# Xray Deployment MCP Server

**MCP 工具服务器**用于自动化 Xray + Caddy 部署，支持 XHTTP 协议。

## 特性

- ✅ **MCP 工具集成** - 与 Open WebUI、Dify 等 AI 平台无缝集成
- ✅ **XHTTP 协议** (packet-up 模式，最大兼容性)
- ✅ **自动配置生成** - 为 Xray + Caddy 生成配置
- ✅ **订阅链接** - 生成 Base64 编码的 VLESS URI
- ✅ **SNI 和 CDN 支持** - 支持自定义 SNI 和 CDN 反代地址
- ✅ **Docker 完整部署** - 一键容器化部署

---

## 快速启动

### 方式一：MCP Server (推荐用于 AI 集成)

```bash
cd xray-mcp-server
./start.sh  # 自动创建 venv 并启动 MCP 服务
```

MCP 服务器启动后，可集成到 Open WebUI 或 Dify 等平台。

### 方式二：Docker All-in-One (推荐生产环境)

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

详细文档：[docker/README.md](./docker/README.md)

### 方式三：systemd 服务 (生产部署)

```bash
# 创建虚拟环境
cd xray-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 创建 systemd 服务文件
sudo tee /etc/systemd/system/xray-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Xray Deployment MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/xray-mcp-server
ExecStart=/path/to/xray-mcp-server/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable xray-mcp
sudo systemctl start xray-mcp
```

---

## MCP 工具

通过 MCP 接口可用的工具：

| 工具 | 描述 |
|------|------|
| `check_environment` | 检查 Caddy/Xray 安装状态 |
| `install_dependencies` | 安装缺失的依赖 |
| `generate_configs` | 生成 Xray 和 Caddy 配置 |
| `deploy_configs` | 部署配置到系统路径 |
| `get_subscription` | 获取订阅链接 |
| `restart_services` | 重启 Xray/Caddy 服务 |

---

## 使用示例

## 使用示例

### 在 Open WebUI 中集成

1. 获取 MCP 服务器地址（例如 `http://your-vps-ip:5000`）
2. 在 Open WebUI 的工具设置中添加该服务器
3. 在对话中直接使用 AI 生成和部署配置

### 场景 1: 单个域名部署

```
User: 部署一个代理，域名 proxy1.example.com
AI:   
  generate_configs(
    domains=["proxy1.example.com"],
    # xray_path 自动生成 (e.g., /a7kRmQ2xJ9vN4pL)
  )
  
  生成结果：
  - Xray: VLESS 入站，SNI = proxy1.example.com
  - Caddy: proxy1.example.com 虚拟主机反代
  - 订阅: vless://uuid@proxy1.example.com:443?...&sni=proxy1.example.com
```

### 场景 2: 多个域名多入口

```
User: 我有多个域名 proxy1.example.com 和 proxy2.example.com，生成多个入口
AI:
  generate_configs(
    domains=["proxy1.example.com", "proxy2.example.com"]
  )
  
  生成结果：
  - Xray: VLESS 入站（支持多 domain）
  - Caddy: 生成两个虚拟主机
    * proxy1.example.com -> SNI 路由到 proxy1.example.com
    * proxy2.example.com -> SNI 路由到 proxy2.example.com
  - 订阅: 
    * vless://uuid@proxy1.example.com:443?...&sni=proxy1.example.com
    * vless://uuid@proxy2.example.com:443?...&sni=proxy2.example.com
```

### 场景 3: 使用 CDN 反代域名

```
User: 域名是 proxy.example.com，但我想通过 CDN 反代域名 cdn.example.com 访问
AI:
  generate_configs(
    domains=["proxy.example.com"],
    cdn_host="cdn.example.com"
  )
  
  生成结果：
  - Caddy: proxy.example.com 虚拟主机 (SNI 路由)
  - 订阅: vless://uuid@cdn.example.com:443?...&sni=proxy.example.com
    * 客户端连接到 cdn.example.com
    * SNI 发送 proxy.example.com 用于 Caddy 路由
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `domains` | 必需，Caddy 虚拟主机列表，每个 domain 各自的 SNI | `["proxy1.com", "proxy2.com"]` |
| `xray_path` | 可选，XHTTP 路径，不指定自动生成随机 | `/secret-path` 或省略 |
| `xray_port` | 可选，Xray 监听端口，默认 10000 | `10000` |
| `cdn_host` | 可选，CDN 反代域名，替换订阅中的 domain | `cdn.example.com` |

---

## 配置管理

### Caddy 分路径配置

系统采用**模块化分路径配置**，支持灵活扩展：

**目录结构**：
```
/etc/caddy/
├── Caddyfile              # 主配置文件（import 管理）
└── conf.d/
    ├── xray-auto.caddy    # 自动生成的 Xray 反代配置
    └── custom-*.caddy     # 用户自定义配置（可选）
```

**主 Caddyfile 示例**：
```caddyfile
{
    admin off
}

# 自动包含所有子配置
import /etc/caddy/conf.d/*.caddy
```

**自动生成的 xray-auto.caddy**：
```caddyfile
proxy1.example.com {
    @xhttp path /a7kRmQ2xJ9vN4pL*
    reverse_proxy @xhttp 127.0.0.1:10000 {
        flush_interval -1
    }
    respond "Welcome" 200
}
```

### 添加其他服务代理

无需修改自动生成的配置，直接在主 Caddyfile 或新建 `conf.d/custom-services.caddy`：

```caddyfile
# Open WebUI
open-webui.example.com {
    reverse_proxy localhost:8111
}

# 其他服务
api.example.com {
    reverse_proxy localhost:3000
}
```

**重启 Caddy 使配置生效**：
```bash
supervisorctl restart caddy
# 或
sudo systemctl reload caddy
```

### Docker Host 网络模式

Docker Compose 采用 `host` 网络模式优势：

- ✅ 无需端口映射，容器直接使用宿主机端口
- ✅ 方便添加其他服务（Open WebUI 等）
- ✅ 性能更优，避免 NAT 开销
- ✅ 便于调试，直接访问 localhost

**特别适用于**：
```
同服务器部署多个应用：
├── Xray (容器内) → localhost:10000
├── Open WebUI → localhost:8111
├── Caddy (容器内) → localhost:80/443
└── 其他服务 → localhost:XXXX
```

---

## 生成配置详解

### Xray 配置（VLESS + XHTTP）

基于 [Xray 官方文档](https://xtls.github.io/)，生成的配置采用 VLESS + XHTTP 协议组合：

```json
{
  "inbounds": [{
    "protocol": "vless",
    "settings": {
      "clients": [{"id": "uuid", "flow": ""}],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "xhttp",
      "xhttpSettings": {
        "path": "/a7kRmQ2xJ9vN4pL",  // 随机生成，增强隐蔽性
        "mode": "packet-up"           // Packet-Up 模式优化数据包
      }
    }
  }],
  "outbounds": [{
    "protocol": "freedom",
    "tag": "direct"
  }]
}
```

**协议选择说明：**
- **VLESS** - Xray 推荐的轻量级协议，低开销高性能
- **XHTTP** - 新一代伪装协议，基于 HTTP 伪装
- **packet-up 模式** - 数据包优化模式，提高兼容性

### Caddy 配置（反向代理）

```caddyfile
proxy.example.com {
    # XHTTP 反向代理到 Xray
    @xhttp path /a7kRmQ2xJ9vN4pL*
    reverse_proxy @xhttp 127.0.0.1:10000 {
        flush_interval -1
        header_up X-Forwarded-For {remote_host}
    }
    
    # 伪装默认响应
    respond "Welcome to proxy.example.com" 200
}
}
```

### 订阅配置（包含 SNI）

```
vless://uuid@proxy.example.com:443?type=xhttp&security=tls&path=%2Fxray&sni=google.com#proxy.example.com
```

---

## 配置管理

### 配置存储

- **Xray 配置**: `/etc/xray/config.json` 或 `/usr/local/etc/xray/config.json`
- **Caddy 配置**: `/etc/caddy/Caddyfile` 或配置片段方式
- **订阅数据**: 内存存储（需要持久化时写入数据库）

### 不会覆盖现有配置！

本工具采用 **配置片段 (snippet)** 方式部署，**不会覆盖**您手动添加的 Caddy 配置。

**文件结构：**
```
/etc/caddy/
├── Caddyfile              # 您的主配置（不会被覆盖）
└── conf.d/
    └── xray-auto.caddy    # 自动生成的 Xray 配置
```

---

## 项目结构

```
xray-mcp-server/
├── main.py                # FastAPI REST 接口
├── server.py              # MCP 工具服务器
├── models.py              # Pydantic 数据模型
├── config_generator.py    # Xray/Caddy 配置生成器
├── installer.py           # 自动安装程序
├── subscription.py        # 订阅链接生成器
├── auth.py                # 认证模块
├── requirements.txt       # 依赖列表
├── start.sh               # 启动脚本
├── Dockerfile             # 容器镜像
└── docker-compose.allinone.yaml  # 完整容器编排
```

---

## 支持

- **Xray 协议**: VLESS + XHTTP (packet-up)
- **客户端兼容**: v2rayN, v2rayNG, Shadowrocket, Clash 等
- **集成平台**: Open WebUI, Dify, 自定义 MCP 客户端

---

## License

MIT


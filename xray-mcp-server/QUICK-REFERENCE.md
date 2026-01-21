# 快速参考卡片

## 项目一句话描述

**Xray + Caddy 自动化部署 MCP 服务器** - 为 AI 平台提供 VLESS/XHTTP 代理配置生成、部署和管理工具

---

## 🚀 快速开始

### Docker 启动（推荐）

```bash
docker-compose up -d
# 服务运行在 host 网络模式，访问 localhost
```

### 生成配置

```bash
curl -X POST http://localhost:8000/deploy \
  -H "X-API-Key: $(cat .env | grep API_KEY)" \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["proxy1.example.com", "proxy2.example.com"],
    "cdn_host": "cdn.example.com"
  }'
```

### 获取订阅链接

```bash
curl "http://localhost:8000/subscription?format=v2ray" \
  -H "X-API-Key: $(cat .env | grep API_KEY)"
```

---

## 📁 文件组织

```
/etc/caddy/
├── Caddyfile              # ← 主配置（用户可编辑）
│   包含: import /etc/caddy/conf.d/*.caddy
│
└── conf.d/
    └── xray-auto.caddy    # ← 自动生成（勿手动编辑）
        包含: 所有域名的虚拟主机块

/etc/xray/
└── config.json            # ← Xray VLESS + XHTTP 配置
```

---

## 🔧 MCP 工具 API

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `check_environment()` | 检查系统状态 | 无 |
| `install_dependencies()` | 自动安装依赖 | 无 |
| `generate_configs()` | 生成配置 | `domains`, `cdn_host` |
| `deploy_configs()` | 部署并重启 | 无（使用上次生成的配置）|
| `get_subscription()` | 获取订阅链接 | `format` (v2ray/clash) |
| `restart_services()` | 重启服务 | 无 |

### 生成配置示例

```python
# 自动生成随机路径（推荐）
generate_configs(
    domains=["proxy1.example.com", "proxy2.example.com"],
    cdn_host="cdn.example.com"
)
# → xray_path: /QOFehQyG5xZGhN0D (自动生成，每次不同)

# 或指定路径
generate_configs(
    domains=["proxy1.example.com"],
    xray_path="/api/v1",
    cdn_host="cdn.example.com"
)
```

---

## 🌐 配置说明

### domains（域名列表）

```
["proxy1.example.com", "proxy2.example.com"]
  ↓
每个域名获得：
- Caddy 虚拟主机块
- 独立的 SNI（= 域名本身）
- 独立的订阅节点
```

### xray_path（XHTTP 伪装路径）

```
不指定 → 自动生成（16字符随机路径）
  示例: /QOFehQyG5xZGhN0D
  
指定值 → 使用固定路径
  示例: /api/v1
```

### cdn_host（CDN 反向代理）

```
有 CDN：
client → cdn.example.com → SNI: proxy1.example.com → Caddy → Xray
                          ↑ 用于 TLS 握手和路由

无 CDN：
client → proxy1.example.com → SNI: proxy1.example.com → Caddy → Xray
```

---

## 📊 订阅链接格式

### V2ray 格式（Base64 编码）

```
vless://uuid@cdn.example.com:443?
  type=xhttp&
  security=tls&
  path=%2FQOFehQyG5xZGhN0D&
  sni=proxy1.example.com
```

### Clash 格式（YAML）

```yaml
- name: "Xray VLESS"
  type: vless
  server: cdn.example.com
  port: 443
  uuid: xxx-xxx-xxx
  network: xhttp
  xhttp-opts:
    path: /QOFehQyG5xZGhN0D
  tls: true
  servername: proxy1.example.com
```

---

## 🔒 安全特性

✅ **随机路径生成**
- 使用 Python `secrets` 模块
- 16 字符 URL 安全字符串
- 每次生成都不同

✅ **API 认证**
- 方式 1: `-H "X-API-Key: KEY"`
- 方式 2: `-H "Authorization: Bearer KEY"`

✅ **FastAPI 文档禁用**
- 无 `/docs` 端点
- 无 `/redoc` 端点

---

## 🛠️ 故障排查

### Caddy 配置检查

```bash
# 验证 Caddyfile 语法
sudo caddy validate --config /etc/caddy/Caddyfile

# 查看详细错误
docker exec xray-allinone supervisorctl tail caddy -f
```

### Xray 配置检查

```bash
# 验证配置
xray test -c /etc/xray/config.json

# 查看日志
docker exec xray-allinone supervisorctl tail xray -f
```

### 服务状态

```bash
# 容器内检查
docker exec xray-allinone supervisorctl status

# 查看监听端口
sudo netstat -tlnp | grep -E ':80|:443|:10000'
```

---

## 📝 添加其他服务代理

### 方式 1：编辑主 Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

添加（在 import 指令后）：

```caddyfile
# Open WebUI
open-webui.example.com {
    reverse_proxy localhost:8111
}
```

### 方式 2：新建配置文件

```bash
sudo nano /etc/caddy/conf.d/custom-services.caddy
```

内容相同，文件会自动被 import 包含。

### 重载配置

```bash
docker exec xray-allinone supervisorctl reload caddy
# 或
sudo systemctl reload caddy
```

---

## 🐳 Docker 网络模式说明

### Host 网络模式的优势

```
┌─ Host Network
│  ├─ Xray: localhost:10000
│  └─ Caddy: localhost:80/443
│
├─ 优势
│  ✓ 无 NAT 转换
│  ✓ 无端口冲突
│  ✓ 性能最优
│  ✓ 易于集成其他服务
```

### 端口检查

```bash
# 确保这些端口可用
80    - HTTP
443   - HTTPS
10000 - Xray
```

---

## 📚 文档导航

| 文档 | 用途 |
|------|------|
| [README.md](README.md) | 项目概览和基本说明 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 详细部署指南（3 种方式）|
| [MCP-TOOLS.md](MCP-TOOLS.md) | MCP 工具完整 API 文档 |
| [Caddyfile.template](Caddyfile.template) | Caddy 配置示例 |
| [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md) | 项目完成总结 |

---

## 🔑 API 密钥管理

### 查看 API 密钥

```bash
cat .env | grep API_KEY
```

### 生成新密钥

```bash
# 删除 .env
rm .env

# 重启容器，自动生成新密钥
docker-compose restart xray-allinone

# 查看新密钥
docker exec xray-allinone cat /app/.env | grep API_KEY
```

---

## ⚡ 性能提示

### 最优配置

```yaml
# docker-compose.yaml 资源限制
resources:
  limits:
    cpus: '2'
    memory: 1G
  reservations:
    cpus: '1'
    memory: 512M
```

### 监控命令

```bash
# 查看容器资源使用
docker stats xray-allinone

# 查看进程
docker exec xray-allinone ps aux | grep -E 'xray|caddy'
```

---

## 🔄 更新和维护

### 更新 Docker 镜像

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 更新系统包

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get upgrade caddy xray

# 重启服务
docker exec xray-allinone supervisorctl restart caddy xray
```

### 备份配置

```bash
# 备份 Caddy
sudo cp -r /etc/caddy /backup/caddy-$(date +%Y%m%d)

# 备份 Xray
sudo cp -r /etc/xray /backup/xray-$(date +%Y%m%d)

# 备份 API 密钥
cp .env /backup/.env-$(date +%Y%m%d)
```

---

## 💡 常见场景

### 场景 1：单域名快速部署

```bash
generate_configs(
    domains=["proxy.example.com"]
)
deploy_configs()
sub_link = get_subscription(format="v2ray")
# → 生成订阅链接供用户导入
```

### 场景 2：多域名 + CDN 配置

```bash
generate_configs(
    domains=["p1.example.com", "p2.example.com"],
    cdn_host="cdn.example.com"
)
deploy_configs()
sub_link = get_subscription(format="v2ray")
# → 多个节点，通过 CDN 访问
```

### 场景 3：添加新服务（Open WebUI）

```bash
# 1. 修改 Caddyfile
nano /etc/caddy/Caddyfile
# 添加: open-webui.example.com { ... }

# 2. 重载配置
supervisorctl reload caddy

# 3. 访问新服务
# https://open-webui.example.com
```

---

## 📞 获取帮助

1. 查看详细文档：`DEPLOYMENT.md` 和 `MCP-TOOLS.md`
2. 检查日志：`docker logs -f xray-allinone`
3. 验证配置：`caddy validate` 和 `xray test`
4. 运行系统检查：`check_environment()`

---

**最后更新**：2024 年

**项目状态**：✅ 生产就绪

**版本**：v1.0

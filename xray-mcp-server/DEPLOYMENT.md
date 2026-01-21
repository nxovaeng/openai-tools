# Xray Deployment 指南

本文档详细说明如何在各种环境中部署 Xray + Caddy 服务。

## 部署选项

### 1. Docker Compose（推荐）- Host 网络模式

**适用场景**：
- 需要快速部署的生产环境
- 同一服务器运行多个服务（Xray、Open WebUI 等）
- 容器化管理的优势

**特点**：
- ✅ Host 网络模式：无端口映射开销
- ✅ 易于添加其他服务（Open WebUI、其他代理等）
- ✅ 自动配置管理和重启

**启动步骤**：

```bash
# 复制示例环境文件
cp .env.example .env

# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f xray-allinone

# 重启服务
supervisorctl restart caddy
supervisorctl restart xray
```

**配置说明**：

Docker Compose 配置中的关键设置：

```yaml
services:
  xray-allinone:
    network_mode: host  # 使用宿主机网络，无 NAT 开销
    volumes:
      - caddy_conf_d:/etc/caddy/conf.d  # 自动生成配置挂载点
      - xray_data:/etc/xray             # Xray 配置持久化
```

**调用 API 生成配置**：

在容器运行后，调用 REST API 生成配置：

```bash
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "domains": ["proxy1.example.com", "proxy2.example.com"],
    "xray_port": 10000,
    "cdn_host": "cdn.example.com"
  }'
```

### 2. systemd 服务（系统部署）

**适用场景**：
- 需要与系统集成的生产环境
- 需要开机自启的服务
- 已有 Caddy/Xray 安装的系统

**安装步骤**：

```bash
# 1. 安装依赖
sudo apt-get install caddy xray python3-venv

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动 MCP 服务器（用于 AI 平台集成）
python server.py

# 或启动 REST API
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. 手工配置生成

**适用场景**：
- 学习和理解配置结构
- 自定义部署流程
- 测试环境

**生成配置**：

```bash
# 激活虚拟环境
source venv/bin/activate

# 生成配置到本地目录
python -c "
from config_generator import ConfigGenerator
gen = ConfigGenerator(
    domains=['proxy1.example.com', 'proxy2.example.com'],
    cdn_host='cdn.example.com'
)
# 输出配置
print('Xray Config:')
print(gen.generate_xray_json())
print()
print('Caddyfile (main):')
print(gen.generate_main_caddyfile())
print()
print('Caddyfile (xray-auto):')
print(gen.generate_caddyfile())
"
```

## Caddy 配置结构

### 文件组织

```
/etc/caddy/
├── Caddyfile              # 主配置文件（用户可编辑）
└── conf.d/
    ├── xray-auto.caddy    # 自动生成的 Xray 配置（勿手动编辑）
    └── custom-*.caddy     # 用户自定义配置（可选）
```

### 主 Caddyfile 示例

```caddyfile
{
    # 全局配置
    admin off
}

# 自动包含所有生成的配置
import /etc/caddy/conf.d/*.caddy

# 添加其他服务代理
# open-webui.example.com {
#     reverse_proxy localhost:8111
# }
```

### 自动生成的 xray-auto.caddy 示例

```caddyfile
# CDN Host: cdn.example.com

proxy1.example.com {
    # XHTTP 反向代理到 Xray
    @xhttp path /QOFehQyG5xZGhN0D*
    reverse_proxy @xhttp 127.0.0.1:10000 {
        flush_interval -1
        header_up X-Forwarded-For {remote_host}
    }
    
    # 伪装响应
    respond "Welcome to proxy1.example.com" 200
}

proxy2.example.com {
    # 相同的 XHTTP 配置
    @xhttp path /QOFehQyG5xZGhN0D*
    reverse_proxy @xhttp 127.0.0.1:10000 {
        flush_interval -1
        header_up X-Forwarded-For {remote_host}
    }
    
    respond "Welcome to proxy2.example.com" 200
}
```

## 添加其他服务代理

无需修改自动生成的 Xray 配置，直接在主 Caddyfile 或新建配置文件：

### 方式 1：编辑主 Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

添加 Open WebUI 代理：

```caddyfile
open-webui.example.com {
    reverse_proxy localhost:8111
}

# 其他服务
api.example.com {
    reverse_proxy localhost:3000
}
```

### 方式 2：新建配置文件

```bash
sudo nano /etc/caddy/conf.d/custom-services.caddy
```

内容：

```caddyfile
# 自定义服务代理
open-webui.example.com {
    reverse_proxy localhost:8111
}

# 更多服务...
```

### 重载配置

```bash
# Docker 容器中
docker exec xray-allinone supervisorctl reload caddy

# 系统服务
sudo systemctl reload caddy

# 或通过 supervisord（如果使用）
supervisorctl reload caddy
```

## Host 网络模式说明

### 优势

```
Host 网络模式架构：
┌─ Docker 容器（Host Network）
│  ├─ Xray: localhost:10000
│  └─ Caddy: localhost:80/443
│
├─ 宿主机服务
│  ├─ Open WebUI: localhost:8111
│  ├─ API 服务: localhost:3000
│  └─ 其他服务: localhost:XXXX
│
└─ 网络优势
   ✓ 无 NAT 转换开销
   ✓ 无端口映射复杂性
   ✓ 容器和主机服务直接通信
   ✓ 减少网络延迟
```

### 端口冲突检查

```bash
# 检查已使用的端口
sudo netstat -tlnp | grep LISTEN

# 确保这些端口可用
# 80 - HTTP
# 443 - HTTPS
# 10000 - Xray
```

### 特殊考虑事项

- **网络隔离**：Host 模式容器能访问宿主机的所有网络接口
- **安全**：确保服务只监听 localhost（127.0.0.1）而非 0.0.0.0
- **权限**：容器运行权限可能需要调整以绑定特权端口（<1024）

## 订阅链接生成

### 获取订阅链接

```bash
# 从容器内
docker exec xray-allinone python main.py get-subscription

# 或通过 API
curl -X GET "http://localhost:8000/subscription?format=v2ray" \
  -H "X-API-Key: your-api-key"
```

### 订阅链接格式

**V2ray 格式**：
```
vless://uuid@cdn.example.com:443?path=%2FQOFehQyG5xZGhN0D&security=tls&sni=proxy1.example.com&type=xhttp
```

**Clash 格式**：
```yaml
- name: "Xray VLESS"
  type: vless
  server: cdn.example.com
  port: 443
  uuid: your-uuid
  network: xhttp
  xhttp-opts:
    path: /QOFehQyG5xZGhN0D
  tls: true
  servername: proxy1.example.com
```

### 订阅参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `server` | 连接地址（CDN host 或域名） | `cdn.example.com` |
| `sni` | TLS SNI，用于 Caddy 路由 | `proxy1.example.com` |
| `path` | XHTTP 路径，自动生成 | `/QOFehQyG5xZGhN0D` |
| `uuid` | 客户端标识符 | UUID v4 |

## 故障排查

### 查看日志

**Docker 容器**：
```bash
# 查看所有日志
docker-compose logs -f

# 只看 Caddy 日志
docker-compose logs -f xray-allinone | grep caddy

# 只看 Xray 日志
docker-compose logs -f xray-allinone | grep xray
```

**系统服务**：
```bash
sudo journalctl -u caddy -f
sudo journalctl -u xray -f
```

### 常见问题

**1. Caddy 无法启动**

```bash
# 检查配置语法
sudo caddy validate --config /etc/caddy/Caddyfile

# 检查端口是否被占用
sudo netstat -tlnp | grep -E ':80|:443'
```

**2. Xray 连接失败**

```bash
# 检查 Xray 是否运行
ps aux | grep xray

# 检查监听端口
sudo netstat -tlnp | grep 10000
```

**3. 获取不到订阅链接**

```bash
# 检查 API 密钥
echo $API_KEY

# 查看服务状态
curl http://localhost:8000/health
```

## 性能优化建议

### 资源分配

```yaml
# Docker 容器资源限制
resources:
  limits:
    cpus: '2'
    memory: 1G
  reservations:
    cpus: '1'
    memory: 512M
```

### Caddy 优化

```caddyfile
{
    # 使用 fastcgi 缓存
    cache_file
    
    # 调整超时
    timeouts {
        read_body 5m
        read_header 10s
    }
}
```

### Xray 优化

在 Xray 配置中添加：

```json
{
  "policy": {
    "levels": {
      "0": {
        "uplinkOnly": 1
      }
    }
  }
}
```

## 监控和维护

### 自动化监控

使用 systemd 或 supervisord 的自动重启特性：

```ini
[program:xray]
command=/usr/local/bin/xray run -config /etc/xray/config.json
autostart=true
autorestart=true
startsecs=3
```

### 定期备份

```bash
# 备份 Caddy 配置
sudo cp -r /etc/caddy /backup/caddy-$(date +%Y%m%d)

# 备份 Xray 配置
sudo cp -r /etc/xray /backup/xray-$(date +%Y%m%d)
```

## 更新和升级

### 更新 Python 依赖

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 更新 Docker 镜像

```bash
# 重新构建镜像
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 更新系统包

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get upgrade caddy xray

# 重启服务
sudo systemctl restart caddy xray
```

# MCP 工具快速参考

本文档为使用 Xray Deployment MCP Server 的 AI 平台（Open WebUI、Dify 等）提供快速参考。

## MCP 工具列表

### 1. `check_environment()`

**用途**：检查系统环境状态

**参数**：无

**返回值**：
```json
{
  "distro": "ubuntu",
  "distro_version": "24.04",
  "caddy_installed": true,
  "caddy_version": "v2.7.4",
  "xray_installed": true,
  "xray_version": "v1.8.4"
}
```

**用法示例**：
```
检查我的系统是否已安装 Caddy 和 Xray
```

---

### 2. `install_dependencies()`

**用途**：自动安装缺失的依赖包

**参数**：无

**返回值**：
```json
{
  "distro": "ubuntu",
  "caddy": {
    "installed": true,
    "version": "v2.7.4",
    "status": "Already installed"
  },
  "xray": {
    "installed": true,
    "version": "v1.8.4",
    "status": "Already installed"
  }
}
```

**用法示例**：
```
安装缺失的 Caddy 和 Xray 包
```

**需求**：需要 root 权限

---

### 3. `generate_configs()`

**用途**：生成 Xray 和 Caddy 配置

**参数**：
| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `domains` | list | ✓ | 域名列表 | `["proxy1.example.com", "proxy2.example.com"]` |
| `xray_port` | int | ✗ | Xray 监听端口，默认 10000 | `10000` |
| `xray_path` | string | ✗ | XHTTP 路径，不指定则自动生成随机路径 | `"/secret-path"` 或留空自动生成 |
| `cdn_host` | string | ✗ | CDN 反向代理地址，用于订阅输出 | `"cdn.example.com"` |

**返回值**：
```json
{
  "success": true,
  "uuid": "a1e8f3c2-1234-5678-abcd-ef1234567890",
  "domains": ["proxy1.example.com", "proxy2.example.com"],
  "xray_path": "/QOFehQyG5xZGhN0D",  // 自动生成的随机路径
  "cdn_host": "cdn.example.com",
  "xray_config": { /* 完整的 Xray JSON 配置 */ },
  "caddyfile": "# 完整的 Caddyfile 内容"
}
```

**用法示例**：
```
为 proxy1.example.com 和 proxy2.example.com 生成配置，
使用 CDN 地址 cdn.example.com，自动生成安全路径
```

**关键说明**：
- `xray_path` 如果不指定，将使用 `secrets` 模块自动生成 16 字符的随机路径
- 自动生成的路径用于 XHTTP 伪装，增强隐蔽性
- 返回值包含实际生成的 `xray_path`

---

### 4. `deploy_configs()`

**用途**：部署生成的配置并重启服务

**参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `xray_config_path` | string | Xray 配置路径，默认 `/usr/local/etc/xray/config.json` |
| `caddy_config_path` | string | 主 Caddyfile 路径，默认 `/etc/caddy/Caddyfile` |

**返回值**：
```json
{
  "mode": "container",
  "xray": {
    "config_saved": "/etc/xray/config.json",
    "restart_success": true,
    "message": "xray restarted"
  },
  "caddy": {
    "main_config": "/etc/caddy/Caddyfile",
    "xray_auto_config": "/etc/caddy/conf.d/xray-auto.caddy",
    "restart_success": true,
    "message": "caddy restarted"
  },
  "note": "Services managed by supervisord in container"
}
```

**部署文件结构**：
- `/etc/xray/config.json` - Xray VLESS + XHTTP 配置
- `/etc/caddy/Caddyfile` - 主 Caddyfile（包含 import 指令）
- `/etc/caddy/conf.d/xray-auto.caddy` - 自动生成的 Xray 反代配置

**用法示例**：
```
部署之前生成的配置并重启 Xray 和 Caddy 服务
```

---

### 5. `get_subscription()`

**用途**：获取订阅链接

**参数**：
| 参数 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| `format` | string | 订阅格式 | `v2ray` 或 `clash` |

**返回值**（V2ray 格式）：
```
dmxlc3M6Ly9hMTQ3ZjlhOC0wOWNlLTQwNjEtODcyZS0wNjk5OTVjNzRiZGVAY2RuLmV4YW1wbGUuY29tOjQ0Mz9wYXRoPSUyRlFPRmVoUXlHNXhaR2hOMEQmc2VjdXJpdHk9dGxzJnNuaT1wcm94eTEuZXhhbXBsZS5jb20mdHlwZT14aHR0cCN4cmF5Lg==

# 解码后：
vless://a147f9a8-09ce-4061-872e-069995c74bde@cdn.example.com:443?path=%2FQOFehQyG5xZGhN0D&security=tls&sni=proxy1.example.com&type=xhttp#xray.
```

**返回值**（Clash 格式）：
```yaml
proxies:
  - name: "Xray VLESS"
    type: vless
    server: cdn.example.com
    port: 443
    uuid: a147f9a8-09ce-4061-872e-069995c74bde
    network: xhttp
    xhttp-opts:
      path: /QOFehQyG5xZGhN0D
    tls: true
    servername: proxy1.example.com
```

**用法示例**：
```
获取 v2ray 格式的订阅链接，用于配置客户端
```

---

### 6. `restart_services()`

**用途**：重启 Xray 和 Caddy 服务

**参数**：无

**返回值**：
```json
{
  "xray": {
    "success": true,
    "message": "xray restarted"
  },
  "caddy": {
    "success": true,
    "message": "caddy restarted"
  }
}
```

**用法示例**：
```
重启 Xray 和 Caddy 服务以应用配置更改
```

---

## 常见工作流

### 流程 1：从零开始部署

```
1. check_environment()
   ↓ 如果缺少依赖
2. install_dependencies()
   ↓
3. generate_configs(
     domains=["proxy1.example.com"],
     cdn_host="cdn.example.com"
   )
   ↓
4. deploy_configs()
   ↓
5. get_subscription(format="v2ray")
   ↓ 获得订阅链接供用户导入客户端
```

### 流程 2：添加新域名

```
1. generate_configs(
     domains=["proxy1.example.com", "proxy2.example.com"],
     cdn_host="cdn.example.com"
   )
   ↓
2. deploy_configs()
   ↓
3. restart_services()
   ↓
4. get_subscription(format="v2ray")
```

### 流程 3：更新 CDN 配置

```
1. generate_configs(
     domains=["proxy1.example.com"],
     cdn_host="new-cdn.example.com"
   )
   ↓
2. deploy_configs()
   ↓
3. get_subscription(format="v2ray")
```

---

## 参数说明详解

### `domains`（域名列表）

- **说明**：为 Caddy 创建虚拟主机的域名列表
- **每个域名**：
  - 获得自己的虚拟主机块
  - 获得自己的 SNI（用于 TLS 握手）
  - 生成独立的订阅节点
- **示例**：
  ```python
  domains = [
    "proxy1.example.com",  # SNI = proxy1.example.com
    "proxy2.example.com",  # SNI = proxy2.example.com
    "proxy3.example.com"   # SNI = proxy3.example.com
  ]
  ```

### `xray_path`（XHTTP 路径）

- **说明**：XHTTP 协议的伪装路径
- **自动生成**：如果不指定，使用 `secrets` 模块生成 16 字符随机路径
- **示例**：
  - 指定：`"/api/v1/data"` → 使用固定路径
  - 自动：留空 → 生成如 `/QOFehQyG5xZGhN0D` 的随机路径
- **用途**：在 HTTP/伪装时隐藏真实用途

### `cdn_host`（CDN 主机）

- **说明**：订阅链接中的连接地址
- **工作原理**：
  ```
  客户端连接到 cdn_host（如 cdn.example.com）
       ↓
  发送 SNI = 实际域名（如 proxy1.example.com）
       ↓
  Caddy 根据 SNI 路由到对应虚拟主机块
       ↓
  反代到 Xray（127.0.0.1:10000）
  ```
- **示例**：
  - 无 CDN：`get_subscription()` 返回连接到原始域名
  - 有 CDN：`get_subscription()` 返回连接到 CDN 地址

---

## 安全性说明

### API 密钥

所有 REST API 调用需要提供 API 密钥：

```bash
# Header 方式
curl -H "X-API-Key: your-api-key"

# Bearer Token 方式
curl -H "Authorization: Bearer your-api-key"
```

### xray_path 随机生成

```python
# 自动生成的路径示例
import secrets
path = "/" + secrets.token_urlsafe(16)
# 结果：/QOFehQyG5xZGhN0D（每次不同）
```

**优势**：
- 使用密码学安全的随机生成
- 路径不可预测
- 增强隐蔽性

---

## 返回值格式说明

### 成功响应

```json
{
  "success": true,
  "data": { /* 具体数据 */ }
}
```

### 错误响应

```json
{
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

---

## 与 AI 平台集成

### Open WebUI

在 Open WebUI 中添加 MCP 工具连接：

```
设置 → 管理员面板 → 工具 → 添加 MCP 服务器
SSH 地址或本地路径：ws://localhost:3000
```

### Dify

在 Dify 工作流中使用工具：

```
添加节点 → 工具 → MCP 工具
选择 xray-deploy 服务器 → 选择工具函数
```

---

## 调试技巧

### 查看详细日志

```bash
# 容器内
docker logs -f xray-allinone

# MCP 服务器
python server.py --debug

# API 日志
export DEBUG=1
python main.py
```

### 验证配置

```bash
# 验证 Xray 配置
xray test -c /etc/xray/config.json

# 验证 Caddyfile
caddy validate --config /etc/caddy/Caddyfile
```

### 测试连接

```bash
# 测试 Caddy 是否响应
curl -H "Host: proxy1.example.com" https://localhost -k

# 测试 Xray 是否响应
nc -zv localhost 10000
```

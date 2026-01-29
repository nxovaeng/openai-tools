# Nginx MCP 工具使用指南

通过自然语言与 AI 交互来管理 Nginx 配置。

## 🚀 快速开始

### 启动 MCP 服务器

```bash
cd xray-mcp-server
python nginx_mcp_server.py
```

### 在 AI 平台中使用

配置 MCP 客户端（如 Open WebUI、Dify）连接到此服务器，然后就可以通过自然语言交互了。

## 💬 自然语言交互示例

### 1. 添加 Xray 服务

**用户**：为 proxy.example.com 添加 Xray 服务

**AI 推理**：
- 识别意图：添加 Xray 服务
- 提取参数：domain = "proxy.example.com"
- 使用默认端口：10000
- 调用工具：`add_xray_service(domain="proxy.example.com")`

**结果**：
```json
{
  "success": true,
  "domain": "proxy.example.com",
  "xray_port": 10000,
  "xray_path": "/a7kRmQ2xJ9vN4pL",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "next_steps": [
    "申请 SSL 证书: certbot --nginx -d proxy.example.com",
    "测试配置: nginx -t",
    "重载 Nginx: nginx -s reload"
  ]
}
```

### 2. 添加 API 服务

**用户**：我想部署一个 API 服务到 api.example.com，后端运行在 3000 端口

**AI 推理**：
- 识别意图：添加 Web 服务
- 服务类型：API
- 提取参数：
  - domain = "api.example.com"
  - backend_port = 3000
  - service_type = "api"
- 调用工具：`add_web_service(domain="api.example.com", backend_port=3000, service_name="API Service", service_type="api")`

**结果**：
```json
{
  "success": true,
  "service_type": "api",
  "domain": "api.example.com",
  "backend_port": 3000,
  "nginx_config_path": "/etc/nginx/conf.d/api-service-api-example-com.conf"
}
```

### 3. 添加支持 WebSocket 的服务

**用户**：创建一个 WebSocket 服务配置，域名 ws.example.com，端口 5000

**AI 推理**：
- 识别意图：添加 Web 服务
- 特殊需求：WebSocket 支持
- 提取参数：
  - domain = "ws.example.com"
  - backend_port = 5000
  - enable_websocket = true
- 调用工具：`add_web_service(domain="ws.example.com", backend_port=5000, service_name="WebSocket Service", enable_websocket=true)`

### 4. 使用 CDN 的 Xray 服务

**用户**：部署 Xray 到 origin.example.com，通过 CDN cdn.example.com 访问

**AI 推理**：
- 识别意图：添加 Xray 服务 + CDN
- 提取参数：
  - domain = "origin.example.com"
  - cdn_host = "cdn.example.com"
- 调用工具：`add_xray_service(domain="origin.example.com", cdn_host="cdn.example.com")`

### 5. 添加静态网站

**用户**：为 blog.example.com 配置静态网站，文件在 /var/www/blog

**AI 推理**：
- 识别意图：添加静态网站
- 提取参数：
  - domain = "blog.example.com"
  - root_path = "/var/www/blog"
- 调用工具：`add_static_site(domain="blog.example.com", root_path="/var/www/blog")`

### 6. 查看所有服务

**用户**：列出所有配置的服务

**AI 推理**：
- 识别意图：查询服务列表
- 调用工具：`list_services()`

**结果**：
```json
{
  "success": true,
  "total": 3,
  "services": [
    "xray-proxy-example-com.conf",
    "api-service-api-example-com.conf",
    "web-app-app-example-com.conf"
  ]
}
```

### 7. 删除服务

**用户**：删除 api.example.com 的配置

**AI 推理**：
- 识别意图：删除服务
- 推断文件名：api-service-api-example-com.conf
- 调用工具：`remove_service(config_filename="api-service-api-example-com.conf")`

### 8. 测试和重载配置

**用户**：测试配置并重载 Nginx

**AI 推理**：
- 识别意图：测试 + 重载
- 调用工具序列：
  1. `test_nginx_config()`
  2. `reload_nginx()`

### 9. 申请 SSL 证书

**用户**：为 proxy.example.com 申请 SSL 证书，邮箱是 admin@example.com

**AI 推理**：
- 识别意图：申请证书
- 提取参数：
  - domain = "proxy.example.com"
  - email = "admin@example.com"
- 调用工具：`request_ssl_certificate(domain="proxy.example.com", email="admin@example.com")`

### 10. 获取订阅链接

**用户**：生成订阅链接

**AI 推理**：
- 识别意图：获取订阅
- 调用工具：`get_subscription()`

## 🎯 复杂场景示例

### 场景 1：完整部署流程

**用户**：我想部署一个完整的服务，包括 Xray 代理、API 服务和 Web 应用

**AI 推理和执行**：

```
1. 添加 Xray 服务
   add_xray_service(domain="proxy.example.com")

2. 添加 API 服务
   add_web_service(
     domain="api.example.com",
     backend_port=3000,
     service_name="API Service",
     service_type="api"
   )

3. 添加 Web 应用
   add_web_service(
     domain="app.example.com",
     backend_port=8080,
     service_name="Web Application",
     service_type="web"
   )

4. 测试配置
   test_nginx_config()

5. 申请证书
   request_ssl_certificate(domain="proxy.example.com")
   request_ssl_certificate(domain="api.example.com")
   request_ssl_certificate(domain="app.example.com")

6. 重载 Nginx
   reload_nginx()

7. 检查状态
   get_service_status()
```

### 场景 2：多域名 Xray 部署

**用户**：部署 3 个 Xray 服务，域名分别是 proxy1、proxy2、proxy3.example.com

**AI 推理和执行**：

```
for i, domain in enumerate(["proxy1.example.com", "proxy2.example.com", "proxy3.example.com"], 1):
    add_xray_service(
        domain=domain,
        xray_port=10000 + i
    )
```

### 场景 3：带自定义配置的服务

**用户**：添加一个管理面板到 admin.example.com，端口 9000，需要限制只允许内网访问，上传文件大小限制 100M

**AI 推理**：
- 识别需求：
  - 管理面板服务
  - 访问限制（需要自定义配置）
  - 大文件上传

**执行**：
```python
add_web_service(
    domain="admin.example.com",
    backend_port=9000,
    service_name="Admin Panel",
    service_type="admin",
    client_max_body_size="100M"
)

# 然后手动添加访问限制（AI 可以提示用户）
# 编辑 /etc/nginx/conf.d/admin-panel-admin-example-com.conf
# 在 location 块中添加：
# allow 192.168.1.0/24;
# deny all;
```

## 🛠️ 可用工具列表

| 工具 | 用途 | 自然语言示例 |
|------|------|--------------|
| `add_xray_service` | 添加 Xray 服务 | "添加代理服务" |
| `add_web_service` | 添加 Web/API 服务 | "部署 API 到..." |
| `add_static_site` | 添加静态网站 | "配置静态网站" |
| `list_services` | 列出所有服务 | "显示所有服务" |
| `remove_service` | 删除服务 | "删除...配置" |
| `get_subscription` | 获取订阅链接 | "生成订阅" |
| `test_nginx_config` | 测试配置 | "测试配置" |
| `reload_nginx` | 重载 Nginx | "重载 Nginx" |
| `get_service_status` | 查看服务状态 | "检查状态" |
| `request_ssl_certificate` | 申请证书 | "申请证书" |

## 📋 工具参数说明

### add_xray_service

```python
add_xray_service(
    domain: str,              # 必需：域名
    xray_port: int = 10000,   # 可选：端口
    xray_path: str = None,    # 可选：路径（自动生成）
    cdn_host: str = None,     # 可选：CDN 域名
    ssl_cert_path: str = None,# 可选：证书路径
    ssl_key_path: str = None  # 可选：私钥路径
)
```

### add_web_service

```python
add_web_service(
    domain: str,                    # 必需：域名
    backend_port: int,              # 必需：后端端口
    service_name: str,              # 必需：服务名称
    service_type: str = "web",      # 可选：服务类型
    enable_websocket: bool = False, # 可选：WebSocket
    enable_gzip: bool = True,       # 可选：Gzip
    client_max_body_size: str = "50M", # 可选：最大请求体
    ssl_cert_path: str = None,      # 可选：证书路径
    ssl_key_path: str = None        # 可选：私钥路径
)
```

### add_static_site

```python
add_static_site(
    domain: str,                      # 必需：域名
    root_path: str,                   # 必需：根目录
    index_files: list = None,         # 可选：索引文件
    enable_directory_listing: bool = False, # 可选：目录列表
    ssl_cert_path: str = None,        # 可选：证书路径
    ssl_key_path: str = None          # 可选：私钥路径
)
```

## 🤖 AI 推理模式

### 参数推断

AI 会根据上下文自动推断参数：

1. **域名识别**
   - "proxy.example.com" → domain
   - "为 api.example.com" → domain

2. **端口识别**
   - "端口 3000" → backend_port = 3000
   - "运行在 8080" → backend_port = 8080

3. **服务类型识别**
   - "API 服务" → service_type = "api"
   - "Web 应用" → service_type = "web"
   - "管理面板" → service_type = "admin"

4. **特性识别**
   - "支持 WebSocket" → enable_websocket = true
   - "大文件上传" → client_max_body_size = "100M"
   - "CDN" → cdn_host = ...

### 意图识别

AI 会识别用户意图并选择合适的工具：

| 用户表达 | 识别意图 | 调用工具 |
|----------|----------|----------|
| "添加/部署/创建 Xray" | 添加 Xray 服务 | `add_xray_service` |
| "添加/部署 API/Web" | 添加 Web 服务 | `add_web_service` |
| "配置静态网站" | 添加静态站点 | `add_static_site` |
| "列出/显示服务" | 查询服务 | `list_services` |
| "删除/移除配置" | 删除服务 | `remove_service` |
| "测试配置" | 测试 | `test_nginx_config` |
| "重载/刷新" | 重载 | `reload_nginx` |
| "申请证书" | 申请 SSL | `request_ssl_certificate` |

## 🎓 最佳实践

### 1. 清晰的表达

✅ 好的表达：
- "为 api.example.com 添加 API 服务，后端端口 3000"
- "部署 Xray 到 proxy.example.com，使用 CDN cdn.example.com"

❌ 模糊的表达：
- "添加一个服务"（缺少域名和类型）
- "配置代理"（不明确是什么类型的代理）

### 2. 分步操作

对于复杂任务，可以分步骤进行：

```
1. 先添加服务
2. 测试配置
3. 申请证书
4. 重载 Nginx
5. 检查状态
```

### 3. 验证结果

每次操作后，AI 会返回结果，包括：
- 成功/失败状态
- 生成的配置文件路径
- 后续步骤建议

## 🔧 故障排查

### 配置测试失败

**问题**：`test_nginx_config()` 返回失败

**解决**：
1. 查看错误信息
2. 检查配置文件语法
3. 使用 `list_services()` 查看所有配置
4. 必要时使用 `remove_service()` 删除有问题的配置

### 证书申请失败

**问题**：`request_ssl_certificate()` 失败

**解决**：
1. 确保域名 DNS 已正确解析
2. 确保 80 端口可访问（Let's Encrypt 验证需要）
3. 检查 Certbot 是否已安装
4. 查看详细错误信息

### 服务无法访问

**问题**：配置后服务无法访问

**解决**：
1. 使用 `get_service_status()` 检查服务状态
2. 使用 `test_nginx_config()` 验证配置
3. 检查后端服务是否运行
4. 检查防火墙规则

## 📚 相关文档

- [Nginx 部署指南](./NGINX_DEPLOYMENT.md)
- [快速开始](../QUICK_START.md)
- [项目 README](./README.md)

---

通过自然语言交互，配置 Nginx 变得简单直观！🎉

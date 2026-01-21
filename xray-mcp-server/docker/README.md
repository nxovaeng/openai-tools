# Xray Deployment API - All-in-One Docker

完整的容器化部署方案，包含 API + Xray + Caddy，使用 supervisord 管理。

## 快速开始

```bash
# 构建并启动
docker compose -f docker-compose.allinone.yaml up -d

# 查看日志
docker compose -f docker-compose.allinone.yaml logs -f
```

## 架构说明

```
┌─────────────────────────────────────┐
│   xray-allinone Container           │
│                                     │
│  ┌──────────────┐                  │
│  │ Supervisord  │                  │
│  └─────┬────────┘                  │
│        │                            │
│  ┌─────┴─────┐                     │
│  │ ├─ FastAPI:8000                │
│  │ ├─ Xray (managed)              │
│  │ └─ Caddy:443/80                │
│  └───────────┘                     │
└─────────────────────────────────────┘
```

## 使用流程

### 1. 部署代理

调用 API 端点：
```bash
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"domains": ["your.domain.com"]}'
```

### 2. 自动完成

- ✅ 生成 Xray 配置到 `/etc/xray/config.json`
- ✅ 生成 Caddy 配置到 `/etc/caddy/Caddyfile`
- ✅ 通过 supervisord 重启 Xray 和 Caddy
- ✅ 返回订阅链接

### 3. 获取订阅

```bash
curl http://localhost:8000/subscription?format=base64
```

## 服务管理

### 进入容器

```bash
docker exec -it xray-allinone bash
```

### 查看服务状态

```bash
supervisorctl status
```

### 手动重启服务

```bash
supervisorctl restart xray
supervi sorctl restart caddy
```

### 查看日志

```bash
# Xray 日志
tail -f /var/log/supervisor/xray.out.log

# Caddy 日志
tail -f /var/log/supervisor/caddy.out.log

# API 日志
tail -f /var/log/supervisor/fastapi.out.log
```

## 与其他模式对比

| 模式 | API | Xray | Caddy | 自动部署 | 适用场景 |
|------|-----|------|-------|----------|----------|
| **All-in-One** | ✅ 容器 | ✅ 容器 | ✅ 容器 | ✅ 是 | 完全容器化 |
| Host (venv) | ✅ 宿主机 | ✅ 宿主机 | ✅ 宿主机 | ✅ 是 | 裸机部署 |
| Docker (config) | ✅ 容器 | ❌ 需手动 | ❌ 需手动 | ❌ 否 | 仅生成配置 |

## 配置持久化

通过 Docker volumes 持久化：

```yaml
volumes:
  - xray_data:/etc/xray      # Xray 配置
  - caddy_data:/data         # Caddy 数据
  - caddy_config:/config     # Caddy 配置
```

## 注意事项

1. **域名解析**：确保域名已解析到服务器 IP
2. **端口映射**：容器 443/80 端口映射到宿主机
3. **API Key**：首次启动会自动生成，保存在 `.env`
4. **证书申请**：Caddy 自动申请 Let's Encrypt 证书

## 故障排查

### Xray 未启动

```bash
# 查看错误日志
docker exec xray-allinone cat /var/log/supervisor/xray.err.log

# 检查配置文件
docker exec xray-allinone cat /etc/xray/config.json
```

### Caddy 未启动

```bash
# 查看错误日志
docker exec xray-allinone cat /var/log/supervisor/caddy.err.log

# 测试配置
docker exec xray-allinone caddy validate --config /etc/caddy/Caddyfile
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DEPLOYMENT_MODE | container | 部署模式 |
| TZ | Asia/Shanghai | 时区 |
| API_KEY | (自动生成) | API 密钥 |

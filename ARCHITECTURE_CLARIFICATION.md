# Xray MCP Server 架构澄清

## 核心设计理解

### 1. Domain - Caddy 反代和 SNI 路由

**作用**：指定 Caddy 虚拟主机和 TLS SNI 值

**示例**：`domains=["proxy1.example.com", "proxy2.example.com"]`

**生成的配置**：
```caddyfile
# 每个 domain 一个虚拟主机
proxy1.example.com {
    @xhttp path /a7kRmQ2xJ9vN4pL*
    reverse_proxy @xhttp 127.0.0.1:10000 { ... }
}

proxy2.example.com {
    @xhttp path /a7kRmQ2xJ9vN4pL*
    reverse_proxy @xhttp 127.0.0.1:10000 { ... }
}
```

**SNI 行为**：
- 每个 domain 自己的 SNI = domain 本身
- `proxy1.example.com` 的 SNI = `proxy1.example.com`
- `proxy2.example.com` 的 SNI = `proxy2.example.com`
- 用于 Caddy 识别不同的虚拟主机

---

### 2. CDN Host - 订阅输出的替换

**作用**：在生成订阅链接时，替换 domain 作为连接地址

**场景**：
```
用户的原始 domain: proxy.example.com
用户的 CDN 反代地址: cdn.example.com
```

**生成的订阅**：
```
vless://uuid@cdn.example.com:443?type=xhttp&security=tls&path=%2Fa7k...&sni=proxy.example.com
```

**意义**：
- 客户端连接到：`cdn.example.com`（CDN 反代地址）
- SNI 发送：`proxy.example.com`（原始 domain，用于 Caddy 路由）
- Caddy 根据 SNI 识别虚拟主机 → 反代到 Xray

**流程图**：
```
┌─────────────────────┐
│  客户端连接          │
│ cdn.example.com:443 │  ← CDN 反代域名
└──────────┬──────────┘
           │
           │ SNI: proxy.example.com
           ↓
┌─────────────────────┐
│   Caddy (反向代理)    │
│ proxy.example.com   │  ← 原始 domain（虚拟主机）
│  ↓ reverse_proxy   │
└──────────┬──────────┘
           │
           ↓ 127.0.0.1:10000
    ┌──────────────┐
    │   Xray VLESS │
    └──────────────┘
```

---

### 3. 多 Domain - 多个入口点

**作用**：为不同的 domain 生成不同的 VLESS 节点

**场景**：
```python
domains=["proxy1.example.com", "proxy2.example.com"]
```

**生成的结果**：

**Caddy 配置**：
```caddyfile
proxy1.example.com {
    ...
}

proxy2.example.com {
    ...
}
```

**订阅节点**（多个）：
```
节点 1: vless://uuid@proxy1.example.com:443?...&sni=proxy1.example.com
节点 2: vless://uuid@proxy2.example.com:443?...&sni=proxy2.example.com
```

**使用场景**：
- 为同一个服务提供多个入口
- 增加可用性和分散流量
- 各 domain 独立管理

---

### 4. 多 Domain + CDN Host 组合

**场景**：
```python
domains=["proxy1.example.com", "proxy2.example.com"]
cdn_host="cdn.example.com"
```

**生成的结果**：

**Caddy 配置**：
```caddyfile
proxy1.example.com { ... }
proxy2.example.com { ... }
```

**订阅节点**（都用 CDN host）：
```
节点 1: vless://uuid@cdn.example.com:443?...&sni=proxy1.example.com
节点 2: vless://uuid@cdn.example.com:443?...&sni=proxy2.example.com
```

**意义**：
- 两个 domain 都通过同一个 CDN 反代访问
- 但用不同的 SNI 让 Caddy 区分虚拟主机
- 可实现多入口共享一个 CDN

---

## 代码实现

### SubscriptionGenerator - 节点生成

```python
for domain in domains:
    VlessNode(
        uuid=uuid,
        domain=cdn_host or domain,  # 订阅链接中的连接地址
        port=port,
        path=path,
        sni=domain  # Caddy 路由标识
    )
```

**逻辑**：
1. `domain` 参数 → 用作 SNI（Caddy 虚拟主机标识）
2. `cdn_host` 参数 → 如果提供，替换 `domain` 作为连接地址
3. 如果未提供 `cdn_host`，则连接地址 = domain

---

## 配置示例

### 示例 1: 单 Domain

```python
generate_configs(
    domains=["proxy.example.com"]
)
```

**Caddy**：
```caddyfile
proxy.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}
```

**订阅**：
```
vless://uuid@proxy.example.com:443?...&sni=proxy.example.com
```

---

### 示例 2: 多 Domain

```python
generate_configs(
    domains=["api.example.com", "web.example.com"]
)
```

**Caddy**：
```caddyfile
api.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}

web.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}
```

**订阅**：
```
vless://uuid@api.example.com:443?...&sni=api.example.com
vless://uuid@web.example.com:443?...&sni=web.example.com
```

---

### 示例 3: 单 Domain + CDN

```python
generate_configs(
    domains=["proxy.example.com"],
    cdn_host="cdn-global.com"
)
```

**Caddy**：
```caddyfile
proxy.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}
```

**订阅**：
```
vless://uuid@cdn-global.com:443?...&sni=proxy.example.com
          ↑                                    ↑
       CDN 域名                          原始 domain
```

---

### 示例 4: 多 Domain + CDN

```python
generate_configs(
    domains=["proxy1.example.com", "proxy2.example.com"],
    cdn_host="cdn.example.com"
)
```

**Caddy**：
```caddyfile
proxy1.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}

proxy2.example.com {
    reverse_proxy /a7k* 127.0.0.1:10000
}
```

**订阅**：
```
vless://uuid@cdn.example.com:443?...&sni=proxy1.example.com
vless://uuid@cdn.example.com:443?...&sni=proxy2.example.com
```

**优势**：多入口共享 CDN，通过 SNI 区分

---

## 关键规则

| 参数 | 作用 | 示例 |
|------|------|------|
| `domains` | Caddy 虚拟主机 + 节点 SNI | `["proxy.example.com"]` |
| `cdn_host` | 替换订阅中的连接地址 | `"cdn.example.com"` |
| `xray_path` | XHTTP 路径（自动生成） | 自动 `/a7kRm...` |

---

## 部署验证清单

- [x] Domain 作为 Caddy 虚拟主机配置
- [x] 每个 domain 自己的 SNI
- [x] CDN host 替换订阅中的连接地址
- [x] 多 domain 生成多个节点
- [x] xray_path 自动随机生成
- [x] FastAPI docs 禁用
- [x] SNI 不需要用户指定参数

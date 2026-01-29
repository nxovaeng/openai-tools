# Xray + Nginx OpenAPI Server

**OpenAPI Tool Server** 用于自动化 Xray + Nginx 部署，支持 XHTTP 协议。

**🎉 完全兼容 [Open WebUI OpenAPI Servers](https://github.com/open-webui/openapi-servers)！**

## 📁 项目结构

```
xray-nginx-openapi/
├── src/                          # 核心服务代码
│   ├── core/                     # 核心功能模块
│   │   ├── config_generator.py   # Xray 配置生成
│   │   ├── nginx_generator.py    # Nginx 配置生成
│   │   ├── subscription.py       # 订阅服务
│   │   └── installer.py          # 依赖安装
│   ├── models/                   # 数据模型
│   │   └── models.py
│   └── api/                      # API 接口
│       ├── openapi_server.py     # OpenAPI 服务器 ⭐
│       ├── mcp_server.py         # MCP 服务器
│       ├── auth.py               # 认证
│       └── config.py             # 配置
├── scripts/                      # 脚本工具
│   ├── start_openapi.sh          # 启动 OpenAPI 服务器 ⭐
│   ├── start_mcp.sh              # 启动 MCP 服务器
│   └── test_api.py               # API 测试
├── config/                       # 配置文件
│   └── .env.example              # 环境变量示例
├── docker/                       # Docker 相关
│   ├── docker-compose.yml        # 标准部署
│   └── docker-compose.openapi.yml # OpenAPI 部署
├── examples/                     # 示例文件
│   ├── openwebui-config.json     # Open WebUI 配置
│   └── mcp-config.json           # MCP 配置
├── docs/                         # 文档
│   ├── QUICKSTART.md             # 快速开始 ⭐
│   ├── OPENAPI_INTEGRATION.md    # OpenAPI 集成
│   ├── MCP_GUIDE.md              # MCP 指南
│   └── DEPLOYMENT.md             # 部署指南
└── tests/                        # 测试文件
```

## ✨ 特性

- ✅ **OpenAPI 标准** - 完全兼容 OpenAPI 3.0 规范
- ✅ **Open WebUI 集成** - 一键添加到 Open WebUI
- ✅ **自动文档** - 访问 `/docs` 查看交互式 API 文档
- ✅ **XHTTP 协议** - Xray 最新协议，packet-up 模式
- ✅ **Nginx 反向代理** - 统一 TLS 管理，模块化配置
- ✅ **自动配置生成** - 为 Xray + Nginx 生成配置
- ✅ **订阅链接** - 生成 Base64 编码的 VLESS URI
- ✅ **多域名支持** - 每个服务独立配置文件
- ✅ **RESTful API** - 标准 HTTP/HTTPS 通信

## 🚀 快速开始

### 1. 启动 OpenAPI 服务器

```bash
# 克隆项目
git clone <your-repo-url>
cd xray-nginx-openapi

# 启动服务器
./scripts/start_openapi.sh
```

服务器将在 `http://localhost:8000` 启动。

### 2. 查看 API 文档

在浏览器中打开：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 3. 集成到 Open WebUI

1. 打开 Open WebUI
2. 进入 **⚙️ Settings** → **Tools**
3. 点击 **➕ Add Tool Server**
4. 输入服务器 URL: `http://localhost:8000`
5. 输入 API Key（在 `config/.env` 中配置）
6. 点击 **Save**

### 4. 开始使用

在 Open WebUI 中与 AI 对话：

```
User: 为 proxy.example.com 添加一个 Xray 服务

AI: [自动调用 API 完成配置]
    ✅ 已成功添加 Xray 服务
    - 域名: proxy.example.com
    - UUID: xxx-xxx-xxx
    - 路径: /a7kRmQ2xJ9vN4pL
```

## 📚 文档

- 🚀 [快速开始](./docs/QUICKSTART.md) - 5 分钟快速入门
- 📖 [OpenAPI 集成](./docs/OPENAPI_INTEGRATION.md) - Open WebUI 集成指南
- 🔧 [MCP 指南](./docs/MCP_GUIDE.md) - MCP 协议使用指南
- 🐳 [部署指南](./docs/DEPLOYMENT.md) - 生产环境部署

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

### 使用 curl

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


## 🔒 安全配置

在 `config/.env` 文件中配置：

```bash
# 启用认证
REQUIRE_AUTH=true

# 设置 API Key
API_KEY=your-secure-api-key-here
```

生成安全的 API Key：

```bash
openssl rand -hex 32
```

## 🎯 特性对比

| 特性 | MCP Server | OpenAPI Server |
|------|-----------|----------------|
| 协议 | MCP 专有协议 | 标准 HTTP/REST |
| 文档 | 手动编写 | 自动生成 ✅ |
| 集成 | 需要 MCP 客户端 | 任何 HTTP 客户端 |
| Open WebUI | 需要桥接 | 原生支持 ✅ |
| 部署 | 复杂 | 简单 ✅ |

## 🧪 测试

```bash
# 运行 API 测试
python scripts/test_api.py

# 运行所有测试
python -m pytest tests/
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Open WebUI](https://github.com/open-webui/open-webui)
- [OpenAPI Servers](https://github.com/open-webui/openapi-servers)
- [Xray-core](https://github.com/XTLS/Xray-core)
- [Nginx](https://nginx.org/)

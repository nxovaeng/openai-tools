# 项目概览

## 📦 Xray + Nginx OpenAPI Server

一个完全兼容 Open WebUI 的 OpenAPI 工具服务器，用于自动化 Xray + Nginx 部署和配置管理。

## 🎯 核心功能

- ✅ **OpenAPI 标准** - 完全兼容 OpenAPI 3.0 规范
- ✅ **Open WebUI 集成** - 原生支持，无需桥接
- ✅ **Xray 部署** - VLESS + XHTTP 协议自动配置
- ✅ **Nginx 管理** - 反向代理配置自动生成
- ✅ **订阅服务** - 自动生成客户端订阅链接
- ✅ **多域名支持** - 独立配置文件管理

## 📁 项目结构

```
xray-nginx-openapi/
│
├── src/                          # 源代码
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
│
├── scripts/                      # 脚本工具
│   ├── start_openapi.sh          # 启动 OpenAPI 服务器 ⭐
│   ├── start_mcp.sh              # 启动 MCP 服务器
│   ├── test_api.py               # API 测试
│   └── verify_structure.sh       # 结构验证
│
├── config/                       # 配置文件
│   └── .env.example              # 环境变量示例
│
├── docker/                       # Docker 相关
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.openapi.yml
│
├── examples/                     # 示例文件
│   ├── api-examples.py           # API 使用示例 ⭐
│   ├── openwebui-config.json     # Open WebUI 配置
│   └── mcp-config.json           # MCP 配置
│
├── docs/                         # 文档
│   ├── QUICKSTART.md             # 快速开始 ⭐
│   ├── OPENAPI_INTEGRATION.md    # OpenAPI 集成
│   ├── MCP_GUIDE.md              # MCP 指南
│   ├── DEPLOYMENT.md             # 部署指南
│   ├── CHANGELOG.md              # 更新日志
│   └── PROJECT_STRUCTURE.md      # 项目结构
│
├── tests/                        # 测试文件
│   ├── test_openapi.py
│   ├── test_mcp.py
│   └── test_core.py
│
├── README.md                     # 项目主文档
├── requirements.txt              # Python 依赖
├── .gitignore                    # Git 忽略规则
├── MIGRATION_GUIDE.md            # 迁移指南
└── FINAL_SUMMARY.md              # 完成总结
```

## 🚀 快速开始

### 1. 启动服务器

```bash
./scripts/start_openapi.sh
```

### 2. 访问文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 集成 Open WebUI

1. 打开 Open WebUI 设置
2. 添加工具服务器: `http://localhost:8000`
3. 输入 API Key
4. 开始使用！

## 📡 主要 API 端点

### Nginx 配置

- `POST /nginx/xray` - 添加 Xray 服务
- `POST /nginx/web` - 添加 Web 服务
- `GET /nginx/services` - 列出服务
- `DELETE /nginx/services/{name}` - 删除服务
- `GET /nginx/test` - 测试配置
- `POST /nginx/reload` - 重载 Nginx

### 订阅和监控

- `GET /subscription` - 获取订阅链接
- `GET /status` - 服务状态

## 💡 使用场景

### 场景 1: 在 Open WebUI 中使用

```
User: 为 proxy.example.com 添加 Xray 服务
AI: ✅ 服务已添加，UUID: xxx-xxx-xxx
```

### 场景 2: 使用 API

```bash
curl -X POST http://localhost:8000/nginx/xray \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"domain": "proxy.example.com"}'
```

### 场景 3: Python 集成

```python
import requests

response = requests.post(
    "http://localhost:8000/nginx/xray",
    json={"domain": "proxy.example.com"},
    headers={"X-API-Key": "your-key"}
)
```

## 📚 文档导航

### 新手入门

1. [README.md](./README.md) - 项目介绍
2. [docs/QUICKSTART.md](./docs/QUICKSTART.md) - 5 分钟快速开始
3. [docs/OPENAPI_INTEGRATION.md](./docs/OPENAPI_INTEGRATION.md) - Open WebUI 集成


## 🎯 核心特性

### OpenAPI 标准化

- ✅ 标准 RESTful API
- ✅ 自动生成文档
- ✅ OpenAPI 3.0 规范
- ✅ 兼容任何 HTTP 客户端

### 功能完整

- ✅ Xray 配置生成
- ✅ Nginx 反向代理
- ✅ SSL/TLS 管理
- ✅ 订阅链接生成
- ✅ 服务监控

### 易于使用

- ✅ 一键启动脚本
- ✅ 交互式文档
- ✅ 丰富的示例
- ✅ 完整的文档

### 生产就绪

- ✅ Docker 支持
- ✅ 认证机制
- ✅ 错误处理
- ✅ 日志记录

## 🔧 技术栈

- **后端**: FastAPI (OpenAPI), FastMCP (MCP)
- **配置**: Xray, Nginx
- **文档**: OpenAPI/Swagger, Markdown

## 📊 版本信息

- **当前版本**: 2.0.0
- **发布日期**: 2026-01-28
- **状态**: ✅ 生产就绪

## 🆘 获取帮助

### 文档

- 查看 [docs/](./docs/) 目录
- 阅读 [README.md](./README.md)

### 示例

- 运行 `python examples/api-examples.py`
- 查看 [examples/](./examples/) 目录

### 测试

- 运行 `python scripts/test_api.py`
- 访问 http://localhost:8000/docs

## 📄 许可证

MIT License

---

**开始使用**: `./scripts/start_openapi.sh`

**文档**: http://localhost:8000/docs

**项目**: https://github.com/your-repo/xray-nginx-openapi

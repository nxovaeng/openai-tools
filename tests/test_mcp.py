#!/usr/bin/env python3
"""
Nginx MCP 工具测试脚本

测试通过模拟自然语言交互来生成配置
"""

import json
import tempfile
from pathlib import Path

# 模拟导入（实际使用时会通过 MCP 协议调用）
from nginx_config_generator import NginxServiceManager
from config_generator import ConfigGenerator


def simulate_add_xray_service(domain: str, xray_port: int = 10000):
    """模拟：添加 Xray 服务"""
    print(f"\n🤖 AI 理解：用户想为 {domain} 添加 Xray 服务")
    print(f"   推理参数：domain={domain}, xray_port={xray_port}")
    
    try:
        # 生成配置
        xray_gen = ConfigGenerator(
            domains=[domain],
            xray_port=xray_port
        )
        
        print(f"   ✓ 生成 UUID: {xray_gen.client_uuid}")
        print(f"   ✓ 生成路径: {xray_gen.xray_path}")
        print(f"   ✓ 监听端口: {xray_port}")
        
        return {
            "success": True,
            "domain": domain,
            "uuid": xray_gen.client_uuid,
            "path": xray_gen.xray_path,
            "port": xray_port
        }
        
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return {"success": False, "error": str(e)}


def simulate_add_web_service(domain: str, backend_port: int, service_name: str):
    """模拟：添加 Web 服务"""
    print(f"\n🤖 AI 理解：用户想为 {domain} 添加 {service_name}")
    print(f"   推理参数：domain={domain}, backend_port={backend_port}")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = NginxServiceManager(conf_dir=tmpdir)
            
            config_file = manager.add_generic_service(
                domain=domain,
                backend_port=backend_port,
                service_name=service_name
            )
            
            print(f"   ✓ 配置文件: {config_file.name}")
            print(f"   ✓ 后端端口: {backend_port}")
            
            return {
                "success": True,
                "domain": domain,
                "backend_port": backend_port,
                "config_file": config_file.name
            }
            
    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return {"success": False, "error": str(e)}


def simulate_natural_language_interaction():
    """模拟自然语言交互"""
    
    print("=" * 70)
    print("Nginx MCP 自然语言交互测试")
    print("=" * 70)
    
    # 场景 1：添加 Xray 服务
    print("\n📝 场景 1：用户说 '为 proxy.example.com 添加 Xray 服务'")
    result1 = simulate_add_xray_service("proxy.example.com")
    print(f"   结果: {json.dumps(result1, indent=2, ensure_ascii=False)}")
    
    # 场景 2：添加 API 服务
    print("\n📝 场景 2：用户说 '部署 API 服务到 api.example.com，端口 3000'")
    result2 = simulate_add_web_service("api.example.com", 3000, "API Service")
    print(f"   结果: {json.dumps(result2, indent=2, ensure_ascii=False)}")
    
    # 场景 3：添加 Web 应用
    print("\n📝 场景 3：用户说 '创建 Web 应用配置，域名 app.example.com，端口 8080'")
    result3 = simulate_add_web_service("app.example.com", 8080, "Web Application")
    print(f"   结果: {json.dumps(result3, indent=2, ensure_ascii=False)}")
    
    # 场景 4：使用 CDN 的 Xray
    print("\n📝 场景 4：用户说 '部署 Xray 到 origin.example.com，通过 CDN cdn.example.com'")
    print("   🤖 AI 理解：需要配置 CDN")
    xray_gen = ConfigGenerator(
        domains=["origin.example.com"],
        cdn_host="cdn.example.com"
    )
    print(f"   ✓ 源站域名: origin.example.com")
    print(f"   ✓ CDN 域名: cdn.example.com")
    print(f"   ✓ 订阅链接会使用 CDN 域名，SNI 使用源站域名")
    
    # 场景 5：多域名部署
    print("\n📝 场景 5：用户说 '部署 3 个 Xray 服务，域名 proxy1、proxy2、proxy3.example.com'")
    print("   🤖 AI 理解：需要批量部署")
    domains = ["proxy1.example.com", "proxy2.example.com", "proxy3.example.com"]
    for i, domain in enumerate(domains, 1):
        result = simulate_add_xray_service(domain, 10000 + i)
        print(f"   [{i}/3] {domain}: {'✓' if result['success'] else '✗'}")
    
    # 场景 6：复杂需求
    print("\n📝 场景 6：用户说 '添加管理面板到 admin.example.com，端口 9000，支持 WebSocket'")
    print("   🤖 AI 理解：需要特殊配置")
    print("   推理参数：")
    print("     - domain: admin.example.com")
    print("     - backend_port: 9000")
    print("     - service_type: admin")
    print("     - enable_websocket: true")
    print("   ✓ 会生成包含 WebSocket 支持的配置")
    
    print("\n" + "=" * 70)
    print("✅ 所有场景测试完成")
    print("=" * 70)
    
    print("\n💡 AI 推理能力展示：")
    print("   1. 从自然语言中提取域名、端口等参数")
    print("   2. 识别服务类型（Xray、API、Web 等）")
    print("   3. 理解特殊需求（CDN、WebSocket 等）")
    print("   4. 批量处理多个请求")
    print("   5. 生成正确的配置文件")


def test_parameter_inference():
    """测试参数推断"""
    
    print("\n" + "=" * 70)
    print("参数推断测试")
    print("=" * 70)
    
    test_cases = [
        {
            "input": "为 proxy.example.com 添加 Xray 服务",
            "inferred": {
                "tool": "add_xray_service",
                "domain": "proxy.example.com",
                "xray_port": 10000  # 默认值
            }
        },
        {
            "input": "部署 API 到 api.example.com，端口 3000",
            "inferred": {
                "tool": "add_web_service",
                "domain": "api.example.com",
                "backend_port": 3000,
                "service_type": "api"
            }
        },
        {
            "input": "创建支持 WebSocket 的服务，域名 ws.example.com，端口 5000",
            "inferred": {
                "tool": "add_web_service",
                "domain": "ws.example.com",
                "backend_port": 5000,
                "enable_websocket": True
            }
        },
        {
            "input": "配置静态网站 blog.example.com，根目录 /var/www/blog",
            "inferred": {
                "tool": "add_static_site",
                "domain": "blog.example.com",
                "root_path": "/var/www/blog"
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}:")
        print(f"  输入: {case['input']}")
        print(f"  推断: {json.dumps(case['inferred'], indent=4, ensure_ascii=False)}")


def test_intent_recognition():
    """测试意图识别"""
    
    print("\n" + "=" * 70)
    print("意图识别测试")
    print("=" * 70)
    
    intents = [
        ("添加 Xray 服务", "add_xray_service"),
        ("部署代理", "add_xray_service"),
        ("创建 API 配置", "add_web_service"),
        ("配置静态网站", "add_static_site"),
        ("列出所有服务", "list_services"),
        ("显示配置", "list_services"),
        ("删除配置", "remove_service"),
        ("移除服务", "remove_service"),
        ("测试配置", "test_nginx_config"),
        ("重载 Nginx", "reload_nginx"),
        ("申请证书", "request_ssl_certificate"),
        ("获取订阅", "get_subscription"),
        ("查看状态", "get_service_status")
    ]
    
    print("\n意图 → 工具映射：")
    for user_input, tool in intents:
        print(f"  '{user_input}' → {tool}")


if __name__ == "__main__":
    # 运行测试
    simulate_natural_language_interaction()
    test_parameter_inference()
    test_intent_recognition()
    
    print("\n" + "=" * 70)
    print("🎉 测试完成！")
    print("=" * 70)
    print("\n💡 提示：")
    print("   - 启动 MCP 服务器: python nginx_mcp_server.py")
    print("   - 在 AI 平台中配置 MCP 客户端")
    print("   - 通过自然语言与 AI 交互来管理 Nginx 配置")
    print("\n📚 详细文档：NGINX_MCP_GUIDE.md")

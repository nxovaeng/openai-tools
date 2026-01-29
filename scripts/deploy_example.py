#!/usr/bin/env python3
"""
Xray + Nginx 部署示例脚本

演示如何使用配置生成器部署多个服务
"""

from config_generator import ConfigGenerator
from nginx_config_generator import NginxServiceManager
import subprocess
import sys


def deploy_xray_services():
    """部署多个 Xray 服务"""
    
    print("=" * 60)
    print("Xray + Nginx 部署示例")
    print("=" * 60)
    
    # 配置域名列表
    domains = [
        "proxy1.example.com",
        "proxy2.example.com",
        "proxy3.example.com"
    ]
    
    # 创建 Nginx 管理器
    nginx_mgr = NginxServiceManager()
    
    print("\n📦 开始部署 Xray 服务...")
    
    for i, domain in enumerate(domains, start=1):
        print(f"\n[{i}/{len(domains)}] 部署 {domain}")
        
        # 生成 Xray 配置
        xray_port = 10000 + i
        xray_gen = ConfigGenerator(
            domains=[domain],
            xray_port=xray_port
        )
        
        print(f"  ✓ Xray 端口: {xray_port}")
        print(f"  ✓ Xray 路径: {xray_gen.xray_path}")
        print(f"  ✓ UUID: {xray_gen.client_uuid}")
        
        # 保存 Xray 配置
        try:
            xray_config_path = xray_gen.save_xray_config()
            print(f"  ✓ Xray 配置已保存: {xray_config_path}")
        except Exception as e:
            print(f"  ✗ 保存 Xray 配置失败: {e}")
            continue
        
        # 生成 Nginx 配置
        try:
            nginx_config_path = nginx_mgr.add_xray_service(
                domain=domain,
                xray_port=xray_port,
                xray_path=xray_gen.xray_path
            )
            print(f"  ✓ Nginx 配置已保存: {nginx_config_path}")
        except Exception as e:
            print(f"  ✗ 保存 Nginx 配置失败: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ 所有服务配置已生成")
    print("=" * 60)
    
    # 列出所有配置文件
    print("\n📋 生成的配置文件：")
    for config_file in nginx_mgr.list_services():
        print(f"  - {config_file}")
    
    # 提示后续步骤
    print("\n📝 后续步骤：")
    print("  1. 申请 SSL 证书：")
    for domain in domains:
        print(f"     certbot --nginx -d {domain}")
    print("\n  2. 测试 Nginx 配置：")
    print("     nginx -t")
    print("\n  3. 重载 Nginx：")
    print("     nginx -s reload")
    print("\n  4. 启动 Xray：")
    print("     systemctl start xray")
    print("     systemctl enable xray")


def deploy_mixed_services():
    """部署混合服务（Xray + 其他应用）"""
    
    print("\n" + "=" * 60)
    print("混合服务部署示例")
    print("=" * 60)
    
    nginx_mgr = NginxServiceManager()
    
    # 部署 Xray 服务
    print("\n📦 部署 Xray 服务...")
    xray_gen = ConfigGenerator(
        domains=["proxy.example.com"],
        xray_port=10000
    )
    xray_gen.save_xray_config()
    nginx_mgr.add_xray_service(
        domain="proxy.example.com",
        xray_port=10000,
        xray_path=xray_gen.xray_path
    )
    print("  ✓ Xray 服务配置完成")
    
    # 部署 API 服务
    print("\n📦 部署 API 服务...")
    nginx_mgr.add_generic_service(
        domain="api.example.com",
        backend_port=3000,
        service_name="API Service"
    )
    print("  ✓ API 服务配置完成")
    
    # 部署 Web 应用
    print("\n📦 部署 Web 应用...")
    nginx_mgr.add_generic_service(
        domain="app.example.com",
        backend_port=8080,
        service_name="Web Application"
    )
    print("  ✓ Web 应用配置完成")
    
    # 部署管理面板
    print("\n📦 部署管理面板...")
    nginx_mgr.add_generic_service(
        domain="admin.example.com",
        backend_port=9000,
        service_name="Admin Panel",
        extra_config="""
        # 限制访问
        allow 192.168.1.0/24;
        deny all;
        """
    )
    print("  ✓ 管理面板配置完成")
    
    print("\n" + "=" * 60)
    print("✅ 混合服务配置已生成")
    print("=" * 60)
    
    print("\n📋 生成的配置文件：")
    for config_file in nginx_mgr.list_services():
        print(f"  - {config_file}")


def show_config_example():
    """显示配置示例"""
    
    print("\n" + "=" * 60)
    print("配置示例")
    print("=" * 60)
    
    # 生成示例配置
    xray_gen = ConfigGenerator(
        domains=["proxy.example.com"],
        xray_port=10000
    )
    
    print("\n📄 Xray 配置 (config.json):")
    print("-" * 60)
    print(xray_gen.generate_xray_json())
    
    print("\n📄 Nginx 配置:")
    print("-" * 60)
    from nginx_config_generator import generate_xray_config
    print(generate_xray_config(
        domain="proxy.example.com",
        xray_port=10000,
        xray_path=xray_gen.xray_path
    ))


def main():
    """主函数"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "deploy":
            deploy_xray_services()
        elif command == "mixed":
            deploy_mixed_services()
        elif command == "show":
            show_config_example()
        else:
            print(f"未知命令: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """打印使用说明"""
    print("""
使用方法:
    python deploy_example.py <command>

命令:
    deploy  - 部署多个 Xray 服务
    mixed   - 部署混合服务（Xray + 其他应用）
    show    - 显示配置示例

示例:
    python deploy_example.py deploy
    python deploy_example.py mixed
    python deploy_example.py show
""")


if __name__ == "__main__":
    main()

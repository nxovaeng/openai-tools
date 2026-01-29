#!/usr/bin/env python3
"""
配置生成器测试脚本

测试 Xray 和 Nginx 配置生成功能
"""

import json
import tempfile
from pathlib import Path
from config_generator import ConfigGenerator, generate_random_path
from nginx_config_generator import (
    NginxServiceManager,
    generate_xray_config,
    generate_service_config,
    generate_main_nginx_conf
)


def test_random_path():
    """测试随机路径生成"""
    print("测试 1: 随机路径生成")
    path = generate_random_path()
    assert path.startswith("/"), "路径应该以 / 开头"
    assert len(path) == 17, f"路径长度应该是 17，实际是 {len(path)}"
    print(f"  ✓ 生成的路径: {path}")


def test_xray_config():
    """测试 Xray 配置生成"""
    print("\n测试 2: Xray 配置生成")
    
    gen = ConfigGenerator(
        domains=["test.example.com"],
        xray_port=10000
    )
    
    # 生成 JSON
    config_json = gen.generate_xray_json()
    config = json.loads(config_json)
    
    # 验证配置结构
    assert "inbounds" in config, "配置应包含 inbounds"
    assert "outbounds" in config, "配置应包含 outbounds"
    assert config["inbounds"][0]["protocol"] == "vless", "协议应该是 vless"
    assert config["inbounds"][0]["port"] == 10000, "端口应该是 10000"
    
    print(f"  ✓ UUID: {gen.client_uuid}")
    print(f"  ✓ 路径: {gen.xray_path}")
    print(f"  ✓ 端口: {gen.xray_port}")


def test_nginx_xray_config():
    """测试 Nginx Xray 配置生成"""
    print("\n测试 3: Nginx Xray 配置生成")
    
    config = generate_xray_config(
        domain="proxy.example.com",
        xray_port=10000,
        xray_path="/test-path"
    )
    
    # 验证配置内容
    assert "proxy.example.com" in config, "配置应包含域名"
    assert "listen 443 ssl http2" in config, "应监听 443 端口"
    assert "proxy_pass http://127.0.0.1:10000" in config, "应反代到 10000 端口"
    assert "location ~ ^/test-path" in config, "应包含路径配置"
    
    print("  ✓ Nginx 配置生成成功")
    print(f"  ✓ 配置长度: {len(config)} 字符")


def test_nginx_generic_config():
    """测试 Nginx 通用服务配置生成"""
    print("\n测试 4: Nginx 通用服务配置生成")
    
    config = generate_service_config(
        domain="api.example.com",
        backend_port=3000,
        service_name="API Service"
    )
    
    # 验证配置内容
    assert "api.example.com" in config, "配置应包含域名"
    assert "proxy_pass http://127.0.0.1:3000" in config, "应反代到 3000 端口"
    assert "API Service" in config, "应包含服务名称"
    
    print("  ✓ 通用服务配置生成成功")


def test_main_nginx_conf():
    """测试主 Nginx 配置生成"""
    print("\n测试 5: 主 Nginx 配置生成")
    
    config = generate_main_nginx_conf()
    
    # 验证配置内容
    assert "worker_processes auto" in config, "应包含 worker_processes"
    assert "include /etc/nginx/conf.d/*.conf" in config, "应包含 include 指令"
    assert "gzip on" in config, "应启用 gzip"
    
    print("  ✓ 主配置生成成功")


def test_service_manager():
    """测试服务管理器"""
    print("\n测试 6: 服务管理器")
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = NginxServiceManager(conf_dir=tmpdir)
        
        # 添加 Xray 服务
        config_file = manager.add_xray_service(
            domain="test.example.com",
            xray_port=10000,
            xray_path="/test-path"
        )
        
        assert config_file.exists(), "配置文件应该存在"
        print(f"  ✓ Xray 服务配置已创建: {config_file.name}")
        
        # 添加通用服务
        config_file2 = manager.add_generic_service(
            domain="api.example.com",
            backend_port=3000,
            service_name="API Service"
        )
        
        assert config_file2.exists(), "配置文件应该存在"
        print(f"  ✓ 通用服务配置已创建: {config_file2.name}")
        
        # 列出服务
        services = manager.list_services()
        assert len(services) == 2, f"应该有 2 个服务，实际有 {len(services)}"
        print(f"  ✓ 服务列表: {services}")
        
        # 删除服务
        success = manager.remove_service(config_file.name)
        assert success, "删除应该成功"
        
        services = manager.list_services()
        assert len(services) == 1, f"删除后应该有 1 个服务，实际有 {len(services)}"
        print("  ✓ 服务删除成功")


def test_multi_domain():
    """测试多域名配置"""
    print("\n测试 7: 多域名配置")
    
    domains = ["proxy1.example.com", "proxy2.example.com", "proxy3.example.com"]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = NginxServiceManager(conf_dir=tmpdir)
        
        for i, domain in enumerate(domains, start=1):
            gen = ConfigGenerator(
                domains=[domain],
                xray_port=10000 + i
            )
            
            manager.add_xray_service(
                domain=domain,
                xray_port=10000 + i,
                xray_path=gen.xray_path
            )
        
        services = manager.list_services()
        assert len(services) == 3, f"应该有 3 个服务，实际有 {len(services)}"
        print(f"  ✓ 创建了 {len(services)} 个服务配置")
        
        for service in services:
            print(f"    - {service}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("配置生成器测试")
    print("=" * 60)
    
    try:
        test_random_path()
        test_xray_config()
        test_nginx_xray_config()
        test_nginx_generic_config()
        test_main_nginx_conf()
        test_service_manager()
        test_multi_domain()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

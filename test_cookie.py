#!/usr/bin/env python3
"""
Cookie 功能测试脚本
用于本地验证 CookieCloud 配置是否正确
"""

import os
import sys
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，跳过加载 .env 文件")

from weread2notionpro.cookie_manager import CookieManager, CookieCloudFetcher, CookieCloudDecryptor

def test_cookie_manager():
    """测试 CookieManager 功能"""
    print("\n" + "="*50)
    print("测试 CookieManager")
    print("="*50)
    
    manager = CookieManager()
    
    # 获取 cookie
    print("\n1. 获取 Cookie...")
    cookies = manager.get_cookies()
    
    if cookies:
        print(f"✅ 成功获取 Cookie，共 {len(cookies)} 个字段")
        print(f"   包含字段: {list(cookies.keys())}")
        
        # 检查关键字段
        if 'wr_vid' in cookies:
            print(f"✅ 找到 wr_vid: {cookies['wr_vid'][:10]}...")
        else:
            print("⚠️  未找到 wr_vid（用户ID）")
            
        if 'wr_name' in cookies:
            print(f"✅ 找到 wr_name: {cookies['wr_name']}")
        else:
            print("⚠️  未找到 wr_name（用户名）")
        
        # 验证有效性
        print("\n2. 验证 Cookie 有效性...")
        if manager.is_valid:
            print("✅ Cookie 有效")
            return True
        else:
            print("❌ Cookie 无效或已过期")
            return False
    else:
        print("❌ 未能获取 Cookie")
        print("\n请检查以下环境变量是否设置正确:")
        print("  - CC_URL (CookieCloud 服务器地址)")
        print("  - CC_ID (用户 UUID)")
        print("  - CC_PASSWORD (加密密码)")
        print("  - WEREAD_COOKIE (直接提供 Cookie，作为备用)")
        return False

def test_direct_fetch():
    """直接测试 CookieCloud 获取"""
    print("\n" + "="*50)
    print("测试直接连接 CookieCloud")
    print("="*50)
    
    server_url = os.getenv('CC_URL', 'https://cookiecloud.malinkang.com')
    uuid = os.getenv('CC_ID')
    password = os.getenv('CC_PASSWORD')
    
    if not all([uuid, password]):
        print("❌ 缺少 CC_ID 或 CC_PASSWORD 环境变量")
        return False
    
    print(f"服务器: {server_url}")
    print(f"UUID: {uuid[:8]}...")
    
    fetcher = CookieCloudFetcher(server_url, uuid, password)
    cookie_str = fetcher.fetch_cookie_from_cloud()
    
    if cookie_str:
        print("✅ 成功从 CookieCloud 获取 Cookie")
        print(f"   前100字符: {cookie_str[:100]}...")
        return True
    else:
        print("❌ 从 CookieCloud 获取 Cookie 失败")
        return False

def main():
    print("CookieCloud 测试工具")
    print("="*50)
    
    # 检查环境变量
    print("\n环境变量检查:")
    env_vars = ['CC_URL', 'CC_ID', 'CC_PASSWORD', 'WEREAD_COOKIE']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: 未设置")
    
    # 运行测试
    results = []
    
    # 测试直接获取
    if os.getenv('CC_ID') and os.getenv('CC_PASSWORD'):
        results.append(("直接获取", test_direct_fetch()))
    
    # 测试 CookieManager
    results.append(("CookieManager", test_cookie_manager()))
    
    # 输出结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    # 返回退出码
    if all(r for _, r in results):
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    main()

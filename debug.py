#!/usr/bin/env python3
"""
本地调试脚本

用法:
    python debug.py book      # 同步书架
    python debug.py weread    # 同步笔记
    python debug.py read_time # 同步阅读时间

环境变量:
    从 .env 文件读取，或手动设置
"""
import os
import sys
import argparse

# 设置默认日志级别为 DEBUG
os.environ.setdefault('LOG_LEVEL', 'DEBUG')

# 配置日志
import logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(
        description='微信读书同步到 Notion - 本地调试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python debug.py book              # 同步书架
    python debug.py weread            # 同步笔记
    python debug.py read_time         # 同步阅读时间
    LOG_LEVEL=DEBUG python debug.py book  # 开启详细日志
        '''
    )
    parser.add_argument(
        'command',
        choices=['book', 'weread', 'read_time'],
        help='要执行的同步命令'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 开始执行: {args.command}")
    print(f"📊 日志级别: {log_level}")
    print("-" * 50)
    
    try:
        if args.command == 'book':
            from weread2notionpro.book import main as book_main
            book_main()
        elif args.command == 'weread':
            from weread2notionpro.weread import main as weread_main
            weread_main()
        elif args.command == 'read_time':
            from weread2notionpro.read_time import main as read_time_main
            read_time_main()
        print("-" * 50)
        print(f"✅ {args.command} 执行完成")
    except Exception as e:
        print("-" * 50)
        print(f"❌ {args.command} 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

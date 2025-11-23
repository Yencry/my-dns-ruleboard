#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行脚本：通过 Script Hub 聚合广告规则到本地文件
"""

import sys
import os


def main():
    print("🚀 广告规则聚合工具（Script Hub）")
    print("=" * 50)

    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        return

    # 安装依赖
    try:
        import requests  # noqa: F401
    except ImportError:
        print("📦 正在安装requests库...")
        os.system("pip install requests")
        import requests  # noqa: F401

    print("\n📥 开始通过 Script Hub 聚合广告规则...")
    try:
        from download_adblock_rules import AdBlockDownloader
        downloader = AdBlockDownloader()
        downloader.download_and_process_all()
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return

    print("\n🎉 完成! 已通过 Script Hub 聚合规则到本地文件:")
    print("📁 rules/merged_adblock.list - 聚合的广告规则 (Loon 格式原始规则)\n")


if __name__ == "__main__":
    main()

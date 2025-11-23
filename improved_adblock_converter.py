#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的广告规则下载和转换脚本
修复了转换过程中的问题
"""

import requests
import re
import os
import time
from urllib.parse import urlparse

class ImprovedAdBlockConverter:
    def __init__(self, output_dir="rules"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def download_file(self, url, filename):
        """下载文件"""
        try:
            print(f"正在下载: {filename}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✓ 下载完成: {filename}")
            return filepath
        except Exception as e:
            print(f"✗ 下载失败 {filename}: {e}")
            return None
    
    def convert_to_loon_domains(self, content):
        """改进的转换函数，提取有效域名"""
        domains = set()  # 使用set去重
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('!') or line.startswith('#') or line.startswith('[Adblock'):
                continue
            
            # 跳过Adblock指令
            if any(line.startswith(prefix) for prefix in ['[', '/', '-', '!']):
                continue
            
            # 提取域名的正则表达式
            # 1. ||domain.com^ 格式
            if line.startswith('||'):
                pattern = r'\|\|([a-zA-Z0-9.-]+)'
                match = re.search(pattern, line)
                if match:
                    domain = match.group(1)
                    if self.is_valid_domain(domain):
                        domains.add(domain)
            
            # 2. |domain.com 格式
            elif line.startswith('|') and not line.startswith('||'):
                pattern = r'\|([a-zA-Z0-9.-]+)'
                match = re.search(pattern, line)
                if match:
                    domain = match.group(1)
                    if self.is_valid_domain(domain):
                        domains.add(domain)
            
            # 3. 0.0.0.0 domain.com 或 127.0.0.1 domain.com 格式
            elif line.startswith('0.0.0.0') or line.startswith('127.0.0.1'):
                parts = line.split()
                if len(parts) >= 2:
                    domain = parts[1]
                    if self.is_valid_domain(domain):
                        domains.add(domain)
            
            # 4. DOMAIN,domain.com 格式
            elif line.startswith('DOMAIN,'):
                domain = line[7:].split(',')[0].strip()
                if self.is_valid_domain(domain):
                    domains.add(domain)
            
            # 5. DOMAIN-SUFFIX,domain.com 格式
            elif line.startswith('DOMAIN-SUFFIX,'):
                domain = line[13:].split(',')[0].strip()
                if self.is_valid_domain(domain):
                    domains.add(domain)
            
            # 6. 纯域名格式
            elif '.' in line and ',' not in line and '/' not in line:
                if self.is_valid_domain(line):
                    domains.add(line)
        
        return sorted(list(domains))
    
    def is_valid_domain(self, domain):
        """验证域名是否有效"""
        if not domain or len(domain) < 4:
            return False
        
        # 排除明显无效的域名
        invalid_patterns = [
            'localhost', 'local', 'example', 'test', 'invalid',
            '0.0.0.0', '127.0.0.1', '255.255.255.255',
            'about:blank', 'data:', 'blob:', 'file:'
        ]
        
        if domain.lower() in invalid_patterns:
            return False
        
        # 检查是否包含有效字符
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
            return False
        
        # 检查是否至少有一个点
        if '.' not in domain:
            return False
        
        # 检查不以点开头或结尾
        if domain.startswith('.') or domain.endswith('.'):
            return False
        
        # 检查长度
        if len(domain) > 253:  # 域名最大长度
            return False
        
        return True
    
    def process_all_sources(self):
        """处理所有规则源"""
        rule_sources = {
            "1Hosts_Lite": "https://badmojr.github.io/1Hosts/Lite/adblock.txt",
            "hBlock": "https://hblock.molinero.dev/hosts_adblock.txt",
            "Multi_NORMAL": "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/multi.txt",
            "Fanboy-CookieMonster": "https://secure.fanboy.co.nz/fanboy-cookiemonster.txt",
            "EasylistChina": "https://easylist-downloads.adblockplus.org/easylistchina.txt",
            "AdGuardSDNSFilter": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
            "rejectAd": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list",
            "Advertising_Domain": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list",
            "Advertising": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list"
        }
        
        all_domains = set()
        
        for name, url in rule_sources.items():
            print(f"\n📥 处理: {name}")
            filepath = self.download_file(url, f"{name}.txt")
            
            if filepath:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    domains = self.convert_to_loon_domains(content)
                    print(f"✓ 提取到 {len(domains)} 个有效域名")
                    all_domains.update(domains)
                    
                    # 保留源文件用于调试
                    # os.remove(filepath)
                    
                except Exception as e:
                    print(f"✗ 处理失败 {name}: {e}")
            
            time.sleep(1)  # 避免请求过快
        
        return sorted(list(all_domains))
    
    def generate_loon_config(self, domains, output_file="improved_adblock.list"):
        """生成Loon配置文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# 改进的广告拦截规则 - Loon格式\n")
            f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总规则数: {len(domains)}\n")
            f.write("# 规则来源: 多个广告拦截源\n")
            f.write("\n")
            
            # 写入规则
            for domain in domains:
                f.write(f"DOMAIN,{domain},REJECT\n")
        
        print(f"✓ 生成配置文件: {output_file} ({len(domains)} 条规则)")
        return output_file

def main():
    print("🚀 改进的广告规则转换器")
    print("=" * 50)
    
    converter = ImprovedAdBlockConverter()
    
    print("📥 开始处理所有规则源...")
    domains = converter.process_all_sources()
    
    if domains:
        print(f"\n📊 总共提取到 {len(domains)} 个唯一域名")
        
        # 显示一些示例域名
        print("\n🔍 示例域名:")
        for domain in domains[:10]:
            print(f"  {domain}")
        
        # 生成配置文件
        output_file = converter.generate_loon_config(domains)
        
        print(f"\n🎉 完成! 配置文件: {output_file}")
        print("📖 使用方法: 将文件内容添加到Loon的[Remote Rule]部分")
    else:
        print("\n❌ 没有提取到任何域名")

if __name__ == "__main__":
    main()

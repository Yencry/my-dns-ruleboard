#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广告规则下载、转换和聚合脚本
将多个广告规则源下载并转换为Loon格式
"""

import requests
import re
import os
import time
from urllib.parse import urlparse
import argparse

class AdBlockDownloader:
    def __init__(self, output_dir="rules"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Script Hub 本地服务地址（与 PowerShell 脚本保持一致）
        self.scripthub_base = "http://localhost:9100"
    
    def extract_original_url(self, script_hub_url):
        """从Script Hub URL中提取原始URL"""
        # Script Hub格式: http://script.hub/file/_start_/ORIGINAL_URL/_end_/FILENAME
        pattern = r'_start_/(.*?)/_end_/'
        match = re.search(pattern, script_hub_url)
        if match:
            return match.group(1)
        return script_hub_url

    def build_scripthub_url(self, original_url, filename):
        """根据原始规则URL和文件名构造 Script Hub 聚合 URL"""
        # 与 download_merged_from_scripthub.ps1 中的格式保持一致：
        # http://localhost:9100/file/_start_/{ORIGINAL_URL}/_end_/{FILENAME}?type=rule-set&target=loon-rule-set&del=true&jqEnabled=true
        return (
            f"{self.scripthub_base}/file/_start_/{original_url}/_end_/{filename}"
            "?type=rule-set&target=loon-rule-set&del=true&jqEnabled=true"
        )

    def expand_source_urls(self, url):
        """将可能包含多个来源链接的字符串拆分为独立 URL 列表

        支持的格式示例：
        https://a.com/list.txt😂https://b.com/list.txt😂https://c.com/list.txt
        """
        # 按 😂 分隔（Script Hub 来源链接习惯用法）
        if '😂' in url:
            parts = [u.strip() for u in url.split('😂') if u.strip()]
            return parts if parts else [url]
        return [url]
    
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
    
    def convert_adblock_to_loon(self, adblock_content):
        """将Adblock格式转换为Loon格式"""
        loon_rules = []
        lines = adblock_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('!') or line.startswith('#'):
                continue
            
            # 跳过Adblock指令
            if line.startswith('[') or line.startswith('/') or line.startswith('-'):
                continue
            
            # 处理不同类型的规则
            if line.startswith('||'):
                # ||domain.com 形式
                domain = line[2:].split('^')[0].split('/')[0]
                if domain and '.' in domain and len(domain) > 3:
                    loon_rules.append(f"DOMAIN,{domain}")
            elif line.startswith('|'):
                # |domain.com 形式
                domain = line[1:].split('^')[0].split('/')[0]
                if domain and '.' in domain and len(domain) > 3:
                    loon_rules.append(f"DOMAIN,{domain}")
            elif line.startswith('|||'):
                # |||domain.com 形式
                domain = line[3:].split('^')[0].split('/')[0]
                if domain and '.' in domain and len(domain) > 3:
                    loon_rules.append(f"DOMAIN,{domain}")
            elif '^' in line:
                # 包含^的规则
                domain = line.split('^')[0].replace('||', '').replace('|', '')
                if domain and '.' in domain and len(domain) > 3:
                    loon_rules.append(f"DOMAIN,{domain}")
            elif '.' in line and '/' not in line and len(line) > 3:
                # 简单域名
                if not line.startswith(('http', 'www', 'ftp', '0.0.0.0', '127.0.0.1')):
                    loon_rules.append(f"DOMAIN,{line}")
        
        return loon_rules
    
    def convert_hosts_to_loon(self, hosts_content):
        """将hosts格式转换为Loon格式"""
        loon_rules = []
        lines = hosts_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            
            # 处理hosts格式: 0.0.0.0 domain.com 或 127.0.0.1 domain.com
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ['0.0.0.0', '127.0.0.1']:
                domain = parts[1]
                if '.' in domain and len(domain) > 3 and domain != 'localhost':
                    loon_rules.append(f"DOMAIN,{domain}")
        
        return loon_rules
    
    def convert_surge_to_loon(self, surge_content):
        """将Surge格式转换为Loon格式"""
        loon_rules = []
        lines = surge_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            
            # Surge格式通常已经是DOMAIN形式
            if line.startswith('DOMAIN,'):
                loon_rules.append(line)
            elif line.startswith('DOMAIN-SUFFIX,'):
                loon_rules.append(line)
            elif '.' in line and ',' not in line and '/' not in line and len(line) > 3:
                # 简单域名
                if not line.startswith(('http', 'www', 'ftp', '0.0.0.0', '127.0.0.1')):
                    loon_rules.append(f"DOMAIN,{line}")
        
        return loon_rules
    
    def process_file(self, filepath, filename):
        """处理下载的文件并转换为Loon格式"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 根据文件名和内容判断格式
            filename_lower = filename.lower()
            if '1hosts' in filename_lower:
                # 1Hosts (Lite) 实际为 Adblock 列表
                loon_rules = self.convert_adblock_to_loon(content)
            elif 'hosts' in filename_lower:
                # 明确为 hosts 格式
                loon_rules = self.convert_hosts_to_loon(content)
            elif 'adblock' in filename_lower:
                # 明确为 Adblock 格式
                loon_rules = self.convert_adblock_to_loon(content)
            elif filename_lower.endswith('.list') or 'surge' in filename_lower:
                # Surge / Loon 列表格式
                loon_rules = self.convert_surge_to_loon(content)
            else:
                # 尝试自动检测
                if '0.0.0.0' in content or '127.0.0.1' in content:
                    loon_rules = self.convert_hosts_to_loon(content)
                elif '||' in content or '^' in content:
                    loon_rules = self.convert_adblock_to_loon(content)
                else:
                    loon_rules = self.convert_surge_to_loon(content)
            
            print(f"✓ 转换完成 {filename}: {len(loon_rules)} 条规则")
            return loon_rules
            
        except Exception as e:
            print(f"✗ 转换失败 {filename}: {e}")
            return []
    
    def merge_rules(self, all_rules, output_filename="merged_adblock.list"):
        """合并所有规则并去重"""
        # 合并所有规则
        merged_rules = []
        seen = set()
        
        for rules in all_rules:
            for rule in rules:
                if rule not in seen:
                    merged_rules.append(rule)
                    seen.add(rule)
        
        # 写入合并后的文件
        output_path = os.path.join(self.output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("#!/bin/bash\n")
            f.write("# 聚合广告拦截规则 - Loon格式\n")
            f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总规则数: {len(merged_rules)}\n")
            f.write("# 规则来源: 1Hosts (Lite), hBlock, Multi NORMAL, Fanboy-CookieMonster, EasylistChina, AdGuardSDNSFilter, rejectAd, Advertising_Domain, Advertising\n")
            f.write("\n")
            
            # 写入规则
            for rule in merged_rules:
                f.write(f"{rule}\n")
        
        print(f"✓ 合并完成: {output_filename} ({len(merged_rules)} 条规则)")
        return output_path
    
    def download_and_process_all(self):
        """下载并处理所有规则源"""
        # 组合来源链接：9 个原始规则 URL 用 😂 拼接，由 Script Hub 一次性聚合
        combined_source_url = '😂'.join([
            "https://badmojr.github.io/1Hosts/Lite/adblock.txt",
            "https://hblock.molinero.dev/hosts_adblock.txt",
            "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/multi.txt",
            "https://secure.fanboy.co.nz/fanboy-cookiemonster.txt",
            "https://easylist-downloads.adblockplus.org/easylistchina.txt",
            "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
            "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list",
            "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list",
            "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
        ])

        # 这里只保留一个来源：Combined，由 Script Hub 内部处理 9 个 URL 的聚合
        rule_sources = {
            "Combined": combined_source_url
        }
        
        # all_rules 需要是「每个来源一份规则列表」的列表，方便后续跨来源去重
        all_rules = []
        
        for name, url in rule_sources.items():
            # 这里的 url 可以是单个源，也可以是多个 URL 用 😂 拼接后的“来源链接”字符串，
            # 会整体传给 Script Hub，由 Script Hub 自己负责拆分和聚合
            filename = f"{name}.list"
            
            # 通过 Script Hub 拉取已转换为 Loon 规则集的结果
            scripthub_url = self.build_scripthub_url(url, filename)
            filepath = self.download_file(scripthub_url, filename)
            
            if filepath:
                # 从 Script Hub 返回的 Loon 规则集中提取有效规则行
                try:
                    rules = []
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # 跳过注释和空行
                            if not line or line.startswith('#') or line.startswith('#!'):
                                continue
                            rules.append(line)
                    if rules:
                        # 保持为 list[list[str]] 结构，避免在 merge_rules 中把字符串当成字符序列遍历
                        all_rules.append(rules)
                except Exception as e:
                    print(f"✗ 解析 Script Hub 返回结果失败 {filename}: {e}")
                
                # 删除临时文件
                try:
                    os.remove(filepath)
                except:
                    pass
            
            # 添加延迟避免请求过快
            time.sleep(1)
        
        # 合并所有规则
        if all_rules:
            # 统计总规则条数（未去重前）
            total_before_merge = sum(len(rules) for rules in all_rules)
            self.merge_rules(all_rules)
            print(f"\n🎉 完成! 总共处理了 {total_before_merge} 条规则（合并前）")
        else:
            print("\n❌ 没有成功处理任何规则")

def main():
    parser = argparse.ArgumentParser(description='广告规则下载和聚合工具')
    parser.add_argument('--output-dir', default='rules', help='输出目录')
    
    args = parser.parse_args()
    
    downloader = AdBlockDownloader(args.output_dir)
    downloader.download_and_process_all()

if __name__ == "__main__":
    main()

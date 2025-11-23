$uri      = 'http://localhost:9100/file/_start_/https://badmojr.github.io/1Hosts/Lite/adblock.txt%F0%9F%98%82https://badmojr.github.io/1Hosts/Lite/adblock.txt%F0%9F%98%82https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/multi.txt%F0%9F%98%82https://secure.fanboy.co.nz/fanboy-cookiemonster.txt%F0%9F%98%82https://easylist-downloads.adblockplus.org/easylistchina.txt%F0%9F%98%82https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt%F0%9F%98%82https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list%F0%9F%98%82https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list%F0%9F%98%82https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list%F0%9F%98%82https://anti-ad.net/surge2.txt/_end_/surge2.list?type=rule-set&target=loon-rule-set&del=true&jqEnabled=true'
$targetDir = 'D:\project\dns_web\rules'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outFile   = Join-Path $targetDir "merged_adblock_$timestamp.list"

# 确保目录存在
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Invoke-WebRequest -Uri $uri -OutFile $outFile
Write-Host "已保存到: $outFile"
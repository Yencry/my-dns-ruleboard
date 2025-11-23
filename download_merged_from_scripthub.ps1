$targetDir = 'D:\project\dns_web\rules'
$tmpDir    = Join-Path $targetDir 'tmp_rules'
$outFile   = Join-Path $targetDir 'merged_adblock.list'

# 要聚合的规则源列表：Url 和 输出文件名
$sources = @(
    @{ Url = 'https://badmojr.github.io/1Hosts/Lite/adblock.txt'; Name = '1hosts.list' }
    @{ Url = 'https://hblock.molinero.dev/hosts_adblock.txt'; Name = 'hblock.list' }
    @{ Url = 'https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/multi.txt'; Name = 'multi.list' }
    @{ Url = 'https://secure.fanboy.co.nz/fanboy-cookiemonster.txt'; Name = 'fanboy-cookiemonster.list' }
    @{ Url = 'https://easylist-downloads.adblockplus.org/easylistchina.txt'; Name = 'easylistchina.list' }
    @{ Url = 'https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt'; Name = 'adguard-sdns.list' }
    @{ Url = 'https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list'; Name = 'rejectAd.list' }
    @{ Url = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list'; Name = 'Advertising_Domain.list' }
    @{ Url = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list'; Name = 'Advertising.list' }
)

# 确保目录存在
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
New-Item -ItemType Directory -Force -Path $tmpDir    | Out-Null

# 清空目标文件
if (Test-Path $outFile) {
    Remove-Item $outFile -Force
}

foreach ($src in $sources) {
    $url  = $src.Url
    $name = $src.Name

    $scriptHubUrl = "http://localhost:9100/file/_start_/{0}/_end_/{1}?type=rule-set&target=loon-rule-set&del=true&jqEnabled=true" -f $url, $name

    $tmpFile      = Join-Path $tmpDir $name

    Write-Host "Fetching via Script-Hub: $url" -ForegroundColor Cyan
    Write-Host "  URL: $scriptHubUrl"

    try {
        Invoke-WebRequest -Uri $scriptHubUrl -OutFile $tmpFile -TimeoutSec 300
    }
    catch {
        Write-Host "  ERROR: 下载失败 $url : $($_.Exception.Message)" -ForegroundColor Red
        throw
    }

    # 追加到总文件
    Get-Content $tmpFile | Add-Content -Path $outFile
    Add-Content -Path $outFile -Value ''
}

Write-Host "已生成本地聚合规则文件: $outFile" -ForegroundColor Green
Write-Host "已保存到: $outFile"
# my-dns-ruleboard

一个用于个人自用的 **DNS 层 / 广告与隐私拦截规则面板**，同时提供自动聚合的 Loon 广告规则文件。
- 自动更新：GitHub Actions 每日北京时间凌晨两点自动更新一次

## 在线预览
```text
https://yencry.github.io/my-dns-ruleboard/
```
页面中包含：

- 常见广告 / 隐私 / hosts 黑名单规则源列表
- 每个规则源的说明、最近更新时间
- 一键复制按钮，方便粘贴到 DNS / 防火墙 / 客户端配置中
- 一条由本仓库自动聚合生成的规则：
  - `Loon 聚合广告规则`

## 规则来源（部分）

当前聚合脚本使用的规则源包括（但不限于）：

- anti-AD (AdGuard)
- Adblock Warning Removal List
- AdGuard DNS filter
- EasyList / EasyList China / EasyPrivacy
- Fanboy Annoyance List / Fanboy Social Blocking List
- HaGeZi Light (adblock)
- hBlock hosts_adblock
- StevenBlack Unified hosts

这些规则的语义基本都是：**应该被拦截的广告 / 跟踪 / 恶意域名**，适合作为 *拒绝 / REJECT* 使用。

## 开源协议

本仓库代码和页面（不包括外部规则源本身）采用 **Mozilla Public License 2.0 (MPL-2.0)** 授权，详见 `LICENSE` 文件。

- 你可以自由使用、修改、再分发本仓库代码；
- 如果你对本仓库的代码作了修改并再分发，需按 MPL-2.0 的要求公开修改后的对应源文件。

外部规则源的许可证由各项目各自规定，请参见对应项目主页。

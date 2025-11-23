#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch last-modified metadata for all rule sources and write to JSON.

This script is intended to run in CI (GitHub Actions). It queries each
upstream rule URL with HEAD (and falls back to GET if needed), extracts
Last-Modified or Date headers, and writes a deterministic JSON file:

    rules/sources_meta.json

The JSON only changes when upstream metadata changes, so commits are
only created when something actually updates.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

# Sources to probe for last-modified information.
SOURCES = [
    {
        "name": "Loon 聚合广告规则",
        "url": "https://yencry.github.io/my-dns-ruleboard/rules/merged_adblock.list",
    },
    {
        "name": "1Hosts (Lite)",
        "url": "https://badmojr.github.io/1Hosts/Lite/adblock.txt",
    },
    {
        "name": "hBlock hosts_adblock",
        "url": "https://hblock.molinero.dev/hosts_adblock.txt",
    },
    {
        "name": "HaGeZi Multi NORMAL",
        "url": "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/multi.txt",
    },
    {
        "name": "Fanboy-CookieMonster",
        "url": "https://secure.fanboy.co.nz/fanboy-cookiemonster.txt",
    },
    {
        "name": "EasyList China",
        "url": "https://easylist-downloads.adblockplus.org/easylistchina.txt",
    },
    {
        "name": "AdGuard DNS filter",
        "url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
    },
    {
        "name": "rejectAd.list (Loon)",
        "url": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/rejectAd.list",
    },
    {
        "name": "Advertising_Domain (Loon)",
        "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list",
    },
    {
        "name": "Advertising (Loon)",
        "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
    },
]


def _parse_http_date(value: str) -> datetime | None:
    """Parse an HTTP date string to an aware datetime, if possible."""

    try:
        dt = parsedate_to_datetime(value)
    except Exception:  # pragma: no cover - best-effort parsing
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_metadata(session: requests.Session, url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch last-modified style metadata for a single URL."""

    base: Dict[str, Any] = {
        "url": url,
        "http_status": None,
        "status": "error",
        "last_modified": None,
        "last_modified_header": None,
    }

    headers = {
        "User-Agent": "my-dns-ruleboard-meta/1.0",
        "Accept": "*/*",
    }

    def try_extract(resp: requests.Response) -> bool:
        if resp is None:
            return False
        base["http_status"] = resp.status_code
        if not resp.ok:
            return False
        lm = resp.headers.get("Last-Modified") or resp.headers.get("Date")
        if not lm:
            return False
        dt = _parse_http_date(lm)
        if not dt:
            return False
        base["last_modified_header"] = lm
        # Use ISO 8601 string for easy parsing on the frontend
        base["last_modified"] = dt.isoformat()
        base["status"] = "ok"
        return True

    # 1) Try HEAD first
    try:
        resp = session.head(url, headers=headers, timeout=timeout, allow_redirects=True)
    except Exception as e:  # pragma: no cover - network errors
        base["error"] = str(e)
        resp = None

    success = try_extract(resp)

    # 2) Fallback to GET if HEAD failed or lacked useful headers
    if not success:
        try:
            resp = session.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
                stream=True,
            )
        except Exception as e:  # pragma: no cover - network errors
            base["error"] = str(e)
            resp = None
        else:
            # Ensure the connection can be reused
            resp.close()
        success = try_extract(resp) or success

    if not success and "error" not in base:
        base["status"] = "no-header"
    return base


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    out_path = base_dir / "rules" / "sources_meta.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()

    result: Dict[str, Any] = {"sources": []}
    for src in SOURCES:
        name = src.get("name") or src.get("url")
        url = src["url"]
        info = fetch_metadata(session, url)
        info["name"] = name
        result["sources"].append(info)

    # Deterministic ordering by name for a stable JSON diff
    result["sources"].sort(key=lambda x: str(x.get("name", "")))

    tmp_path = out_path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    tmp_path.replace(out_path)

    print(f"[ok] wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

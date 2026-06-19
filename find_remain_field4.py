#!/usr/bin/env python3
"""分析腾讯行情字段，找到流通量/剩余规模"""
import sys, io, requests, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0",
})

# 永吉转债 — 发行1.46亿，已知小规模妖债
resp = s.get("https://qt.gtimg.cn/q=sh113646", timeout=10)
line = resp.text.strip()
m = re.search(r'v_\w+="(.+)"', line)
if m:
    parts = m.group(1).split("~")
    print(f"永吉转债 (发行1.46亿) — 共 {len(parts)} 个字段:")
    for i, p in enumerate(parts):
        if p:
            print(f"  [{i}] {p}")

print("\n\n")

# 大中转债 — 发行规模较大
resp = s.get("https://qt.gtimg.cn/q=sz127070", timeout=10)
line = resp.text.strip()
m = re.search(r'v_\w+="(.+)"', line)
if m:
    parts = m.group(1).split("~")
    print(f"大中转债 (发行22亿) — 共 {len(parts)} 个字段:")
    for i, p in enumerate(parts):
        if p:
            print(f"  [{i}] {p}")

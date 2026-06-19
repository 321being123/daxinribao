#!/usr/bin/env python3
"""探测东财 push2 clist 接口中可转债的剩余规模字段"""
import sys, io, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
})

# 尝试获取所有字段
resp = s.get("https://push2.eastmoney.com/api/qt/clist/get", params={
    "pn": 1, "pz": 3, "po": 0, "np": 1,
    "fltt": 2, "invt": 2, "fid": "f3",
    "fs": "b:MK0354",
    "fields": "f12,f14,f2,f3,f9,f23,f161,f243,f244,f230,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f245,f246,f247,f248,f249,f250,f251,f252,f253,f254,f255,f256,f257,f258,f259,f260",
}, timeout=15)
data = resp.json()
if data.get("data") and data["data"].get("diff"):
    for item in data["data"]["diff"][:3]:
        print(f"\n=== {item.get('f12')} {item.get('f14')} ===")
        for k, v in sorted(item.items()):
            print(f"  {k}: {v}")
else:
    print("No data:", json.dumps(data, ensure_ascii=False))

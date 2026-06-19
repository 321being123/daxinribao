#!/usr/bin/env python3
"""探测东财 datacenter 单只转债详情接口中是否有剩余规模字段"""
import sys, io, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
})

# 尝试用 datacenter 的 RPT_BOND_CB_LIST，筛选单只转债，获取所有字段
resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
    "reportName": "RPT_BOND_CB_LIST",
    "columns": "ALL",
    "filter": "(SECURITY_CODE=\"113646\")",
    "pageNumber": 1, "pageSize": 1,
    "source": "WEB", "client": "WEB",
}, timeout=15)
data = resp.json()
if data.get("success") and data.get("result"):
    row = data["result"]["data"][0]
    for k, v in sorted(row.items()):
        if v is not None and v != "":
            print(f"  {k}: {v}")
else:
    print("Failed:", json.dumps(data, ensure_ascii=False)[:500])

#!/usr/bin/env python3
"""分析腾讯行情字段[57] = 成交额(万元)，找到流通量字段"""
import sys, io, requests, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

# 用已知数据验证：
# 永吉转债: 发行1.46亿, [57]=5075.4873万 → 0.50754873亿 → 这是成交额不是流通规模
# 大中转债: 发行22亿, [57]=137998.7691万 → 13.8亿 → 这也是成交额

# 看看东财 datacenter 可转债转股信息接口
# RPT_F10_BOND_CB_TRANSFERINFO
s.headers.update({"Referer": "https://data.eastmoney.com/"})

print("=== RPT_F10_BOND_CB_TRANSFERINFO ===")
resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
    "reportName": "RPT_F10_BOND_CB_TRANSFERINFO",
    "columns": "ALL",
    "filter": "(SECURITY_CODE=\"113646\")",
    "pageNumber": 1, "pageSize": 5,
    "source": "WEB", "client": "WEB",
}, timeout=10)
data = resp.json()
if data.get("success") and data.get("result"):
    for row in data["result"]["data"]:
        for k, v in sorted(row.items()):
            if v is not None and v != "":
                print(f"  {k}: {v}")
        print("---")
else:
    print(f"Failed: {data.get('message')}")

print("\n=== RPT_F10_BOND_CB_INFO ===")
resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
    "reportName": "RPT_F10_BOND_CB_INFO",
    "columns": "ALL",
    "filter": "(SECURITY_CODE=\"113646\")",
    "pageNumber": 1, "pageSize": 5,
    "source": "WEB", "client": "WEB",
}, timeout=10)
data = resp.json()
if data.get("success") and data.get("result"):
    for row in data["result"]["data"]:
        for k, v in sorted(row.items()):
            if v is not None and v != "":
                print(f"  {k}: {v}")
        print("---")
else:
    print(f"Failed: {data.get('message')}")

# 尝试东财 f10 个股接口
print("\n=== 东财 F10 转债信息 ===")
resp = s.get("https://datacenter-web.eastmoney.com/securities/api/data/v1/get", params={
    "reportName": "RPT_F10_BOND_CB_TRANSFERINFO",
    "columns": "ALL",
    "filter": "(SECURITY_CODE=\"113646\")",
    "pageNumber": 1, "pageSize": 5,
    "source": "WEB", "client": "WEB",
}, timeout=10)
data = resp.json()
if data.get("success") and data.get("result"):
    for row in data["result"]["data"]:
        for k, v in sorted(row.items()):
            if v is not None and v != "":
                print(f"  {k}: {v}")
        print("---")
else:
    print(f"Failed: {data.get('message')}")

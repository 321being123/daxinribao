#!/usr/bin/env python3
"""探测东财转债详情页接口中的剩余规模字段"""
import sys, io, requests, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
})

# 方法1：东财 datacenter 个股资金流接口可能有转债的剩余规模
# 方法2：东财 bond detail API
# 尝试东财 datacenter 的 RPT_BOND_CB_DETAIL
for reportName in ["RPT_BOND_CB_DETAIL", "RPT_BOND_CB_TRANS", "RPT_BOND_CB_CONVERT"]:
    try:
        resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
            "reportName": reportName,
            "columns": "ALL",
            "pageNumber": 1, "pageSize": 1,
            "source": "WEB", "client": "WEB",
        }, timeout=10)
        data = resp.json()
        if data.get("success"):
            print(f"[OK] {reportName}: {list(data['result']['data'][0].keys())[:20]}")
        else:
            print(f"[FAIL] {reportName}: {data.get('message')}")
    except Exception as e:
        print(f"[ERR] {reportName}: {e}")

# 方法3：尝试东财转债页面 JS 接口
print("\n--- 尝试东财转债列表页 JS 接口 ---")
try:
    resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
        "reportName": "RPT_BOND_CB_LIST",
        "columns": "SECURITY_CODE,SECURITY_NAME_ABBR,ACTUAL_ISSUE_SCALE,CURRENT_BOND_PRICENEW,TRANSFER_VALUE,TRANSFER_PREMIUM_RATIO",
        "filter": "(SECURITY_CODE=\"113646\")",
        "pageNumber": 1, "pageSize": 1,
        "source": "WEB", "client": "WEB",
    }, timeout=10)
    data = resp.json()
    print(json.dumps(data.get("result", {}).get("data", [{}])[0], ensure_ascii=False, indent=2))
except Exception as e:
    print(f"ERR: {e}")

# 方法4：腾讯行情 转债数据里看有没有流通量
print("\n--- 腾讯行情 永吉转债 ---")
try:
    resp = s.get("https://qt.gtimg.cn/q=sh113646", timeout=10)
    print(resp.text[:500])
except Exception as e:
    print(f"ERR: {e}")

# 方法5：东财 datacenter 可转债转股进度
print("\n--- 东财转股进度 RPT_BOND_CB_PROGRESS ---")
try:
    resp = s.get("https://datacenter-web.eastmoney.com/api/data/v1/get", params={
        "reportName": "RPT_BOND_CB_PROGRESS",
        "columns": "ALL",
        "filter": "(SECURITY_CODE=\"113646\")",
        "pageNumber": 1, "pageSize": 5,
        "source": "WEB", "client": "WEB",
    }, timeout=10)
    data = resp.json()
    if data.get("success") and data.get("result"):
        row = data["result"]["data"][0]
        for k, v in sorted(row.items()):
            print(f"  {k}: {v}")
    else:
        print(f"Failed: {data.get('message')}")
except Exception as e:
    print(f"ERR: {e}")

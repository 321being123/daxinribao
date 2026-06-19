#!/usr/bin/env python3
"""
集思录登录 + 获取全量可转债数据
集思录新版登录需要code_verify验证码，但先试直接POST
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import re
import time
import json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.jisilu.cn/account/login/",
    "Origin": "https://www.jisilu.cn",
    "X-Requested-With": "XMLHttpRequest",
})

# 1. 访问登录页
resp = s.get("https://www.jisilu.cn/account/login/", timeout=15)

# 2. 提取所有可能的token
# 尝试多种pattern
for pattern in [
    r'name=["\']token["\']\s+value=["\']([^"\']+)["\']',
    r'token["\s:=]+([a-f0-9]{40})',
    r'xsrf["\s:=]+([a-f0-9]{40})',
    r'_token["\']\s+value=["\']([^"\']+)',
    r'csrf[_token]*["\']\s+value=["\']([^"\']+)',
]:
    m = re.search(pattern, resp.text, re.I)
    if m:
        print(f"找到token: pattern={pattern[:30]} → {m.group(1)[:30]}...")
        token = m.group(1)
        break
else:
    token = ""
    # 看所有input
    inputs = re.findall(r'<input[^>]+>', resp.text)
    for inp in inputs:
        if 'hidden' in inp and 'token' not in inp.lower() and 'return' not in inp.lower() and 'code' not in inp.lower():
            print(f"  hidden input: {inp}")

# 3. 尝试不用token直接登录（有些版本不需要）
for attempt_data in [
    {"user_name": "18612596191", "password": "dai.1234", "_post_type": "ajax"},
    {"user_name": "18612596191", "password": "dai.1234", "net_auto_login": "1", "_post_type": "ajax", "token": token},
    {"username": "18612596191", "password": "dai.1234", "_post_type": "ajax"},
]:
    resp = s.post("https://www.jisilu.cn/account/login/", data=attempt_data, timeout=15)
    try:
        result = resp.json()
        if result.get('success') or result.get('status') == 'ok' or result.get('code') == 1:
            print(f"登录成功! data={attempt_data}")
            print(f"  结果: {json.dumps(result, ensure_ascii=False)[:200]}")
            break
        else:
            print(f"登录失败: {json.dumps(result, ensure_ascii=False)[:200]}")
    except:
        # 非JSON说明可能登录成功跳转了
        if 'cbnew' in resp.url or 'data' in resp.url:
            print(f"登录成功(跳转)! url={resp.url}")
            break
        print(f"非JSON响应, url={resp.url}")

# 4. 检查是否已登录
cookie_str = "; ".join([f"{k}={v}" for k, v in s.cookies.items()])
print(f"\nCookie: {cookie_str[:100]}...")
has_login = 'kbzw__user_login' in s.cookies
print(f"已登录: {has_login}")

# 5. 请求可转债API — 分页获取全量
all_rows = []
for page in range(1, 15):
    ts = int(time.time() * 1000)
    api_url = f"https://www.jisilu.cn/data/cbnew/cb_list_new/?___jsl={ts}"
    post_data = {
        "rp": 100,  # 每页100条
        "page": page,
    }
    resp = s.post(api_url, data=post_data, timeout=15)
    try:
        data = resp.json()
        rows = data.get('rows', [])
        if not rows:
            print(f"  第{page}页: 无数据，停止")
            break
        all_rows.extend(rows)
        print(f"  第{page}页: {len(rows)}条，累计{len(all_rows)}条")
        if len(rows) < 100:
            break
    except:
        print(f"  第{page}页: 解析失败")
        break

print(f"\n总共获取 {len(all_rows)} 条转债")

# 6. 解析剩余规模和溢价率
if all_rows:
    # 找剩余规模字段
    sample = all_rows[0]['cell']
    # curr_iss_amt = 剩余规模(亿), orig_iss_amt = 发行规模(亿)
    # premium_rt = 溢价率(%)
    print(f"\n关键字段:")
    print(f"  代码: {sample.get('bond_id')}")
    print(f"  名称: {sample.get('bond_nm')}")
    print(f"  现价: {sample.get('price')}")
    print(f"  溢价率: {sample.get('premium_rt')}%")
    print(f"  剩余规模: {sample.get('curr_iss_amt')}亿")
    print(f"  发行规模: {sample.get('orig_iss_amt')}亿")
    print(f"  转股价值: {sample.get('convert_value')}")

    # 统计
    data_list = []
    for row in all_rows:
        c = row.get('cell', {})
        if c.get('price') and c.get('curr_iss_amt') and c.get('premium_rt') is not None:
            data_list.append({
                'code': c.get('bond_id'),
                'name': c.get('bond_nm'),
                'price': float(c.get('price')),
                'premium': float(c.get('premium_rt')),
                'remain': float(c.get('curr_iss_amt')),
                'issue': float(c.get('orig_iss_amt', 0)),
                'tv': float(c.get('convert_value', 0)),
            })

    print(f"\n有效数据: {len(data_list)} 只")

    # 按剩余规模分组统计
    print("\n" + "="*60)
    print("妖债溢价率统计（按剩余规模分组）")
    print("="*60)

    def stats(label, items):
        if not items:
            print(f"\n  {label}（0只）: 无数据")
            return
        premiums = [d['premium'] for d in items]
        avg = sum(premiums) / len(premiums)
        med = sorted(premiums)[len(premiums)//2]
        print(f"\n  {label}（{len(items)}只）:")
        print(f"    平均溢价率: {avg:.2f}%")
        print(f"    中位数溢价率: {med:.2f}%")
        print(f"    最小: {min(premiums):.2f}%  最大: {max(premiums):.2f}%")

    stats("剩余规模 < 0.5亿", [d for d in data_list if d['remain'] < 0.5])
    stats("剩余规模 < 1亿", [d for d in data_list if d['remain'] < 1.0])
    stats("剩余规模 < 2亿", [d for d in data_list if d['remain'] < 2.0])
    stats("剩余规模 < 3亿", [d for d in data_list if d['remain'] < 3.0])
    stats("剩余规模 < 5亿", [d for d in data_list if d['remain'] < 5.0])
    stats("全市场", data_list)

    # 明细
    def details(label, items):
        if not items:
            return
        items_sorted = sorted(items, key=lambda x: x['premium'], reverse=True)
        print(f"\n  {label} 明细（按溢价率降序）:")
        for d in items_sorted[:20]:
            print(f"    {d['code']} {d['name']:8s}  剩余={d['remain']:.2f}亿  发行={d['issue']:.2f}亿  转股价值={d['tv']:7.2f}  溢价率={d['premium']:7.2f}%  价格={d['price']:.2f}")

    details("< 0.5亿", [d for d in data_list if d['remain'] < 0.5])
    details("< 1亿", [d for d in data_list if d['remain'] < 1.0])
    details("1~2亿", [d for d in data_list if 1.0 <= d['remain'] < 2.0])
    details("2~3亿", [d for d in data_list if 2.0 <= d['remain'] < 3.0])

    # 保存cookie
    with open("D:\\Users\\日报\\.jsl_cookie.txt", "w") as f:
        f.write(cookie_str)

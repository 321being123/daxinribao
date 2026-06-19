#!/usr/bin/env python3
"""
直接请求宁稳网简表页面获取可转债数据（含剩余规模）
宁稳网简表URL: https://www.ninwin.cn/index.php?m=cb&show_cb_only=Y&show_listed_only=Y
全表URL: https://www.ninwin.cn/index.php?m=cb&a=cb_all&show_cb_only=Y&show_listed_only=Y
简表不需要登录，全表需要cookie
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.ninwin.cn/",
})

# 先试简表（不需要登录）
url = "https://www.ninwin.cn/index.php?m=cb&show_cb_only=Y&show_listed_only=Y"
resp = s.get(url, timeout=15)
print(f"状态码: {resp.status_code}")
print(f"内容长度: {len(resp.text)}")

# 解析HTML表格
soup = BeautifulSoup(resp.text, 'lxml')
table = soup.find('table', id='cb_hq')
if table:
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"表格行数: {len(rows)}")
        # 打印表头
        thead = table.find('thead')
        if thead:
            ths = thead.find_all('th')
            headers = [th.get_text(strip=True) for th in ths]
            print(f"表头: {headers}")
        # 打印前3行数据
        for row in rows[:3]:
            tds = row.find_all('td')
            vals = [td.get_text(strip=True) for td in tds]
            print(f"  {vals}")
    else:
        print("无tbody")
else:
    print("无id=cb_hq的表格")
    # 看看页面里有什么表格
    tables = soup.find_all('table')
    print(f"页面有 {len(tables)} 个table")
    for i, t in enumerate(tables):
        tid = t.get('id', '')
        cls = t.get('class', '')
        print(f"  table[{i}]: id={tid}, class={cls}")
    # 打印页面前500字符
    print(f"\n页面前1000字符:\n{resp.text[:1000]}")

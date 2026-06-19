#!/usr/bin/env python3
"""测试efinance获取可转债数据（含剩余规模）"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import efinance as ef

# 获取可转债行情数据
df = ef.stock.get_real_bill_info()
print(f"get_real_bill_info: {len(df)}行")
print(f"字段: {list(df.columns)}")
print(df.head(3).to_string())

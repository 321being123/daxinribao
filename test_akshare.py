#!/usr/bin/env python3
"""用akshare bond_cb_jsl获取全量转债数据（含剩余规模），统计小流通妖债溢价率"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak

# bond_cb_jsl 默认只返回30行，检查是否有参数获取更多
import inspect
sig = inspect.signature(ak.bond_cb_jsl)
print(f"bond_cb_jsl 参数: {sig}")

# 尝试调用看能否获取全量
df = ak.bond_cb_jsl()
print(f"\n获取到 {len(df)} 行")
print(f"剩余规模分布:")
print(df['剩余规模'].describe())

"""
从理杏仁导出的CSV导入A股全市场数据到赛道热度数据库
只需要执行一次，后续增量更新由 ipo_daily_report.py 自动完成
"""
import csv
import sqlite3
import os
import sys

# ======== 从 ipo_daily_report.py 复制的必要常量（避免依赖导入） ========
NEW_STOCK_HOT_SECTORS = {
    "光通信": 3.0, "光纤": 3.0, "光子": 2.5,
    "半导体": 2.0, "芯片": 2.0, "集成电路": 2.0, "先进封装": 2.0,
    "AI": 2.5, "人工智能": 2.5, "算力": 2.0, "GPU": 2.5,
    "机器人": 1.5, "人形机器人": 2.0, "具身智能": 2.0,
    "低空经济": 1.5, "飞行汽车": 1.5, "航天": 1.0, "航空": 0.8,
    "储能": 1.0, "新能源": 0.8, "光伏": 0.8, "锂电池": 0.8,
    "创新药": 0.8, "医疗器械": 0.5, "生物医药": 0.5,
    "新材料": 0.5, "高端装备": 0.5, "精密制造": 0.3,
    "军工": 0.8, "自动驾驶": 1.0, "智能驾驶": 1.0,
    "电力设备": 0.3, "轨道交通": 0.3, "核电": 0.5,
    "数字经济": 0.5, "数据要素": 0.5, "云计算": 0.5,
    "氢能": 0.8, "钠离子": 0.8, "固态电池": 1.0,
    "消费电子": 0.3, "汽车电子": 0.5,
}


def _match_sector_by_keywords(search_text):
    """对一段文本匹配所有赛道关键词"""
    matches = []
    for keyword in NEW_STOCK_HOT_SECTORS:
        if keyword in search_text:
            matches.append(keyword)
    return matches


def _init_sector_db(db_path):
    """初始化赛道热度数据库"""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_sector (
            stock_code TEXT,
            sector_key TEXT,
            stock_name TEXT,
            PRIMARY KEY (stock_code, sector_key)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sector_heat (
            sector_key TEXT PRIMARY KEY,
            avg_gain_60d REAL,
            stock_count INTEGER,
            boost REAL,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_gain (
            stock_code TEXT PRIMARY KEY,
            gain_60d REAL,
            updated_at TEXT
        )
    """)
    conn.commit()
    return conn


def import_csv(csv_path):
    """将理杏仁CSV导入数据库"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_heat.db")
    conn = _init_sector_db(db_path)

    # 读取CSV
    with open(csv_path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8-sig")
    reader = csv.reader(text.strip().split("\n"))

    rows = list(reader)
    header = rows[0]
    data_rows = rows[1:]

    print(f"CSV共 {len(data_rows)} 行数据")

    # 列索引
    col_code = 1   # 代码
    col_name = 2   # 公司名称
    col_ind1 = 3   # 一级行业
    col_ind2 = 4   # 二级行业
    col_ind3 = 5   # 三级行业
    col_gain = 7   # 过去60日股价涨跌幅

    stock_sector_cnt = 0
    stock_gain_cnt = 0
    has_gain_cnt = 0

    for row in data_rows:
        if len(row) < 10:
            continue

        # 清洗代码：去掉引号、等号、前缀
        code = row[col_code].strip().replace('"', '').replace('=', '')
        name = row[col_name].strip().replace('"', '').replace('=', '')
        ind1 = row[col_ind1].strip() if len(row) > col_ind1 else ""
        ind2 = row[col_ind2].strip() if len(row) > col_ind2 else ""
        ind3 = row[col_ind3].strip() if len(row) > col_ind3 else ""
        gain_raw = row[col_gain].strip().replace('"', '').replace('=', '') if len(row) > col_gain else ""

        if not code or not name:
            continue

        has_gain_cnt += 1

        # 解析60日涨幅
        gain = None
        try:
            gain = float(gain_raw)
        except (ValueError, TypeError):
            pass

        # --- 匹配赛道关键词（股票简称 + 各级行业） ---
        search_text = f"{name} {ind1} {ind2} {ind3}"
        matched = _match_sector_by_keywords(search_text)
        for sector_key in matched:
            cur = conn.execute(
                "SELECT 1 FROM stock_sector WHERE stock_code=? AND sector_key=?",
                (code, sector_key),
            )
            if not cur.fetchone():
                conn.execute(
                    "INSERT INTO stock_sector (stock_code, sector_key, stock_name) VALUES (?,?,?)",
                    (code, sector_key, name),
                )
                stock_sector_cnt += 1

        # --- 存储60日涨跌幅 ---
        if gain is not None:
            conn.execute(
                "INSERT OR REPLACE INTO stock_gain (stock_code, gain_60d, updated_at) VALUES (?,?,?)",
                (code, gain, "2026-06-19 10:22:00"),
            )
            stock_gain_cnt += 1

    conn.commit()

    print(f"\n导入完成:")
    print(f"  总计股票数: {has_gain_cnt}")
    print(f"  新增股票-赛道映射: {stock_sector_cnt} 条")
    print(f"  新增股票涨幅记录: {stock_gain_cnt} 条")

    # 统计各赛道股票数
    print(f"\n赛道股票分布:")
    rows = conn.execute(
        "SELECT sector_key, COUNT(*) FROM stock_sector GROUP BY sector_key ORDER BY COUNT(*) DESC"
    ).fetchall()
    for sk, cnt in rows:
        print(f"  {sk}: {cnt}只")

    # 计算赛道热度
    print(f"\n计算赛道热度系数...")
    sector_avg_gains = {}
    rows = conn.execute(
        """SELECT ss.sector_key, sg.gain_60d
           FROM stock_sector ss
           JOIN stock_gain sg ON ss.stock_code = sg.stock_code
           WHERE sg.gain_60d IS NOT NULL"""
    ).fetchall()
    for sk, gain in rows:
        if sk not in sector_avg_gains:
            sector_avg_gains[sk] = []
        sector_avg_gains[sk].append(gain)

    # 找最大均值
    max_avg = 1  # 避免除0
    for gains in sector_avg_gains.values():
        if gains:
            avg = sum(gains) / len(gains)
            if avg > max_avg:
                max_avg = avg

    for sector_key, gains in sector_avg_gains.items():
        if not gains:
            continue
        avg_gain = sum(gains) / len(gains)
        boost = round((avg_gain / max_avg) * 3.0, 2) if max_avg > 0 else 0
        conn.execute(
            "INSERT OR REPLACE INTO sector_heat (sector_key, avg_gain_60d, stock_count, boost, updated_at) VALUES (?,?,?,?,?)",
            (sector_key, round(avg_gain, 2), len(gains), boost, "2026-06-19 10:22:00"),
        )

    conn.commit()

    print(f"\n赛道热度排名（按系数降序）:")
    rows = conn.execute(
        "SELECT sector_key, boost, avg_gain_60d, stock_count FROM sector_heat ORDER BY boost DESC"
    ).fetchall()
    for sk, boost, gain, cnt in rows:
        print(f"  {sk}: 系数{boost} ({cnt}只, 60日均值{gain}%)")

    conn.close()
    print("\n导入完成！此后每次跑日报将自动复用这些数据。")


if __name__ == "__main__":
    # 自动查找CSV
    csv_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv") and "理杏仁" not in f]
    if not csv_files:
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
    
    if csv_files:
        csv_path = os.path.join(csv_dir, csv_files[0])
        print(f"找到CSV: {csv_files[0]}")
        import_csv(csv_path)
    else:
        print("未找到CSV文件")

"""
测试：板块因子是否重要
对比有板块基准 vs 无板块基准（统一用250%）的预测误差
"""
import requests, re, sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ipo_daily_report import NEW_STOCK_HOT_SECTORS

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ipo_history.db'))
rows = conn.execute('SELECT security_code,security_name,board_key,ld_close_change,listing_date FROM ipo_history WHERE board_key!="北交所" ORDER BY listing_date DESC LIMIT 20').fetchall()
conn.close()

stocks = []
for code, name, board, actual, date in rows:
    url = f'https://ds.emoney.cn/DataCenter2/datacenter/NewStockXgzl?secucode={code}&type=ss'
    resp = s.get(url, timeout=15)
    rows2 = re.findall(r'<tr>(.*?)</tr>', resp.text, re.DOTALL)
    data = {}
    for row in rows2:
        tds = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in tds]
        for i in range(len(cells)-1):
            data[cells[i]] = cells[i+1]
    def gf(k,d=None):
        try: return float(data.get(k,0) or 0) or d
        except: return d
    ip = gf('发行价格(元／股)')
    os_ = gf('网上发行数量(万股)')
    lr = gf('网上发行中签率(%)')
    mb = data.get('主营业务','')
    ind = data.get('参考行业','') or data.get('所属行业','')
    cmv = os_ * ip / 10000 if os_ and ip else None
    search = f'{data.get("股票简称","")} {mb} {ind}'
    bl, bb = None, 0
    for kw, boost in NEW_STOCK_HOT_SECTORS.items():
        if kw in search and boost > bb:
            bb, bl = boost, kw
    board_map = {'创业板':284,'深市主板':180,'沪市主板':245,'科创板':332}
    bv = board_map.get(board, 200)
    stocks.append({'code':code,'name':name,'board':board,'bv':bv,'ip':ip,'lr':lr,'cmv':cmv,'bl':bl,'bb':bb,'actual':actual})

def predict(st, board_enabled=True):
    base = st['bv'] if board_enabled else 250
    est = float(base)
    if st['bb']:
        est *= (1 + st['bb'] * 0.15)
        if st['bl'] and st['code'].startswith(('688','787')):
            est *= 1.25
            if st['bb'] >= 1.0:
                est *= 1.2
    if st['ip']:
        if st['ip'] < 15: est *= 1.1
        elif st['ip'] > 50: est *= 0.90
    if st['lr']:
        if st['lr'] < 0.02: est *= 1.15
        elif st['lr'] < 0.03: est *= 1.10
        elif st['lr'] > 0.08: est *= 0.92
    if st['cmv']:
        if st['cmv'] < 3: est *= 1.25
        elif st['cmv'] < 6: est *= 1.15
        elif st['cmv'] < 10: est *= 1.05
        elif st['cmv'] > 20: est *= 0.90
    return int(round(est))

print(f"  代码       名称   板块   带板块  无板块  实际")
print("-" * 50)
err_with = err_without = 0
for st in stocks:
    pw = predict(st, True)
    pwo = predict(st, False)
    a = st['actual']
    err_with += abs(pw - a) / a * 100 if a > 0 else 0
    err_without += abs(pwo - a) / a * 100 if a > 0 else 0
    print(f"  {st['code']:>8} {st['name']:<6} {st['board']:<4} {pw:>6}% {pwo:>6}% {a:>6.0f}%")

print()
print(f"带板块平均相对误差: {err_with/20:.1f}%")
print(f"无板块平均相对误差: {err_without/20:.1f}%")
print(f"差异: {err_with/20 - err_without/20:+.1f}个百分点")
print()
print("结论:", end=" ")
diff = err_with/20 - err_without/20
if abs(diff) < 2:
    print("板块因子基本无影响，可以去掉")
elif diff > 0:
    print("无板块反而更好，板块因子拖后腿")
else:
    print("有板块略有帮助，但效果有限")

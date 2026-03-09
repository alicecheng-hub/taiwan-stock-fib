import requests
import json
import os
import time
from datetime import datetime, timedelta

# 確保 data 資料夾存在
os.makedirs('data', exist_ok=True)

STOCK_LIST = [
    '2330', '2454', '2317', '2308', '2382',
    '3711', '2412', '2881', '2882', '5871',
    '2303', '6505', '1303', '1301', '2002',
    '2886', '2891', '3008', '2395', '4938',
    '1583', '2345', '3037', '4966', '6669',
]

def get_monthly_data(stock_id, yyyymm):
    """抓 TWSE 單月K線資料"""
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={yyyymm}01&stockNo={stock_id}"
    try:
        res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data.get('stat') != 'OK' or not data.get('data'):
            return []
        rows = []
        for r in data['data']:
            try:
                date_parts = r[0].split('/')
                year = int(date_parts[0]) + 1911
                date_str = f"{year}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"
                open_p  = float(r[3].replace(',', ''))
                high_p  = float(r[4].replace(',', ''))
                low_p   = float(r[5].replace(',', ''))
                close_p = float(r[6].replace(',', ''))
                rows.append({'date': date_str, 'open': open_p, 'high': high_p, 'low': low_p, 'close': close_p})
            except:
                continue
        return rows
    except Exception as e:
        print(f"  Error fetching {stock_id} {yyyymm}: {e}")
        return []

result = {}
now = datetime.now()

for code in STOCK_LIST:
    try:
        all_rows = []
        # 抓最近4個月
        for i in range(3, -1, -1):
            d = now - timedelta(days=30 * i)
            yyyymm = d.strftime('%Y%m')
            rows = get_monthly_data(code, yyyymm)
            all_rows.extend(rows)
            time.sleep(0.5)  # 避免太快被擋

        # 去重複、排序
        seen = set()
        unique_rows = []
        for r in all_rows:
            if r['date'] not in seen:
                seen.add(r['date'])
                unique_rows.append(r)
        unique_rows.sort(key=lambda x: x['date'])

        if not unique_rows:
            print(f"No data for {code}")
            continue

        closes = [r['close'] for r in unique_rows]
        highs  = [r['high']  for r in unique_rows]
        lows   = [r['low']   for r in unique_rows]

        high = max(highs)
        low  = min(lows)
        current = closes[-1]
        prev = closes[-2] if len(closes) > 1 else current
        change = round((current - prev) / prev * 100, 2)
        rng = high - low

        fib_levels = []
        for ratio in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]:
            fib_levels.append({
                'ratio': ratio,
                'price': round(high - rng * ratio, 2)
            })

        candles = [{'date': r['date'], 'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']} for r in unique_rows[-30:]]

        recent = unique_rows[-9:]
        r9h = max(r['high'] for r in recent)
        r9l = min(r['low']  for r in recent)
        rsv = ((current - r9l) / (r9h - r9l) * 100) if r9h != r9l else 50
        kd  = round(rsv, 1)

        hit_fib = None
        for f in fib_levels[1:-1]:
            if f['price'] > 0 and abs(current - f['price']) / f['price'] * 100 < 4:
                hit_fib = f['ratio']
                break

        result[code] = {
            'code':         code,
            'name':         code,
            'currentPrice': current,
            'change':       change,
            'high':         high,
            'low':          low,
            'kd':           kd,
            'hitFib':       hit_fib,
            'fibLevels':    fib_levels,
            'candles':      candles,
        }

        print(f"OK {code}: {current} ({change:+.2f}%)")

    except Exception as e:
        print(f"Error {code}: {e}")

output = {
    'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'stocks':  result
}

with open('data/stocks.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n完成！共 {len(result)} 支股票")

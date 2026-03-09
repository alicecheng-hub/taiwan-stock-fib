import requests
import json
import os
from datetime import datetime, timedelta

TOKEN = os.environ.get('FINMIND_TOKEN', '')
if not TOKEN:
    raise ValueError('FINMIND_TOKEN secret is not set in GitHub Actions')

BASE = 'https://api.finmindtrade.com/api/v4/data'

# 確保 data 資料夾存在
os.makedirs('data', exist_ok=True)

STOCK_LIST = [
    '2330', '2454', '2317', '2308', '2382',
    '3711', '2412', '2881', '2882', '5871',
    '2303', '6505', '1303', '1301', '2002',
    '2886', '2891', '3008', '2395', '4938',
    '1583', '2345', '3037', '4966', '6669',
]

start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
result = {}

for code in STOCK_LIST:
    try:
        url = f"{BASE}?dataset=TaiwanStockPrice&stock_id={code}&start_date={start_date}&token={TOKEN}"
        res = requests.get(url, timeout=10)
        data = res.json()

        if not data.get('data'):
            print(f"No data for {code}")
            continue

        rows = data['data']
        closes = [float(r['close']) for r in rows]
        highs  = [float(r['max'])   for r in rows]
        lows   = [float(r['min'])   for r in rows]

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

        candles = []
        for r in rows[-30:]:
            candles.append({
                'date':  r['date'],
                'open':  float(r['open']),
                'high':  float(r['max']),
                'low':   float(r['min']),
                'close': float(r['close']),
            })

        recent = rows[-9:]
        r9h = max(float(r['max']) for r in recent)
        r9l = min(float(r['min']) for r in recent)
        rsv = ((current - r9l) / (r9h - r9l) * 100) if r9h != r9l else 50
        kd  = round(rsv, 1)

        hit_fib = None
        for f in fib_levels[1:-1]:
            if abs(current - f['price']) / f['price'] * 100 < 4:
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

print(f"完成！共 {len(result)} 支股票")

import requests
import json
import os
import time
from datetime import datetime, timedelta

os.makedirs('data', exist_ok=True)

STOCK_LIST = [
    '0050','0056','00878','00900','006208',
    '2330','2454','2379','2303','2408',
    '2412','2308','2317','2382','3711',
    '2357','4938','3008','2345','3037',
    '4966','6669','2391','3034','2337',
    '2474','3045','2352','2324','2376',
    '2301','2354','6505','3231','2395',
    '1301','1303','1326','2002','1101',
    '1216','2105','1402','2207','1590',
    '1802','1504','1477','1605','2603',
    '2609','2610','2615','2618','1583',
    '1815','3443','5269','6415','6770',
    '2049','3702','2439',
]
STOCK_LIST = list(dict.fromkeys(STOCK_LIST))

def get_monthly_data(stock_id, yyyymm):
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={yyyymm}01&stockNo={stock_id}"
    try:
        res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data.get('stat') != 'OK' or not data.get('data'):
            return []
        rows = []
        for r in data['data']:
            try:
                dp = r[0].split('/')
                year = int(dp[0]) + 1911
                date_str = f"{year}-{dp[1].zfill(2)}-{dp[2].zfill(2)}"
                vol = int(r[1].replace(',','')) // 1000
                rows.append({
                    'date': date_str,
                    'open':   float(r[3].replace(',','')),
                    'high':   float(r[4].replace(',','')),
                    'low':    float(r[5].replace(',','')),
                    'close':  float(r[6].replace(',','')),
                    'volume': vol,
                })
            except:
                continue
        return rows
    except Exception as e:
        print(f"  Error {stock_id} {yyyymm}: {e}")
        return []

def calc_kd_series(rows, n=9):
    k, d = 50.0, 50.0
    kd_series = []
    for i, r in enumerate(rows):
        window = rows[max(0, i-n+1):i+1]
        h = max(x['high'] for x in window)
        l = min(x['low']  for x in window)
        rsv = ((r['close'] - l) / (h - l) * 100) if h != l else 50
        k = k * 2/3 + rsv * 1/3
        d = d * 2/3 + k   * 1/3
        kd_series.append((round(k,1), round(d,1)))
    return kd_series

result = {}
now = datetime.now()

for code in STOCK_LIST:
    try:
        all_rows = []
        for i in range(4, -1, -1):
            d = now - timedelta(days=30 * i)
            yyyymm = d.strftime('%Y%m')
            rows = get_monthly_data(code, yyyymm)
            all_rows.extend(rows)
            time.sleep(0.3)

        seen = set()
        unique_rows = []
        for r in all_rows:
            if r['date'] not in seen:
                seen.add(r['date'])
                unique_rows.append(r)
        unique_rows.sort(key=lambda x: x['date'])

        if len(unique_rows) < 5:
            print(f"No data for {code}")
            continue

        closes = [r['close']  for r in unique_rows]
        highs  = [r['high']   for r in unique_rows]
        lows   = [r['low']    for r in unique_rows]
        vols   = [r['volume'] for r in unique_rows]

        high = max(highs); low = min(lows)
        current = closes[-1]
        prev = closes[-2] if len(closes) > 1 else current
        change = round((current - prev) / prev * 100, 2)
        rng = high - low

        fib_levels = []
        for ratio in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]:
            fib_levels.append({'ratio': ratio, 'price': round(high - rng * ratio, 2)})

        candles = []
        for r in unique_rows[-30:]:
            candles.append({'date': r['date'], 'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close'], 'volume': r['volume']})

        kd_series = calc_kd_series(unique_rows)
        k_now, d_now = kd_series[-1]
        k_prev, d_prev = kd_series[-2] if len(kd_series) > 1 else (k_now, d_now)
        k_prev2, d_prev2 = kd_series[-3] if len(kd_series) > 2 else (k_prev, d_prev)

        golden_cross = (k_prev2 <= d_prev2) and (k_now > d_now) and (k_now < 60)
        death_cross  = (k_prev2 >= d_prev2) and (k_now < d_now)

        # MA均線（最後一天）
        ma5  = round(sum(closes[-5:])  / min(5,  len(closes)), 2)
        ma20 = round(sum(closes[-20:]) / min(20, len(closes)), 2)
        # 均線黃金交叉
        ma5_prev  = round(sum(closes[-6:-1]) / min(5, len(closes)), 2) if len(closes) >= 6 else ma5
        ma20_prev = round(sum(closes[-21:-1]) / min(20, len(closes)), 2) if len(closes) >= 21 else ma20
        ma_golden = (ma5_prev <= ma20_prev) and (ma5 > ma20)

        # 平均成交量（近5日 vs 近20日）
        avg_vol5  = round(sum(vols[-5:])  / min(5,  len(vols)))
        avg_vol20 = round(sum(vols[-20:]) / min(20, len(vols)))
        vol_surge = vols[-1] > avg_vol20 * 1.5  # 今日量 > 20日均量1.5倍

        hit_fib = None
        for f in fib_levels[1:-1]:
            if f['price'] > 0 and abs(current - f['price']) / f['price'] * 100 < 1.5:
                hit_fib = f['ratio']
                break

        result[code] = {
            'code': code, 'name': code,
            'currentPrice': current, 'change': change,
            'high': high, 'low': low,
            'k': k_now, 'd': d_now,
            'kd': round(k_now, 1),
            'ma5': ma5, 'ma20': ma20,
            'maGolden': ma_golden,
            'goldenCross': golden_cross,
            'deathCross':  death_cross,
            'volSurge': vol_surge,
            'avgVol20': avg_vol20,
            'hitFib': hit_fib, 'fibLevels': fib_levels, 'candles': candles,
        }
        tags = []
        if golden_cross: tags.append('KD黃金交叉')
        if ma_golden:    tags.append('MA黃金交叉')
        if vol_surge:    tags.append('量增')
        print(f"OK {code}: {current} K={k_now:.0f} D={d_now:.0f} {' '.join(tags)}")

    except Exception as e:
        print(f"Error {code}: {e}")

output = {'updated': datetime.now().strftime('%Y-%m-%d %H:%M'), 'stocks': result}
with open('data/stocks.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n完成！共 {len(result)} 支股票")

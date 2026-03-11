import requests
import json
import os
import time
import calendar
from datetime import datetime, timedelta

os.makedirs('data', exist_ok=True)

# 股票資料：代號 -> (名稱, 產業別, 是否上櫃)
# sector 用熱門主題標籤
STOCK_INFO = {
    '0050':  ('元大台灣50',     'ETF',   False),
    '0056':  ('元大高股息',     'ETF',   False),
    '00878': ('國泰永續高股息', 'ETF',   False),
    '00900': ('富邦特選高股息', 'ETF',   False),
    '006208':('富邦台灣50',     'ETF',   False),
    '2330':  ('台積電',         '半導體',False),
    '2454':  ('聯發科',         '半導體',False),
    '2379':  ('瑞昱',           '半導體',False),
    '2303':  ('聯電',           '半導體',False),
    '2408':  ('南亞科',         '半導體',False),
    '2412':  ('中華電',         '電信',  False),
    '2308':  ('台達電',         '散熱',  False),
    '2317':  ('鴻海',           'AI',    False),
    '2382':  ('廣達',           'AI',    False),
    '3711':  ('日月光投控',     '半導體',False),
    '2357':  ('華碩',           'AI',    False),
    '4938':  ('和碩',           'AI',    False),
    '3008':  ('大立光',         '光電',  False),
    '2345':  ('智邦',           '網通',  False),
    '3037':  ('欣興',           'PCB',   False),
    '4966':  ('譜瑞-KY',        '半導體',False),
    '6669':  ('緯穎',           'AI',    False),
    '2391':  ('台研',           '散熱',  False),
    '3034':  ('聯詠',           '半導體',False),
    '2337':  ('旺宏',           '半導體',False),
    '2474':  ('可成',           '傳產',  False),
    '3045':  ('台灣大',         '電信',  False),
    '2352':  ('佳世達',         '傳產',  False),
    '2324':  ('仁寶',           'AI',    False),
    '2376':  ('技嘉',           'AI',    False),
    '2301':  ('光寶科',         '散熱',  False),
    '2354':  ('鴻準',           '散熱',  False),
    '6505':  ('台塑化',         '石化',  False),
    '3231':  ('緯創',           'AI',    False),
    '2395':  ('研華',           '傳產',  False),
    '1301':  ('台塑',           '石化',  False),
    '1303':  ('南亞',           '玻纖布',False),
    '1326':  ('台化',           '石化',  False),
    '2002':  ('中鋼',           '傳產',  False),
    '1101':  ('台泥',           '傳產',  False),
    '1216':  ('統一',           '傳產',  False),
    '2105':  ('正新',           '傳產',  False),
    '1402':  ('遠東新',         '傳產',  False),
    '2207':  ('和泰車',         '傳產',  False),
    '1590':  ('亞德客-KY',      '傳產',  False),
    '1802':  ('台玻',           '傳產',  False),
    '1504':  ('東元',           '傳產',  False),
    '1477':  ('聚陽',           '傳產',  False),
    '1605':  ('華新',           '傳產',  False),
    '2603':  ('長榮',           '海運',  False),
    '2609':  ('陽明',           '海運',  False),
    '2610':  ('華航',           '航空',  False),
    '2615':  ('萬海',           '海運',  False),
    '2618':  ('長榮航',         '航空',  False),
    '1583':  ('程泰',           '傳產',  False),
    '1815':  ('富喬',           '玻纖布',True),
    '3443':  ('創意',           '半導體',False),
    '5269':  ('祥碩',           '半導體',True),
    '6415':  ('矽力-KY',        '半導體',True),
    '6770':  ('力積電',         '半導體',False),
    '2049':  ('上銀',           '傳產',  False),
    '3702':  ('大聯大',         '傳產',  False),
    '2439':  ('美律',           '傳產',  False),
    '2371':  ('大同',           '傳產',  False),
    '8110':  ('華東',           '玻纖布',True),
    '6176':  ('瑞儀',           '光電',  True),
    '6269':  ('台郡',           'PCB',   True),
    '5478':  ('智冠',           '傳產',  True),
    '6585':  ('鼎基',           '傳產',  True),
    '2066':  ('世德',           '傳產',  False),
    '6203':  ('海韻電',         '散熱',  True),
    '6147':  ('頃邦',           '傳產',  True),
    '6182':  ('合晶',           '半導體',True),
    '4909':  ('新復興',         'PCB',   True),
}

STOCK_LIST = list(STOCK_INFO.keys())

def get_monthly_data_twse(stock_id, yyyymm):
    """統一用 TWSE API"""
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


def get_monthly_data_tpex(stock_id, yyyymm):
    """上櫃股票（TPEx）- 用session取得cookie後抓資料"""
    year = int(yyyymm[:4]) - 1911
    month = int(yyyymm[4:6])
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        # 先訪問頁面取得 cookie
        session.get('https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43.php?l=zh-tw',
                    headers=headers, timeout=10)
        time.sleep(0.5)
        timestamp = int(time.time() * 1000)
        api_url = (
            f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/"
            f"st43_result.php?l=zh-tw&d={year}/{month:02d}&stkno={stock_id}&s=0,asc,0&_={timestamp}"
        )
        res = session.get(api_url, headers={
            **headers,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43.php?l=zh-tw',
            'X-Requested-With': 'XMLHttpRequest',
        }, timeout=15)
        if res.status_code != 200:
            print(f"  TPEx HTTP {res.status_code} {stock_id} {yyyymm}")
            return []
        text = res.text.strip()
        if not text or not text.startswith('{'):
            print(f"  TPEx bad response {stock_id} {yyyymm}: {text[:60]}")
            return []
        data = res.json()
        if not data.get('aaData'):
            return []
        rows = []
        for r in data['aaData']:
            try:
                dp = r[0].strip().split('/')
                y = int(dp[0]) + 1911
                d = f"{y}-{dp[1].zfill(2)}-{dp[2].zfill(2)}"
                vol = int(r[1].replace(',','')) // 1000
                rows.append({
                    'date':   d,
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
        print(f"  Error TPEx {stock_id} {yyyymm}: {e}")
        return []


def get_monthly_data(stock_id, yyyymm, is_otc=False):
    if is_otc:
        return get_monthly_data_tpex(stock_id, yyyymm)
    return get_monthly_data_twse(stock_id, yyyymm)

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
    name, sector, is_otc = STOCK_INFO[code]
    try:
        all_rows = []
        for i in range(4, -1, -1):
            dt = now - timedelta(days=30 * i)
            yyyymm = dt.strftime('%Y%m')
            rows = get_monthly_data(code, yyyymm, is_otc)
            all_rows.extend(rows)
            time.sleep(0.4)

        seen = set()
        unique_rows = []
        for r in all_rows:
            if r['date'] not in seen:
                seen.add(r['date'])
                unique_rows.append(r)
        unique_rows.sort(key=lambda x: x['date'])

        if len(unique_rows) < 5:
            print(f"No data for {code} {name}")
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
        k_rising     = (k_prev2 < k_prev < k_now) and (k_now < 40)  # K值止跌回升（低檔連升兩日）

        ma5  = round(sum(closes[-5:])  / min(5,  len(closes)), 2)
        ma20 = round(sum(closes[-20:]) / min(20, len(closes)), 2)
        ma5_prev  = round(sum(closes[-6:-1]) / min(5, len(closes)), 2) if len(closes) >= 6 else ma5
        ma20_prev = round(sum(closes[-21:-1]) / min(20, len(closes)), 2) if len(closes) >= 21 else ma20
        ma_golden = (ma5_prev <= ma20_prev) and (ma5 > ma20)

        avg_vol5  = round(sum(vols[-5:])  / min(5,  len(vols)))
        avg_vol20 = round(sum(vols[-20:]) / min(20, len(vols)))
        vol_surge = vols[-1] > avg_vol20 * 1.5

        hit_fib = None
        for f in fib_levels[1:-1]:
            if f['price'] > 0 and abs(current - f['price']) / f['price'] * 100 < 1.5:
                hit_fib = f['ratio']
                break

        result[code] = {
            'code': code, 'name': name, 'sector': sector,
            'currentPrice': current, 'change': change,
            'high': high, 'low': low,
            'k': k_now, 'd': d_now,
            'kd': round(k_now, 1),
            'ma5': ma5, 'ma20': ma20,
            'maGolden': ma_golden,
            'goldenCross': golden_cross,
            'deathCross':  death_cross,
            'kRising':     k_rising,
            'volSurge': vol_surge,
            'avgVol20': avg_vol20,
            'hitFib': hit_fib, 'fibLevels': fib_levels, 'candles': candles,
        }
        tags = []
        if golden_cross: tags.append('KD黃金交叉')
        if k_rising:     tags.append('K止跌回升')
        if ma_golden:    tags.append('MA黃金交叉')
        if vol_surge:    tags.append('量增')
        market = '上櫃' if is_otc else '上市'
        print(f"OK {code} {name}({market}) [{sector}]: {current} K={k_now:.0f} D={d_now:.0f} {' '.join(tags)}")

    except Exception as e:
        print(f"Error {code} {name}: {e}")

output = {'updated': datetime.now().strftime('%Y-%m-%d %H:%M'), 'stocks': result}
with open('data/stocks.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n完成！共 {len(result)} 支股票")

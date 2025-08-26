from bs4 import BeautifulSoup
import pandas as pd
import requests
from dateutil import parser
import time
import datetime as dt


pd.set_option("display.max_rows", None)


def get_date(c):
    print("📅 [DEBUG] Extracting date from calendar header...")
    tr = c.select_one("tr")
    ths = tr.select("th")
    for th in ths:
        if th.has_attr("colspan"):
            date_text = th.get_text().strip()
            print(f"📅 [DEBUG] Found date text: {date_text}")
            parsed_date = parser.parse(date_text)
            print(f"📅 [DEBUG] Parsed date: {parsed_date}")
            return parsed_date
    print("⚠️ [DEBUG] No date found in header")
    return None
    
def get_data_point(key, element):
    print(f"📊 [DEBUG] Extracting data point for key: {key}")
    for e in['span', 'a']:
        d = element.select_one(f"{e}#{key}")
        if d is not None:
            value = d.get_text()
            print(f"📊 [DEBUG] Found {key}: {value}")
            return value
    print(f"⚠️ [DEBUG] No data found for key: {key}")
    return ''


def get_data_for_key(tr, key):
    print(f"🔍 [DEBUG] Getting data for key: {key}")
    if tr.has_attr(key):
        value = tr.attrs[key]
        print(f"🔍 [DEBUG] Found {key}: {value}")
        return value
    print(f"⚠️ [DEBUG] No attribute found for key: {key}")
    return ''


def get_data_dict(item_date, table_rows):
    print(f"📋 [DEBUG] Processing {len(table_rows)} table rows for date: {item_date}")
    data = []

    for i, tr in enumerate(table_rows):
        print(f"📋 [DEBUG] Processing row {i+1}/{len(table_rows)}")
        
        row_data = dict(
            date=item_date,
            country=get_data_for_key(tr, 'data-country'),
            category=get_data_for_key(tr, 'data-category'),
            event=get_data_for_key(tr, 'data-event'),
            symbol=get_data_for_key(tr, 'data-symbol'),
            actual=get_data_point('actual', tr),
            previous=get_data_point('previous', tr),
            forecast=get_data_point('forecast', tr)
        )
        
        print(f"📋 [DEBUG] Row {i+1} data: {row_data}")
        data.append(row_data)

    print(f"📋 [DEBUG] Processed {len(data)} rows for date {item_date}")
    return data


def get_fx_calendar(from_date):
    print(f"📅 [DEBUG] Starting FX calendar scraping from {from_date}")
    
    session = requests.Session()
    print("🌐 [DEBUG] Created requests session")

    fr_d_str = dt.datetime.strftime(from_date, "%Y-%m-%d 00:00:00")
    to_date = from_date + dt.timedelta(days=6)
    to_d_str = dt.datetime.strftime(to_date, "%Y-%m-%d 00:00:00")
    
    print(f"📅 [DEBUG] Date range: {fr_d_str} to {to_d_str}")
    
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Cookie": f"calendar-importance=3; cal-custom-range={fr_d_str}|{to_d_str}; TEServer=TEIIS3; cal-timezone-offset=0;"
    }
    
    print("🌐 [DEBUG] Headers configured")
    print(f"🌐 [DEBUG] Making request to TradingEconomics calendar...")

    try:
        resp = session.get("https://tradingeconomics.com/calendar", headers=headers)
        print(f"🌐 [DEBUG] Response status code: {resp.status_code}")
        print(f"🌐 [DEBUG] Response content length: {len(resp.content)} bytes")
        
        if resp.status_code != 200:
            print(f"❌ [DEBUG] HTTP error: {resp.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ [DEBUG] Request failed: {e}")
        return []

    print("🔍 [DEBUG] Parsing HTML content...")
    soup = BeautifulSoup(resp.content, 'html.parser')

    table = soup.select_one("table#calendar")
    if not table:
        print("❌ [DEBUG] Calendar table not found")
        return []
    
    print("✅ [DEBUG] Calendar table found")

    last_header_date = None
    trs = {}
    final_data = []

    print("🔍 [DEBUG] Processing table children...")
    for i, c in enumerate(table.children):
        if c.name == 'thead':
            if 'class' in c.attrs and 'hidden-head' in c.attrs['class']:
                print(f"📅 [DEBUG] Skipping hidden header {i+1}")
                continue
            last_header_date = get_date(c)
            trs[last_header_date] = []
            print(f"📅 [DEBUG] New date section: {last_header_date}")
        elif c.name == "tr":
            if last_header_date:
                trs[last_header_date].append(c)
                print(f"📋 [DEBUG] Added row to date {last_header_date}")

    print(f"📅 [DEBUG] Found {len(trs)} date sections")
    
    for item_date, table_rows in trs.items():
        print(f"📅 [DEBUG] Processing {len(table_rows)} rows for {item_date}")
        final_data += get_data_dict(item_date, table_rows)

    print(f"✅ [DEBUG] FX calendar scraping complete. Total events: {len(final_data)}")
    return final_data
    

def fx_calendar():
    print("📅 [DEBUG] Starting batch FX calendar scraping...")
    
    final_data = []

    start = parser.parse("2022-03-07T00:00:00Z")
    end = parser.parse("2022-03-25T00:00:00Z")

    print(f"📅 [DEBUG] Date range: {start} to {end}")

    while start < end:
        print(f"📅 [DEBUG] Scraping week starting: {start}")
        week_data = get_fx_calendar(start)
        final_data += week_data
        print(f"📅 [DEBUG] Week complete. Total events so far: {len(final_data)}")
        start = start + dt.timedelta(days=7)
        time.sleep(1)

    print(f"✅ [DEBUG] Batch scraping complete. Total events: {len(final_data)}")
    print(pd.DataFrame.from_dict(final_data))




























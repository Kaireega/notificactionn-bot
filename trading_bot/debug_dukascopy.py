#!/usr/bin/env python3
"""
Debug script for Dukascopy SWFX Sentiment Index.
"""
import sys
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import requests
from bs4 import BeautifulSoup
import certifi


def analyze_dukascopy_structure():
    """Analyze Dukascopy's HTML structure to understand their data format."""
    print("🔍 Analyzing Dukascopy SWFX Sentiment Index Structure...")
    
    try:
        url = "https://www.dukascopy.com/swiss/english/marketwatch/sentiment/"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        print("   - Making request to Dukascopy...")
        resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=20)
        
        print(f"   - Status code: {resp.status_code}")
        print(f"   - Content length: {len(resp.content)}")
        
        if resp.status_code != 200:
            print(f"   - ❌ HTTP Error: {resp.status_code}")
            return
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Look for sentiment-related content
        print("\n📊 Analyzing page content...")
        
        # Check for sentiment-related text
        text = soup.get_text().lower()
        sentiment_keywords = ['sentiment', 'swfx', 'index', 'bullish', 'bearish', 'long', 'short']
        
        print("   - Sentiment keywords found:")
        for keyword in sentiment_keywords:
            if keyword in text:
                print(f"     ✅ {keyword}")
            else:
                print(f"     ❌ {keyword}")
        
        # Look for currency pairs
        currency_pairs = ['eur/usd', 'gbp/usd', 'usd/jpy', 'usd/chf', 'aud/usd', 'usd/cad']
        print("\n   - Currency pairs found:")
        for pair in currency_pairs:
            if pair in text:
                print(f"     ✅ {pair}")
            else:
                print(f"     ❌ {pair}")
        
        # Look for tables
        tables = soup.find_all('table')
        print(f"\n   - Tables found: {len(tables)}")
        
        for i, table in enumerate(tables[:3]):  # Show first 3 tables
            print(f"     Table {i+1}:")
            rows = table.find_all('tr')
            print(f"       Rows: {len(rows)}")
            if rows:
                first_row = rows[0]
                cells = first_row.find_all(['td', 'th'])
                print(f"       First row cells: {len(cells)}")
                if cells:
                    print(f"       First cell content: {cells[0].get_text().strip()[:50]}...")
        
        # Look for divs with sentiment-related classes
        sentiment_divs = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['sentiment', 'swfx', 'index', 'market']))
        print(f"\n   - Sentiment-related divs: {len(sentiment_divs)}")
        
        for i, div in enumerate(sentiment_divs[:3]):  # Show first 3
            print(f"     Div {i+1} class: {div.get('class', 'No class')}")
            print(f"       Content preview: {div.get_text().strip()[:100]}...")
        
        # Look for any widgets or iframes
        iframes = soup.find_all('iframe')
        print(f"\n   - Iframes found: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get('src', 'No src')
            print(f"     Iframe {i+1}: {src}")
        
        # Look for JavaScript that might load sentiment data
        scripts = soup.find_all('script')
        sentiment_scripts = []
        for script in scripts:
            script_content = script.get_text().lower()
            if any(word in script_content for word in ['sentiment', 'swfx', 'index']):
                sentiment_scripts.append(script)
        
        print(f"\n   - Sentiment-related scripts: {len(sentiment_scripts)}")
        
        # Look for any data attributes or JSON
        data_elements = soup.find_all(attrs={'data-sentiment': True})
        print(f"\n   - Elements with data-sentiment: {len(data_elements)}")
        
        # Check for any API endpoints or data URLs
        links = soup.find_all('a', href=True)
        sentiment_links = []
        for link in links:
            href = link.get('href', '').lower()
            if any(word in href for word in ['sentiment', 'swfx', 'api', 'data']):
                sentiment_links.append(link)
        
        print(f"\n   - Sentiment-related links: {len(sentiment_links)}")
        for link in sentiment_links[:3]:
            href = link.get('href', '')
            text = link.get_text().strip()
            print(f"     Link: {href} - {text}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"   - ❌ Error: {e}")


if __name__ == "__main__":
    analyze_dukascopy_structure()

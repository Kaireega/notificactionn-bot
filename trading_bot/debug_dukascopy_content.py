#!/usr/bin/env python3
"""
Debug script to see exact Dukascopy content.
"""
import sys
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import requests
from bs4 import BeautifulSoup
import certifi
import re


def debug_dukascopy_content():
    """Debug the exact content from Dukascopy."""
    print("🔍 Debugging Dukascopy Content...")
    
    try:
        url = "https://www.dukascopy.com/swiss/english/marketwatch/sentiment/"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        print("   - Making request to Dukascopy...")
        resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=20)
        
        if resp.status_code != 200:
            print(f"   - ❌ HTTP Error: {resp.status_code}")
            return
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        text = soup.get_text()
        
        print(f"   - Content length: {len(text)}")
        
        # Look for currency pairs in the text
        currency_patterns = [
            r'EUR/USD',
            r'GBP/USD', 
            r'USD/JPY',
            r'USD/CHF',
            r'AUD/USD',
            r'USD/CAD',
            r'EUR/GBP',
            r'EUR/JPY',
            r'GBP/JPY',
            r'NZD/USD'
        ]
        
        print("\n📊 Currency pairs found:")
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"   ✅ {pattern}: {len(matches)} matches")
                # Show context around first match
                first_match = re.search(pattern, text, re.IGNORECASE)
                if first_match:
                    start = max(0, first_match.start() - 50)
                    end = min(len(text), first_match.end() + 50)
                    context = text[start:end]
                    print(f"      Context: ...{context}...")
            else:
                print(f"   ❌ {pattern}: No matches")
        
        # Look for sentiment keywords
        sentiment_keywords = ['bullish', 'bearish', 'neutral', 'long', 'short', 'sentiment']
        print("\n📊 Sentiment keywords found:")
        for keyword in sentiment_keywords:
            matches = re.findall(keyword, text, re.IGNORECASE)
            if matches:
                print(f"   ✅ {keyword}: {len(matches)} matches")
                # Show context around first match
                first_match = re.search(keyword, text, re.IGNORECASE)
                if first_match:
                    start = max(0, first_match.start() - 50)
                    end = min(len(text), first_match.end() + 50)
                    context = text[start:end]
                    print(f"      Context: ...{context}...")
            else:
                print(f"   ❌ {keyword}: No matches")
        
        # Look for percentage patterns
        percentage_pattern = r'\d+%'
        percentages = re.findall(percentage_pattern, text)
        print(f"\n📊 Percentage patterns found: {len(percentages)}")
        if percentages:
            print("   Sample percentages:")
            for i, pct in enumerate(percentages[:10]):
                print(f"      {pct}")
        
        # Look for any text that might contain sentiment data
        print("\n📊 Potential sentiment data sections:")
        
        # Look for sections with both currency pairs and percentages
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(pair in line for pair in ['EUR/USD', 'GBP/USD', 'USD/JPY']) and '%' in line:
                print(f"   Line {i}: {line.strip()}")
        
        print("\n✅ Debug complete!")
        
    except Exception as e:
        print(f"   - ❌ Error: {e}")


if __name__ == "__main__":
    debug_dukascopy_content()

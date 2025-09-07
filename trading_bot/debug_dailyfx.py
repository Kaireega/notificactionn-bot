#!/usr/bin/env python3
"""
Debug script for DailyFX scraping.
"""
import sys
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from scraping.dailyfx_com import dailyfx_com
import requests
from bs4 import BeautifulSoup
import certifi


def test_dailyfx_direct():
    """Test DailyFX scraping directly."""
    print("🔍 Testing DailyFX scraping directly...")
    
    try:
        print("   - Making request to DailyFX...")
        resp = requests.get("https://www.dailyfx.com/sentiment", verify=certifi.where(), timeout=20)
        
        print(f"   - Status code: {resp.status_code}")
        print(f"   - Content length: {len(resp.content)}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Try different selectors
            selectors = [
                ".dfx-technicalSentimentCard",
                ".dfx-technicalSentimentCard__pairAndSignal",
                ".dfx-technicalSentimentCard__changeValue"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"   - Selector '{selector}': {len(elements)} elements found")
                
                if elements:
                    print(f"     First element: {elements[0]}")
                    break
        else:
            print(f"   - ❌ HTTP Error: {resp.status_code}")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")


def test_dailyfx_function():
    """Test the dailyfx_com function."""
    print("\n📊 Testing dailyfx_com function...")
    
    try:
        result = dailyfx_com()
        print(f"   - Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   - Keys: {list(result.keys())}")
            print(f"   - Sentiment: {result.get('sentiment', 'N/A')}")
            print(f"   - Data length: {len(result.get('data', []))}")
            
            if result.get('data'):
                print(f"   - First pair: {result['data'][0]}")
        else:
            print(f"   - ⚠️ Unexpected type: {type(result)}")
            print(f"   - Content: {result}")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")


if __name__ == "__main__":
    test_dailyfx_direct()
    test_dailyfx_function()


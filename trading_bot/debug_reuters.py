#!/usr/bin/env python3
"""
Debug script for Reuters scraping.
"""
import sys
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from scraping.bloomberg_com import bloomberg_com
import requests
from bs4 import BeautifulSoup
import cloudscraper
import certifi


def test_reuters_direct():
    """Test Reuters scraping directly."""
    print("🔍 Testing Reuters scraping directly...")
    
    try:
        s = cloudscraper.create_scraper()
        
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
        }
        
        print("   - Making request to Reuters...")
        resp = s.get("https://www.reuters.com/business/finance/", headers=headers, verify=certifi.where(), timeout=20)
        
        print(f"   - Status code: {resp.status_code}")
        print(f"   - Content length: {len(resp.content)}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Try different selectors
            selectors = [
                '[class^="media-story-card__body"]',
                '.media-story-card__body',
                '[data-testid="Heading"]',
                'h3',
                'a[href*="/business/"]'
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


def test_bloomberg_function():
    """Test the bloomberg_com function."""
    print("\n📰 Testing bloomberg_com function...")
    
    try:
        result = bloomberg_com()
        print(f"   - Result type: {type(result)}")
        print(f"   - Result length: {len(result)}")
        
        if result:
            print(f"   - First item: {result[0]}")
        else:
            print("   - ⚠️ Empty result")
            
    except Exception as e:
        print(f"   - ❌ Error: {e}")


if __name__ == "__main__":
    test_reuters_direct()
    test_bloomberg_function()



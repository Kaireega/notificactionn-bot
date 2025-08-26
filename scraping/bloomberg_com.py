from bs4 import BeautifulSoup
import cloudscraper
import certifi
import requests

def get_article(card):
    print("📰 [DEBUG] Extracting article data from card...")
    
    if not card:
        print("⚠️ [DEBUG] No card provided")
        return None
        
    headline = card.get_text()
    link = 'https://www.reuters.com' + card.get('href')
    
    article_data = dict(
        headline=headline,
        link=link
    )
    
    print(f"📰 [DEBUG] Article: {headline[:50]}...")
    print(f"📰 [DEBUG] Link: {link}")
    
    return article_data


def bloomberg_com():
    print("📰 [DEBUG] Starting Bloomberg/Reuters news scraping...")
    
    print("🌐 [DEBUG] Creating cloudscraper instance...")
    s = cloudscraper.create_scraper()
    print("✅ [DEBUG] Cloudscraper created")

    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    }
    print("🌐 [DEBUG] Headers configured")

    print("🌐 [DEBUG] Making request to Reuters finance page...")
    print("🌐 [DEBUG] Using cloudscraper to bypass anti-bot protection...")
    
    try:
        # Use CA bundle verification
        resp = s.get("https://www.reuters.com/business/finance/", headers=headers, verify=certifi.where())
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

    # Multiple selector strategies for different site structures
    selector_strategies = [
        # Strategy 1: Original media story cards
        {
            'name': 'media-story-card',
            'container_selector': '[class^="media-story-card__body"]',
            'link_selector': 'a[data-testid="Heading"]'
        },
        # Strategy 2: Story card variations
        {
            'name': 'story-card-variant',
            'container_selector': '[class*="story-card"]',
            'link_selector': 'a'
        },
        # Strategy 3: Article containers
        {
            'name': 'article-container',
            'container_selector': 'article',
            'link_selector': 'a[data-testid="Link"]'
        },
        # Strategy 4: Generic news containers
        {
            'name': 'news-container',
            'container_selector': '[class*="news"], [class*="article"]',
            'link_selector': 'a'
        },
        # Strategy 5: Headlines with h3/h2 tags
        {
            'name': 'headline-tags',
            'container_selector': 'h2, h3',
            'link_selector': 'a'
        },
        # Strategy 6: Data modules
        {
            'name': 'data-module',
            'container_selector': '[data-module*="story"], [data-module*="article"]',
            'link_selector': 'a'
        }
    ]

    links = []
    
    for strategy in selector_strategies:
        print(f"🔍 [DEBUG] Trying strategy: {strategy['name']}")
        
        try:
            containers = soup.select(strategy['container_selector'])
            print(f"📰 [DEBUG] Found {len(containers)} containers with {strategy['name']} strategy")
            
            if not containers:
                continue
                
            for i, container in enumerate(containers[:10]):  # Limit to first 10 for performance
                print(f"📰 [DEBUG] Processing container {i+1}/{min(len(containers), 10)} for {strategy['name']}")
                
                try:
                    # Find link within container
                    link_element = container.select_one(strategy['link_selector'])
                    if not link_element:
                        # Fallback: any link in container
                        link_element = container.find('a')
                    
                    if not link_element:
                        print(f"⚠️ [DEBUG] No link found in container {i+1}")
                        continue
                    
                    # Extract article data
                    href = link_element.get('href', '')
                    if not href:
                        print(f"⚠️ [DEBUG] No href found in link {i+1}")
                        continue
                    
                    # Handle relative URLs
                    if href.startswith('/'):
                        href = 'https://www.reuters.com' + href
                    elif not href.startswith('http'):
                        continue
                    
                    # Get headline text
                    headline_text = link_element.get_text(strip=True)
                    if not headline_text:
                        # Try to get text from parent container
                        headline_text = container.get_text(strip=True)[:100]
                    
                    if headline_text and len(headline_text) > 10:  # Ensure meaningful content
                        article_data = {
                            'headline': headline_text,
                            'link': href,
                            'strategy': strategy['name']
                        }
                        
                        # Avoid duplicates
                        if not any(article['link'] == href for article in links):
                            links.append(article_data)
                            print(f"📰 [DEBUG] Added article {len(links)}: {headline_text[:50]}...")
                    
                except Exception as e:
                    print(f"❌ [DEBUG] Error processing container {i+1} for {strategy['name']}: {e}")
                    continue
            
            # If we found articles with this strategy, we can stop trying others
            if links:
                print(f"✅ [DEBUG] Successfully found articles using {strategy['name']} strategy")
                break
                
        except Exception as e:
            print(f"❌ [DEBUG] Error with strategy {strategy['name']}: {e}")
            continue

    # If no articles found, try a final fallback approach
    if not links:
        print("🔍 [DEBUG] Trying fallback approach: all links on page")
        try:
            all_links = soup.find_all('a', href=True)
            print(f"📰 [DEBUG] Found {len(all_links)} total links on page")
            
            finance_keywords = ['finance', 'economy', 'market', 'business', 'trade', 'currency', 'forex']
            
            for link in all_links[:50]:  # Check first 50 links
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if (href and text and len(text) > 20 and 
                    any(keyword in text.lower() for keyword in finance_keywords)):
                    
                    if href.startswith('/'):
                        href = 'https://www.reuters.com' + href
                    elif not href.startswith('http'):
                        continue
                    
                    article_data = {
                        'headline': text,
                        'link': href,
                        'strategy': 'fallback'
                    }
                    
                    if not any(article['link'] == href for article in links):
                        links.append(article_data)
                        print(f"📰 [DEBUG] Added fallback article: {text[:50]}...")
                        
                        if len(links) >= 5:  # Limit fallback results
                            break
                            
        except Exception as e:
            print(f"❌ [DEBUG] Error in fallback approach: {e}")

    print(f"✅ [DEBUG] Bloomberg/Reuters scraping complete. Retrieved {len(links)} articles")
    return links


    
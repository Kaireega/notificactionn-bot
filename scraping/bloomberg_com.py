from bs4 import BeautifulSoup
import cloudscraper
import certifi
import requests

def get_article(card):
    return dict(
        headline=card.get_text(),
        link='https://www.reuters.com' + card.get('href')
    )


def bloomberg_com():

    s = cloudscraper.create_scraper()

    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    }

    # Use CA bundle verification
    resp = s.get("https://www.reuters.com/business/finance/", headers=headers, verify=certifi.where())

    soup = BeautifulSoup(resp.content, 'html.parser')

    links = []
    cards = soup.select('[class^="media-story-card__body"]')
    for card in cards:
        ca = card.find('a', {'data-testid': 'Heading'})
        links.append(get_article(ca))
    return links


    
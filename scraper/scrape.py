#!/usr/bin/env python3
"""
BUzz Metrics Scraper - Sprint 1
Fetches the BUzz homepage and extracts article links.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_buzz_homepage():
    """
    Fetch BUzz homepage and extract article links.
    Returns list of tuples: (headline, url)
    """
    url = "https://buzz.bournemouth.ac.uk/"

    try:
        print(f"Fetching {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Find all article links
        # BUzz typically uses article cards with headlines in <h2> or <h3> tags
        # and links within the main content area
        articles = []
        seen_urls = set()

        # Strategy: Look for article headlines with links
        # Common patterns: <h2><a>, <h3><a>, article tags, etc.

        # Try finding article containers first
        article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in str(x).lower() or 'article' in str(x).lower() or 'card' in str(x).lower()))

        if article_containers:
            print(f"Found {len(article_containers)} potential article containers")

            for container in article_containers:
                # Look for headline link within container
                headline_elem = container.find(['h1', 'h2', 'h3', 'h4'])

                if headline_elem:
                    link = headline_elem.find('a')
                    if not link:
                        # Sometimes the link wraps the headline container
                        parent = headline_elem.find_parent('a')
                        if parent:
                            link = parent

                    if link and link.get('href'):
                        href = link.get('href')
                        full_url = urljoin(url, href)
                        headline = headline_elem.get_text(strip=True)

                        # Deduplicate
                        if full_url not in seen_urls and headline:
                            articles.append((headline, full_url))
                            seen_urls.add(full_url)

        # Fallback: if no article containers found, look for all h2/h3 with links
        if not articles:
            print("No article containers found, using fallback method...")

            for heading in soup.find_all(['h2', 'h3']):
                link = heading.find('a')
                if not link:
                    link = heading.find_parent('a')

                if link and link.get('href'):
                    href = link.get('href')
                    full_url = urljoin(url, href)
                    headline = heading.get_text(strip=True)

                    # Filter out navigation/footer links
                    if headline and full_url not in seen_urls:
                        # Only include if URL looks like an article
                        if '/20' in full_url or 'buzz.bournemouth.ac.uk' in full_url:
                            articles.append((headline, full_url))
                            seen_urls.add(full_url)

        return articles

    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []


def main():
    print("=" * 80)
    print("BUzz Metrics Scraper - Sprint 1")
    print("=" * 80)
    print()

    articles = scrape_buzz_homepage()

    if not articles:
        print("No articles found.")
        return

    print(f"\nFound {len(articles)} unique articles")
    print("\nFirst 10 articles:")
    print("-" * 80)

    for i, (headline, url) in enumerate(articles[:10], 1):
        print(f"\n{i}. {headline}")
        print(f"   {url}")

    print("\n" + "=" * 80)
    print(f"Total articles scraped: {len(articles)}")
    print("=" * 80)


if __name__ == "__main__":
    main()

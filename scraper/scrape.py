#!/usr/bin/env python3
"""
BUzz Metrics Scraper - Sprint 2
Scrapes front page and first page of category sections to extract article metadata.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import re
from datetime import datetime
from collections import defaultdict


BASE_URL = "https://buzz.bournemouth.ac.uk"

# Pages to scrape
PAGES = [
    BASE_URL,
    f"{BASE_URL}/category/sport/",
    f"{BASE_URL}/category/news-top/",
    f"{BASE_URL}/category/local/",
    f"{BASE_URL}/category/lifestyle/"
]

# Valid newsday date ranges (Mon-Fri only)
VALID_NEWSDAY_RANGES = [
    ("2026-01-12", "2026-01-16"),  # Week 1
    ("2026-01-19", "2026-01-23"),  # Week 2
    ("2026-01-26", "2026-01-30"),  # Week 3
]

# Category normalization map
CATEGORY_MAP = {
    # Sport
    "AFC Bournemouth": "Sport",
    "Men's Football": "Sport",
    "Local Football": "Sport",
    "Tennis": "Sport",
    "Boxing": "Sport",
    "Rugby Union": "Sport",
    "Rugby League": "Sport",
    "Cricket": "Sport",
    "Formula 1": "Sport",
    "Golf": "Sport",
    "Sport": "Sport",
    "Opinion & Analysis": "Sport",

    # News
    "News Top": "News",
    "Local": "News",
    "National": "News",
    "World": "News",
    "Bournemouth": "News",
    "Dorset": "News",
    "Poole": "News",
    "Campus": "News",

    # Features
    "New Features": "Features",
    "Lifestyle": "Features",
    "Health": "Features",
    "Entertainment": "Features",
    "Technology": "Features",
    "Sustainability": "Features",
    "Features": "Features",
    "Fashion": "Features",
    "1st News": "News",
}


def is_valid_newsday(date_str):
    """
    Check if article date falls within valid newsday ranges (Mon-Fri only).
    """
    if not date_str:
        return False

    try:
        article_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        for start_str, end_str in VALID_NEWSDAY_RANGES:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

            if start_date <= article_date <= end_date:
                return True

        return False
    except:
        return False


def scrape_page_for_articles(url):
    """
    Scrape a page and return article URLs.
    """
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        article_urls = []

        # Find article containers
        article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in str(x).lower() or 'article' in str(x).lower() or 'card' in str(x).lower()))

        for container in article_containers:
            # Look for headline link
            headline_elem = container.find(['h1', 'h2', 'h3', 'h4'])

            if headline_elem:
                link = headline_elem.find('a')
                if not link:
                    parent = headline_elem.find_parent('a')
                    if parent:
                        link = parent

                if link and link.get('href'):
                    full_url = urljoin(BASE_URL, link.get('href'))
                    # Only include article URLs
                    if '/20' in full_url and 'buzz.bournemouth.ac.uk' in full_url:
                        article_urls.append(full_url)

        print(f"  Found {len(article_urls)} articles")
        return article_urls

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []


def extract_article_metadata(url):
    """
    Fetch an article and extract metadata.
    Returns dict with article info or None.
    """
    try:
        time.sleep(0.5)  # Rate limiting

        print(f"  Extracting: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract headline
        headline_elem = soup.find('h1', class_=lambda x: x and 'title' in str(x).lower())
        if not headline_elem:
            headline_elem = soup.find('h1')
        headline = headline_elem.get_text(strip=True) if headline_elem else "Unknown"

        # Extract author from byline
        author = "Unknown"

        # First try to find author link in byline
        byline_container = soup.find('div', class_=lambda x: x and 'author' in str(x).lower())
        if byline_container:
            author_link = byline_container.find('a', href=re.compile(r'/author/'))
            if author_link:
                author_text = author_link.get_text(strip=True)
                # Remove "View all posts by" prefix if present
                author = re.sub(r'^View all posts by\s+', '', author_text, flags=re.IGNORECASE)

        # Try meta tag for JSON-LD schema
        if author == "Unknown":
            # Look for JSON-LD schema with author info
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        if isinstance(data['author'], dict) and 'name' in data['author']:
                            author = data['author']['name']
                            break
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and '@type' in item and item['@type'] == 'Person':
                                if 'name' in item:
                                    author = item['name']
                                    break
                except:
                    continue

        # Try searching for "by [Name]" pattern in visible text
        if author == "Unknown":
            byline_elem = soup.find(string=re.compile(r'\bby\s+[A-Z]', re.IGNORECASE))
            if byline_elem:
                # Make sure it's not in a script tag
                if byline_elem.find_parent('script') is None:
                    byline_text = byline_elem.strip()
                    match = re.search(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', byline_text)
                    if match:
                        author = match.group(1).strip()

        # Check if generic author
        generic_authors = ['editor green', 'editor', 'buzz', 'staff']
        if author.lower() in generic_authors:
            author = "Unknown"

        # Extract date and time from byline or meta
        article_date = None
        article_time = None

        # Try to find date in <time> tag
        date_elem = soup.find('time')
        if date_elem:
            datetime_str = date_elem.get('datetime')
            if datetime_str:
                try:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    article_date = dt.strftime('%Y-%m-%d')
                    article_time = dt.strftime('%H:%M')
                except:
                    pass

        # Fallback: search for date in text
        if not article_date:
            date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')
            date_match = date_pattern.search(soup.get_text())
            if date_match:
                date_str = date_match.group(0)
                # Parse date
                formats = ["%B %d, %Y", "%b %d, %Y"]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str.strip(), fmt)
                        article_date = dt.strftime('%Y-%m-%d')
                        break
                    except:
                        continue

        # Extract category from "Category:" line
        category = "Unknown"
        category_elem = soup.find(string=re.compile(r'Category:', re.IGNORECASE))
        if category_elem:
            # Find the next link after "Category:"
            parent = category_elem.find_parent()
            if parent:
                cat_link = parent.find_next('a')
                if cat_link:
                    category = cat_link.get_text(strip=True)

        # Fallback: look for category in URL
        if category == "Unknown":
            if '/category/' in url:
                cat_match = re.search(r'/category/([^/]+)/', url)
                if cat_match:
                    category = cat_match.group(1).replace('-', ' ').title()

        # Detect Shorthand embed
        content_type = "standard"
        word_count = None

        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
        if iframe:
            content_type = "shorthand"
            word_count = None
        else:
            # Count words in article body paragraphs
            # Find main content area
            article_body = soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in str(x).lower() or 'entry' in str(x).lower()))

            if article_body:
                # Remove script, style, nav, footer, aside elements
                for tag in article_body(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    tag.decompose()

                # Count words in paragraphs
                paragraphs = article_body.find_all('p')
                text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                words = text.split()
                word_count = len(words) if words else None

        # Map category to primary category
        category_primary = CATEGORY_MAP.get(category, "News")  # Default to "News"

        return {
            'headline': headline,
            'url': url,
            'author': author,
            'date': article_date,
            'time': article_time,
            'category': category,
            'category_primary': category_primary,
            'word_count': word_count,
            'content_type': content_type
        }

    except requests.RequestException as e:
        print(f"  Error extracting {url}: {e}")
        return None


def main():
    print("=" * 80)
    print("BUzz Metrics Scraper - Sprint 2")
    print("=" * 80)
    print()

    # Collect all article URLs from pages
    all_urls = set()

    for page_url in PAGES:
        urls = scrape_page_for_articles(page_url)
        all_urls.update(urls)

    print(f"\n{'-' * 80}")
    print(f"Total unique article URLs found: {len(all_urls)}")
    print(f"{'-' * 80}\n")

    # Extract metadata for each article
    articles = []
    for url in sorted(all_urls):
        metadata = extract_article_metadata(url)
        if metadata:
            # Filter by valid newsday dates
            if is_valid_newsday(metadata['date']):
                articles.append(metadata)

    print(f"\n{'-' * 80}")
    print(f"Successfully extracted: {len(articles)} articles (from valid newsdays)")
    print(f"{'-' * 80}\n")

    # Sort articles by date
    articles.sort(key=lambda x: (x['date'] if x['date'] else '', x['headline']))

    # Generate statistics
    by_day = defaultdict(int)
    by_category = defaultdict(int)
    by_category_primary = defaultdict(int)
    by_author = defaultdict(int)
    word_counts = []
    shorthand_count = 0
    standard_count = 0

    for article in articles:
        if article['date']:
            by_day[article['date']] += 1
        by_category[article['category']] += 1
        by_category_primary[article['category_primary']] += 1
        by_author[article['author']] += 1

        if article['content_type'] == 'shorthand':
            shorthand_count += 1
        else:
            standard_count += 1
            if article['word_count']:
                word_counts.append(article['word_count'])

    # Save to JSON
    output = {
        'scrape_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_articles': len(articles),
        'articles': articles
    }

    output_path = '../data/metrics_raw.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 80)
    print("BUzz Scraper Summary - Week 1 (Jan 12-16, 2026)")
    print("=" * 80)
    print(f"\nTotal Articles: {len(articles)}")

    print("\nBy Day:")
    day_names = {
        '2026-01-12': 'Sun 12 Jan',
        '2026-01-13': 'Mon 13 Jan',
        '2026-01-14': 'Tue 14 Jan',
        '2026-01-15': 'Wed 15 Jan',
        '2026-01-16': 'Thu 16 Jan',
    }
    for date in sorted(by_day.keys()):
        day_name = day_names.get(date, date)
        print(f"  {day_name}: {by_day[date]}")

    print("\nBy Category (Primary):")
    for cat in sorted(by_category_primary.keys(), key=lambda x: by_category_primary[x], reverse=True):
        print(f"  {cat}: {by_category_primary[cat]}")

    print("\nBy Original Category:")
    for category in sorted(by_category.keys(), key=lambda x: by_category[x], reverse=True):
        print(f"  {category}: {by_category[category]}")

    print("\nTop Authors:")
    for author in sorted(by_author.keys(), key=lambda x: by_author[x], reverse=True)[:10]:
        print(f"  {author}: {by_author[author]}")

    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        print(f"\nAvg Word Count: {avg_words:.0f} (excluding Shorthand)")

    print(f"\nContent Types:")
    print(f"  Standard articles: {standard_count}")
    print(f"  Shorthand embeds: {shorthand_count}")

    # Print sample articles
    print(f"\nSample Articles (first 3):")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article['headline']}")
        print(f"   URL: {article['url']}")
        print(f"   Author: {article['author']}")
        print(f"   Date: {article['date']} | Time: {article['time']}")
        print(f"   Category: {article['category']} → {article['category_primary']}")
        print(f"   Word Count: {article['word_count']}")
        print(f"   Content Type: {article['content_type']}")

    print(f"\nData saved to {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

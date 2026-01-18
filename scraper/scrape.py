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
import gender_guesser.detector as gender
import hashlib


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


def get_gender(full_name):
    """
    Extract first name and guess gender.
    Returns: 'male', 'female', or 'unknown'
    """
    d = gender.Detector()

    # Skip titles
    titles = ['councillor', 'cllr', 'dr', 'detective', 'chief', 'inspector',
              'sergeant', 'professor', 'mr', 'mrs', 'ms', 'miss', 'sir', 'dame']

    words = full_name.split()

    # Find first word that's not a title
    first_name = None
    for word in words:
        if word.lower() not in titles:
            first_name = word
            break

    if not first_name:
        return 'unknown'

    result = d.get_gender(first_name)

    # Map gender-guesser results
    if result in ['male', 'mostly_male']:
        return 'male'
    elif result in ['female', 'mostly_female']:
        return 'female'
    else:
        return 'unknown'


def deduplicate_sources(sources):
    """
    Deduplicate sources by name.
    Prefer longer/more complete names. Merge names where one is a subset of another.
    """
    unique = []

    for source in sources:
        name = source['name']
        name_lower = name.lower().strip()

        # Check if this name is a duplicate or substring of an existing name
        merged = False
        for i, existing in enumerate(unique):
            existing_lower = existing['name'].lower().strip()

            # Exact match (case-insensitive)
            if existing_lower == name_lower:
                merged = True
                break
            # If new name contains existing (e.g., "Becca Parker" contains "Becca")
            elif existing_lower in name_lower and existing_lower != name_lower:
                # Replace with longer name
                unique[i] = source
                merged = True
                break
            # If existing contains new name (e.g., existing "Becca Parker", new "Becca")
            elif name_lower in existing_lower and existing_lower != name_lower:
                # Keep existing (longer) name
                merged = True
                break
            # Check surname match for different first names
            elif len(name.split()) > 1 and len(existing['name'].split()) > 1:
                surname = name.split()[-1].lower()
                existing_surname = existing['name'].split()[-1].lower()
                if surname == existing_surname:
                    # Same surname, prefer the one we have (keep first occurrence)
                    merged = True
                    break

        if not merged:
            unique.append(source)

    return unique


def extract_quoted_sources(text):
    """
    Returns list of sources with evidence and gender.
    """
    sources = []

    # Step 1: Find all quotes with their positions
    # Match curly and straight quotes (using explicit Unicode escapes)
    # Use [^\n] instead of . to prevent matching across paragraph boundaries
    quote_pattern = r'["\u201C\u201D]([^\n"\u201C\u201D]+?)["\u201C\u201D]'

    for match in re.finditer(quote_pattern, text):
        quote_text = match.group(1)
        quote_start = match.start()
        quote_end = match.end()

        # Skip very short quotes (likely not actual quotes)
        if len(quote_text) < 10:
            continue

        # Skip quotes that are just attribution (e.g., " Wilder said. ")
        attribution_words = ['said', 'says', 'explained', 'explains', 'added', 'adds',
                           'told', 'tells', 'noted', 'argued', 'claimed', 'commented',
                           'stated', 'remarked', 'announced', 'confirmed', 'revealed']
        quote_lower = quote_text.lower().strip()
        # If the quote is mostly just "Name said." or similar, skip it
        word_count_quote = len(quote_text.split())
        if word_count_quote < 5 and any(attr in quote_lower for attr in attribution_words):
            continue

        # Step 2: Get context (100 chars before and after)
        context_before = text[max(0, quote_start-100):quote_start]
        context_after = text[quote_end:min(len(text), quote_end+100)]

        # Step 3: Look for attribution AFTER quote
        # Pattern: [quote], said/says/etc [Capitalised Name]
        # Pattern: [quote]. [Capitalised Name] said/added/etc
        # Improved name pattern to capture full names (allows multiple words, hyphens, etc.)
        name_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3})'

        after_match = re.search(
            r'^[,.\s]*(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)\s+' + name_pattern,
            context_after
        )

        if not after_match:
            # Try reversed pattern: , [Name] said
            after_match = re.search(
                r'^[,.\s]*' + name_pattern + r'\s+(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)',
                context_after
            )

        # Step 4: Look for attribution BEFORE quote
        # Pattern: [Capitalised Name] said/says/etc: [quote]
        # Also handles: "quote," Name said. "quote2"
        # Also handles: Name, title/role, said: "quote"
        before_match = re.search(
            name_pattern + r'(?:,\s+[^,]+?,)?\s+(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)[,:.]\s*$',
            context_before
        )

        # Also check for "According to [Name]," pattern
        according_match = re.search(
            r'[Aa]ccording to\s+' + name_pattern + r'[,]?\s*$',
            context_before
        )

        # Step 5: Extract name and store evidence
        if after_match:
            name = after_match.group(1).strip()
            sources.append({
                'name': name,
                'full_attribution': context_after[:50].strip(),
                'quote_snippet': quote_text[:50],
                'position': 'after'
            })
        elif before_match:
            name = before_match.group(1).strip()
            sources.append({
                'name': name,
                'full_attribution': context_before[-50:].strip(),
                'quote_snippet': quote_text[:50],
                'position': 'before'
            })
        elif according_match:
            name = according_match.group(1).strip()
            sources.append({
                'name': name,
                'full_attribution': context_before[-50:].strip(),
                'quote_snippet': quote_text[:50],
                'position': 'before'
            })

    # Step 6: Deduplicate by normalized name
    unique_sources = deduplicate_sources(sources)

    # Step 7: Add gender detection
    for source in unique_sources:
        source['gender'] = get_gender(source['name'])

    return unique_sources


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


def extract_shorthand_content(shorthand_url):
    """
    Fetch and extract text content from a Shorthand embed page.
    Returns tuple: (cleaned_text, word_count) or (None, None) if extraction fails.
    """
    try:
        print(f"    Fetching Shorthand: {shorthand_url}")
        response = requests.get(shorthand_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract text from paragraphs, blockquotes, and headings
        content_tags = soup.find_all(['p', 'blockquote', 'h1', 'h2', 'h3'])

        text_parts = []
        for tag in content_tags:
            # Skip navigation, footer, and metadata
            parent_classes = []
            for parent in tag.parents:
                if parent.get('class'):
                    parent_classes.extend(parent.get('class'))

            # Skip if in nav/footer/header
            skip_classes = ['nav', 'navigation', 'footer', 'header', 'menu', 'metadata',
                          'caption', 'credit', 'credits']
            if any(skip_class in ' '.join(parent_classes).lower() for skip_class in skip_classes):
                continue

            text = tag.get_text(strip=True)

            # Skip if text contains photo credits or UI elements
            if text:
                text_lower = text.lower()
                skip_phrases = ['photo by', 'image by', 'unsplash', 'shorthand',
                              'built with', 'click to', 'scroll to']
                if any(phrase in text_lower for phrase in skip_phrases):
                    continue

                # Skip very short fragments (likely UI elements)
                word_count_fragment = len(text.split())
                if word_count_fragment < 5:
                    continue

                text_parts.append(text)

        # Join all text for word count, but preserve paragraph structure for quote extraction
        full_text = ' '.join(text_parts)
        words = full_text.split()
        word_count = len(words) if words else None

        # For quote extraction, join paragraphs with newline to prevent cross-paragraph quotes
        text_for_quotes = '\n'.join(text_parts)

        print(f"    Shorthand word count: {word_count}")
        return (text_for_quotes, word_count)

    except requests.RequestException as e:
        print(f"    Error fetching Shorthand page: {e}")
        return (None, None)
    except Exception as e:
        print(f"    Error parsing Shorthand content: {e}")
        return (None, None)


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

        # Try JSON-LD schema first (most reliable)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                date_published = None

                # Handle @graph structure (WordPress schema.org)
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if isinstance(item, dict) and 'datePublished' in item:
                            date_published = item['datePublished']
                            break
                elif isinstance(data, dict):
                    date_published = data.get('datePublished')
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'datePublished' in item:
                            date_published = item['datePublished']
                            break

                if date_published:
                    # Parse ISO 8601 format: "2026-01-16T14:30:00+00:00"
                    if 'T' in date_published:
                        date_part, time_part = date_published.split('T')
                        article_date = date_part  # "2026-01-16"
                        # Extract HH:MM from time_part (e.g., "14:30:00+00:00" -> "14:30")
                        article_time = time_part[:5]
                        break
                    else:
                        article_date = date_published
            except:
                continue

        # Fallback: Try to find date in <time> tag
        if not article_date:
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

        # Find main content area
        article_body = soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in str(x).lower() or 'entry' in str(x).lower()))

        # Detect Shorthand embed first
        content_type = "standard"
        word_count = None
        shorthand_url = None
        article_text = None

        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
        if iframe:
            content_type = "shorthand"
            # Extract Shorthand URL and fetch content
            shorthand_url = iframe.get('src')
            if shorthand_url:
                # Ensure it's a full URL
                if not shorthand_url.startswith('http'):
                    shorthand_url = 'https:' + shorthand_url if shorthand_url.startswith('//') else shorthand_url

                # Fetch text and word count from Shorthand page
                article_text, word_count = extract_shorthand_content(shorthand_url)
            else:
                print(f"    Warning: Shorthand iframe found but no src URL")
                word_count = None
        else:
            # Count words in article body paragraphs
            if article_body:
                # Remove script, style, nav, footer, aside elements
                for tag in article_body(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    tag.decompose()

                # Count words in paragraphs
                paragraphs = article_body.find_all('p')
                text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                words = text.split()
                word_count = len(words) if words else None
                article_text = text

        # Extract quoted sources from the actual article text
        # For Shorthand: use fetched Shorthand content
        # For standard: use article body text
        if article_text:
            source_evidence = extract_quoted_sources(article_text)
        else:
            # Fallback to extracting from page body if Shorthand fetch failed
            if article_body:
                fallback_text = article_body.get_text(separator=' ', strip=True)
            else:
                fallback_text = soup.get_text(separator=' ', strip=True)
            source_evidence = extract_quoted_sources(fallback_text)

        # Map category to primary category
        category_primary = CATEGORY_MAP.get(category, "News")  # Default to "News"

        # Count sources by gender
        sources_male = sum(1 for s in source_evidence if s['gender'] == 'male')
        sources_female = sum(1 for s in source_evidence if s['gender'] == 'female')
        sources_unknown = sum(1 for s in source_evidence if s['gender'] == 'unknown')

        # Generate unique ID from URL
        article_id = hashlib.md5(url.encode()).hexdigest()[:12]

        # Calculate confidence scores
        author_confidence = "high" if author != "Unknown" and author.lower() not in ['editor', 'staff', 'buzz'] else "low"

        word_count_confidence = "high" if content_type == "standard" else "medium"

        # Quoted sources confidence
        if len(source_evidence) > 0:
            quoted_sources_confidence = "high"
        elif word_count and word_count < 300:
            quoted_sources_confidence = "medium"
        else:
            quoted_sources_confidence = "low"

        # Build warnings array
        warnings = []
        if author == "Unknown":
            warnings.append("Unknown author")
        if content_type == "shorthand":
            warnings.append("Shorthand word count may have ~20% inflation")
        if len(source_evidence) == 0 and word_count and word_count > 500:
            warnings.append("No quoted sources in article >500 words")

        return {
            'id': article_id,
            'headline': headline,
            'url': url,
            'author': author,
            'author_confidence': author_confidence,
            'date': article_date,
            'time': article_time,
            'category': category,
            'category_primary': category_primary,
            'word_count': word_count,
            'word_count_confidence': word_count_confidence,
            'content_type': content_type,
            'shorthand_url': shorthand_url,
            'quoted_sources': len(source_evidence),
            'quoted_sources_confidence': quoted_sources_confidence,
            'sources_male': sources_male,
            'sources_female': sources_female,
            'sources_unknown': sources_unknown,
            'source_evidence': source_evidence,
            'warnings': warnings
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
    shorthand_with_count = 0
    shorthand_without_count = 0
    standard_count = 0

    # Source statistics
    total_sources = 0
    total_male = 0
    total_female = 0
    total_unknown = 0
    source_distribution = defaultdict(int)
    articles_with_imbalance = []

    for article in articles:
        if article['date']:
            by_day[article['date']] += 1
        by_category[article['category']] += 1
        by_category_primary[article['category_primary']] += 1
        by_author[article['author']] += 1

        if article['content_type'] == 'shorthand':
            shorthand_count += 1
            if article['word_count']:
                shorthand_with_count += 1
                word_counts.append(article['word_count'])
            else:
                shorthand_without_count += 1
        else:
            standard_count += 1
            if article['word_count']:
                word_counts.append(article['word_count'])

        # Source statistics
        num_sources = article['quoted_sources']
        total_sources += num_sources
        total_male += article['sources_male']
        total_female += article['sources_female']
        total_unknown += article['sources_unknown']

        # Distribution: 0, 1, 2, 3+
        if num_sources >= 3:
            source_distribution['3+'] += 1
        else:
            source_distribution[num_sources] += 1

        # Gender imbalance: 3+ male, 0 female
        if article['sources_male'] >= 3 and article['sources_female'] == 0:
            articles_with_imbalance.append({
                'headline': article['headline'],
                'url': article['url'],
                'male': article['sources_male'],
                'female': article['sources_female']
            })

    # Save to JSON
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
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
    print(f"    - With word count: {shorthand_with_count}")
    print(f"    - Without word count: {shorthand_without_count}")

    # Print source statistics
    print(f"\n{'=' * 80}")
    print("QUOTED SOURCE ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Sources: {total_sources}")
    print(f"Average per Article: {total_sources / len(articles):.1f}")

    print(f"\nSource Distribution:")
    # Sort keys, handling '3+' specially
    sorted_keys = sorted([k for k in source_distribution.keys() if k != '3+'])
    if '3+' in source_distribution:
        sorted_keys.append('3+')
    for count in sorted_keys:
        print(f"  {count} sources: {source_distribution[count]} articles")

    print(f"\nGender Breakdown:")
    print(f"  Male: {total_male} ({100*total_male/max(total_sources,1):.1f}%)")
    print(f"  Female: {total_female} ({100*total_female/max(total_sources,1):.1f}%)")
    print(f"  Unknown: {total_unknown} ({100*total_unknown/max(total_sources,1):.1f}%)")

    # Articles with gender imbalance
    if articles_with_imbalance:
        print(f"\nArticles with Gender Imbalance (3+ male, 0 female): {len(articles_with_imbalance)}")
        for article in articles_with_imbalance:
            print(f"  - {article['headline']}")
            print(f"    Male: {article['male']}, Female: {article['female']}")

    # Sample articles with full source evidence
    articles_with_sources = [a for a in articles if a['quoted_sources'] > 0]
    if articles_with_sources:
        print(f"\nSample Articles with Sources (first 5):")
        for i, article in enumerate(articles_with_sources[:5], 1):
            print(f"\n{i}. {article['headline']}")
            print(f"   URL: {article['url']}")
            print(f"   Sources: {article['quoted_sources']} (M:{article['sources_male']}, F:{article['sources_female']}, U:{article['sources_unknown']})")
            if article['source_evidence']:
                print(f"   Evidence:")
                for j, source in enumerate(article['source_evidence'][:3], 1):
                    print(f"     {j}. {source['name']} ({source['gender']})")
                    print(f"        Quote: \"{source['quote_snippet']}...\"")
                    print(f"        Attribution: {source['full_attribution']}")

    # Articles with 0 sources
    articles_no_sources = [a for a in articles if a['quoted_sources'] == 0]
    if articles_no_sources:
        print(f"\nArticles with 0 Sources ({len(articles_no_sources)}):")
        for article in articles_no_sources[:5]:
            print(f"  - {article['headline']}")
            print(f"    Category: {article['category_primary']}")

    print(f"\nData saved to {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

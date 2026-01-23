#!/usr/bin/env python3
"""
Add historical articles to BUzz Metrics dataset.
Usage: python3 add_historical.py --date 2026-01-14 --headlines headlines.txt
       python3 add_historical.py --date 2026-01-14 --urls urls.txt
"""

import argparse
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from scrape import (
    analyze_article_with_groq,
    extract_shorthand_content_new,
    normalize_quotes,
    SPORT_CATEGORIES
)

BASE_URL = "https://buzz.bournemouth.ac.uk"

def search_buzz_for_headline(headline, target_date):
    """
    Search BUzz site for article matching headline.
    Uses the monthly archive page for better accuracy.
    Returns URL if found, None if not found.
    """
    try:
        # Parse target date to get year/month
        from datetime import datetime
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.strftime('%m')

        # Fetch the monthly archive page
        archive_url = f"{BASE_URL}/{year}/{month}/"
        print(f"    Searching archive: {archive_url}")

        response = requests.get(archive_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Find all article links on the archive page
        # Look for h2 or h3 tags with article headlines
        article_elements = soup.find_all(['h2', 'h3'])

        # Normalize headline for comparison
        headline_normalized = headline.lower().strip()
        headline_words = set(headline_normalized.split())

        best_match = None
        best_score = 0

        for elem in article_elements:
            link = elem.find('a')
            if not link or not link.get('href'):
                continue

            link_text = link.get_text(strip=True).lower()
            link_href = link.get('href')

            # Must be an article URL
            if not re.search(r'/\d{4}/\d{2}/', link_href):
                continue

            # Calculate match score (how many words match)
            link_words = set(link_text.split())
            common_words = headline_words & link_words
            score = len(common_words)

            # Exact match
            if headline_normalized == link_text:
                full_url = BASE_URL + link_href if not link_href.startswith('http') else link_href
                print(f"    ✓ Exact match: {link_text[:60]}")
                return full_url

            # Track best partial match
            if score > best_score and score >= 3:  # At least 3 words must match
                best_match = link_href
                best_score = score
                print(f"    Partial match ({score} words): {link_text[:60]}")

        # Return best match if found
        if best_match:
            full_url = BASE_URL + best_match if not best_match.startswith('http') else best_match
            print(f"    Using best match (score: {best_score})")
            return full_url

        print(f"    No match found in archive")
        return None

    except Exception as e:
        print(f"    Error searching: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_article(url, target_date):
    """
    Fetch and process article, return article dict matching schema.
    """
    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Extract headline
        headline = "Unknown"
        h1 = soup.find('h1')
        if h1:
            headline = h1.get_text(strip=True)

        # Extract author
        author = "Unknown"
        author_elem = soup.find('a', rel='author')
        if author_elem:
            author = author_elem.get_text(strip=True)

        # Extract time from JSON-LD or meta tags
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
                        # Extract HH:MM from time_part (e.g., "14:30:00+00:00" -> "14:30")
                        article_time = time_part[:5]
                        break
            except:
                continue

        # Fallback: Try to find time in <time> tag
        if not article_time:
            date_elem = soup.find('time')
            if date_elem:
                datetime_str = date_elem.get('datetime')
                if datetime_str:
                    try:
                        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        article_time = dt.strftime('%H:%M')
                    except:
                        pass

        # Default to 00:00 if not found
        if not article_time:
            article_time = "00:00"

        # Detect Shorthand embed
        shorthand_url = None
        content_type = "standard"

        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
        if iframe:
            content_type = "shorthand"
            # Extract Shorthand URL and fetch content
            shorthand_url = iframe.get('src')
            if shorthand_url:
                # Ensure it's a full URL
                if not shorthand_url.startswith('http'):
                    shorthand_url = 'https:' + shorthand_url if shorthand_url.startswith('//') else shorthand_url

                # Use new clean extraction function
                print(f"  Shorthand detected, extracting...")
                shorthand_data = extract_shorthand_content_new(shorthand_url)

                if not shorthand_data:
                    print(f"  Failed to extract Shorthand content")
                    return None

                word_count = shorthand_data.get('word_count', 0)
                source_evidence = shorthand_data.get('sources', [])
                images = shorthand_data.get('images', {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []})

                # Override author with Shorthand byline if found
                if shorthand_data.get('author'):
                    author = shorthand_data['author']
            else:
                print(f"  Warning: Shorthand iframe found but no src URL")
                return None

        else:
            # WordPress article
            article_body = soup.find('article')
            if not article_body:
                print(f"  No article body found")
                return None

            body_text = article_body.get_text(separator=' ', strip=True)

            # Count words
            word_count = len(body_text.split())

            # Get Groq sources
            print(f"  Analyzing with Groq...")
            groq_sources = analyze_article_with_groq(body_text)

            if groq_sources is None:
                print(f"  Groq failed, using empty sources")
                source_evidence = []
            else:
                source_evidence = groq_sources

            # Count images (basic)
            images = {
                'total': len(soup.find_all('img')),
                'original': 0,
                'stock': 0,
                'uncredited': 0,
                'details': []
            }

        # Extract category from JSON-LD
        category = "News"
        category_detail = None
        placement_tags = ["1st News", "2nd News", "3rd News", "Dorset", "News Top"]

        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                candidate_categories = []

                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if isinstance(item, dict) and 'articleSection' in item:
                            sections = item['articleSection']
                            if isinstance(sections, list):
                                candidate_categories.extend(sections)
                            elif isinstance(sections, str):
                                candidate_categories.append(sections)

                # Filter placement tags
                filtered_categories = [c for c in candidate_categories if c not in placement_tags]

                # Determine Sport or News
                if filtered_categories:
                    for cat in filtered_categories:
                        if cat in SPORT_CATEGORIES:
                            category = "Sport"
                            category_detail = cat
                            break
                    if category == "News" and filtered_categories:
                        category_detail = filtered_categories[0]
                break
            except:
                continue

        # Count sources by gender
        sources_male = sum(1 for s in source_evidence if s.get('gender') == 'male')
        sources_female = sum(1 for s in source_evidence if s.get('gender') == 'female')
        sources_unknown = sum(1 for s in source_evidence if s.get('gender') in ['unknown', 'nonbinary'])

        # Generate article ID
        article_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]

        # Build warnings
        warnings = []
        if article_time == "00:00":
            warnings.append('Historical import - time unknown')

        # Build article dict
        article = {
            'id': article_id,
            'headline': headline,
            'url': url,
            'author': author,
            'author_confidence': 'medium',
            'date': target_date,
            'time': article_time,
            'category': category,
            'category_detail': category_detail,
            'category_primary': category,
            'display_category': category,
            'word_count': word_count,
            'word_count_confidence': 'high' if content_type == "standard" else 'medium',
            'content_type': content_type,
            'shorthand_url': shorthand_url,
            'quoted_sources': len(source_evidence),
            'quoted_sources_confidence': 'high' if source_evidence else 'low',
            'sources_male': sources_male,
            'sources_female': sources_female,
            'sources_unknown': sources_unknown,
            'source_evidence': source_evidence,
            'images': images,
            'embeds': {'video_count': 0, 'audio_count': 0, 'video_evidence': [], 'audio_evidence': []},
            'warnings': warnings
        }

        return article

    except Exception as e:
        print(f"  Error processing article: {e}")
        import traceback
        traceback.print_exc()
        return None

def add_to_datasets(articles):
    """Append articles to all three JSON files."""
    import os

    filepaths = [
        '../data/metrics_raw.json',
        '../data/metrics_verified.json',
        '../docs/metrics_verified.json'
    ]

    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing_urls = {a['url'] for a in data['articles']}
        added = 0

        for article in articles:
            if article['url'] not in existing_urls:
                data['articles'].append(article)
                added += 1
            else:
                print(f"  Skipped (exists): {article['headline'][:40]}...")

        # Update counts
        data['total_articles'] = len(data['articles'])
        data['last_updated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if added > 0:
            print(f"✓ Added {added} articles to {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Add historical articles to BUzz Metrics dataset')
    parser.add_argument('--date', required=True, help='Date for articles: YYYY-MM-DD')
    parser.add_argument('--headlines', help='File with headlines, one per line')
    parser.add_argument('--urls', help='File with URLs, one per line (skips search)')
    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        return

    if not args.headlines and not args.urls:
        print("Error: Must provide either --headlines or --urls")
        return

    print("=" * 80)
    print("BUzz Metrics - Historical Article Import")
    print("=" * 80)
    print(f"Target date: {args.date}\n")

    articles = []
    not_found = []

    if args.urls:
        # Direct URL input
        with open(args.urls, encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(urls)} URLs...\n")

        for url in urls:
            print(f"\nProcessing: {url}")
            article = process_article(url, args.date)

            if article:
                articles.append(article)
                print(f"  ✓ {article['headline'][:50]}")
                print(f"  Sources: {article.get('quoted_sources', 0)}")
            else:
                print(f"  ✗ Failed to process")

            time.sleep(1)  # Rate limit

    else:
        # Search by headline
        with open(args.headlines, encoding='utf-8') as f:
            headlines = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(headlines)} headlines...\n")

        for headline in headlines:
            print(f"\nSearching: {headline[:60]}...")

            url = search_buzz_for_headline(headline, args.date)

            if url:
                article = process_article(url, args.date)
                if article:
                    articles.append(article)
                    print(f"  ✓ Found and processed")
                    print(f"  Sources: {article.get('quoted_sources', 0)}")
                else:
                    not_found.append(headline)
            else:
                print(f"  ✗ NOT FOUND")
                not_found.append(headline)

            time.sleep(1)  # Rate limit

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successfully processed: {len(articles)}")

    if not_found:
        print(f"\nNot found ({len(not_found)}):")
        for headline in not_found:
            print(f"  - {headline}")
        print("\nCreate a file with URLs for these and re-run with --urls")

    if articles:
        print(f"\n{len(articles)} articles ready to import")
        confirm = input("\nAdd to datasets? (y/n): ")

        if confirm.lower() == 'y':
            add_to_datasets(articles)
            print("\n✓ Import complete!")
        else:
            print("\nImport cancelled")
    else:
        print("\nNo articles to import")

    print("=" * 80)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
BUzz Metrics Verifier - Sprint 6
Uses spaCy NER to independently verify quoted sources from scraped articles.
"""

import json
import requests
from bs4 import BeautifulSoup
import spacy
import re
import time
from datetime import datetime

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")


def fetch_article_text(url, content_type, shorthand_url=None):
    """
    Fetch article text from either standard article or Shorthand page.
    Returns cleaned text or None if fetch fails.
    """
    try:
        time.sleep(1)  # Be polite with rate limiting

        if content_type == "shorthand" and shorthand_url:
            print(f"  Fetching Shorthand: {shorthand_url}")
            response = requests.get(shorthand_url, timeout=10)
        else:
            print(f"  Fetching article: {url}")
            response = requests.get(url, timeout=10)

        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Extract text from paragraphs, blockquotes, and headings
        if content_type == "shorthand":
            content_tags = soup.find_all(['p', 'blockquote', 'h1', 'h2', 'h3'])
        else:
            # For standard articles, find article body
            article_body = soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in str(x).lower())
            if article_body:
                content_tags = article_body.find_all(['p', 'blockquote'])
            else:
                content_tags = soup.find_all('p')

        # Extract and clean text
        text_parts = []
        for tag in content_tags:
            text = tag.get_text(strip=True)
            if text and len(text) > 10:  # Skip very short fragments
                # Skip common UI elements
                if any(skip in text.lower() for skip in ['photo by', 'image by', 'click to', 'scroll to']):
                    continue
                text_parts.append(text)

        full_text = '\n'.join(text_parts)
        return full_text

    except requests.RequestException as e:
        print(f"  Warning: Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        print(f"  Warning: Error processing {url}: {e}")
        return None


def find_quoted_sources_with_ner(text):
    """
    Use spaCy NER to find PERSON entities within 50 characters of quotation marks.
    Returns list of source evidence dictionaries.
    """
    if not text:
        return []

    # Run NER
    doc = nlp(text)

    # Find all quote positions (straight, left curly, right curly)
    quote_chars = ['"', '\u201C', '\u201D']  # straight, left curly, right curly
    quote_positions = []
    for i, char in enumerate(text):
        if char in quote_chars:
            quote_positions.append(i)

    # Find PERSON entities near quotes
    sources = []
    seen_names = set()

    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue

        # Get entity position in text
        ent_start = ent.start_char
        ent_end = ent.end_char

        # Check if within 50 characters of any quote
        near_quote = False
        for quote_pos in quote_positions:
            distance = min(abs(ent_start - quote_pos), abs(ent_end - quote_pos))
            if distance <= 50:
                near_quote = True
                break

        if near_quote:
            name = ent.text.strip()
            # Normalize and deduplicate
            name_lower = name.lower()

            # Skip if already seen (case-insensitive)
            if name_lower in seen_names:
                continue

            # Skip common false positives
            if name_lower in ['i', 'me', 'you', 'he', 'she', 'they', 'we']:
                continue

            seen_names.add(name_lower)

            # Get context around entity
            context_start = max(0, ent_start - 50)
            context_end = min(len(text), ent_end + 50)
            context = text[context_start:context_end].replace('\n', ' ')

            sources.append({
                'name': name,
                'context': f"PERSON within 50 chars of quote: ...{context}..."
            })

    return sources


def main():
    print("=" * 80)
    print("BUzz Metrics Verifier - Sprint 6")
    print("=" * 80)
    print()

    # Load scraped data
    print("Loading metrics_raw.json...")
    with open('../data/metrics_raw.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    print(f"Found {len(articles)} articles to verify")
    print()

    results = []

    for i, article in enumerate(articles, 1):
        article_id = article['id']
        url = article['url']
        headline = article['headline']
        content_type = article['content_type']
        shorthand_url = article.get('shorthand_url')

        print(f"[{i}/{len(articles)}] {headline[:60]}...")

        # Fetch article text
        text = fetch_article_text(url, content_type, shorthand_url)

        if not text:
            print("  Skipping due to fetch failure")
            results.append({
                'id': article_id,
                'url': url,
                'verify_quoted_sources': None,
                'verify_evidence': [],
                'error': 'Failed to fetch article text'
            })
            continue

        # Find sources with NER
        verify_evidence = find_quoted_sources_with_ner(text)

        print(f"  Found {len(verify_evidence)} source(s) via NER")
        for source in verify_evidence:
            print(f"    - {source['name']}")

        results.append({
            'id': article_id,
            'url': url,
            'verify_quoted_sources': len(verify_evidence),
            'verify_evidence': verify_evidence
        })

    # Save results
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_verified': len(results),
        'results': results
    }

    output_path = '../data/verify_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 80)
    print(f"Verification complete - {len(results)} articles processed")
    print(f"Data saved to {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

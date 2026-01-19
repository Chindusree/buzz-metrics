#!/usr/bin/env python3
"""
Sprint 7.9: Controlled Dataset Test
Test extraction on 4 specific URLs only
"""

import json
from datetime import datetime
from scrape import extract_article_metadata

# Test URLs - 2 Shorthand, 2 WordPress
TEST_URLS = [
    # Shorthand
    "https://buzz.bournemouth.ac.uk/2026/01/celebrating-the-rnlis-work-in-poole/",
    "https://buzz.bournemouth.ac.uk/2026/01/can-upfs-be-avoided-on-a-budget/",
    # WordPress
    "https://buzz.bournemouth.ac.uk/2026/01/tonight-stitch-and-movie-night/",
    "https://buzz.bournemouth.ac.uk/2026/01/hotel-staff-take-the-plunge-for-charity/",
]

def main():
    print("=" * 80)
    print("Sprint 7.9: Controlled Dataset Test")
    print("=" * 80)
    print(f"\nTesting {len(TEST_URLS)} URLs:\n")

    articles = []

    for i, url in enumerate(TEST_URLS, 1):
        print(f"[{i}/{len(TEST_URLS)}] Extracting: {url}")

        metadata = extract_article_metadata(url)

        if metadata:
            articles.append(metadata)
            print(f"  ✓ {metadata['headline']}")
            print(f"    Type: {metadata['content_type']}")
            print(f"    Sources: {metadata['quoted_sources']}")
            print(f"    Word count: {metadata['word_count']}")
        else:
            print(f"  ✗ Failed to extract")
        print()

    # Save to metrics_raw.json
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_articles': len(articles),
        'articles': articles
    }

    output_path = '../data/metrics_raw.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f"✓ Extracted {len(articles)}/{len(TEST_URLS)} articles")
    print(f"✓ Saved to {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()

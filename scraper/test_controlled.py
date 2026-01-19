#!/usr/bin/env python3
"""
Sprint 7.9.2: Controlled Dataset Test
Test extraction on 4 specific URLs only
"""

import json
from datetime import datetime
from scrape import extract_article_metadata

# Sprint 7.9.2: New test URLs
TEST_URLS = [
    'https://buzz.bournemouth.ac.uk/2026/01/christchurch-chef-reveals-excitement-over-new-locally-produced-menus/',
    'https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/',
    'https://buzz.bournemouth.ac.uk/2025/10/power-restored-after-storm-amy/',
    'https://buzz.bournemouth.ac.uk/2026/01/running-together-how-bournemouths-run-clubs-are-building-community/'
]

def main():
    print("=" * 80)
    print("Sprint 7.9.2: Controlled Dataset Test")
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

            # Sprint 7.9.2: Print Shorthand URL if present
            if metadata.get('shorthand_url'):
                print(f"    Shorthand URL: {metadata['shorthand_url']}")

            # Sprint 7.9.2: Print source names
            if metadata.get('source_evidence'):
                source_names = [s['name'] for s in metadata['source_evidence']]
                print(f"    Source names: {', '.join(source_names) if source_names else 'None'}")
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

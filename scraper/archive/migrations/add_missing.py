#!/usr/bin/env python3
"""
Sprint 7.27: Safely add missing articles to existing data.
DOES NOT overwrite - only appends new articles.
"""

import json
import os
from scrape import extract_article_metadata
from datetime import datetime

MISSING_URLS = [
    "https://buzz.bournemouth.ac.uk/2026/01/bleazard-and-quirk-praise-performance-in-fa-cup-exit/",
    "https://buzz.bournemouth.ac.uk/2026/01/watch-the-latest-news-around-bournemouth-and-dorset/",
    "https://buzz.bournemouth.ac.uk/2026/01/new-greek-restaurant-set-to-open-in-wallisdown/",
    "https://buzz.bournemouth.ac.uk/2026/01/intersectional-uprising-protest-empowers-bournemouth-residents/",
    "https://buzz.bournemouth.ac.uk/2026/01/cherries-denied-three-points-late-on-at-brighton/",
]

def main():
    print("=" * 80)
    print("Sprint 7.27: Safe Manual Article Addition")
    print("=" * 80)
    print()

    # Step 1: Load existing data
    raw_path = '../data/metrics_raw.json'

    if not os.path.exists(raw_path):
        print("ERROR: metrics_raw.json not found!")
        return

    with open(raw_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    existing_urls = {a['url'] for a in existing.get('articles', [])}
    print(f"✓ Loaded existing data: {len(existing_urls)} articles")
    print()

    # Step 2: Backup before modifying
    backup_path = f'../data/metrics_raw.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
    print(f"✓ Backup created: {backup_path}")
    print()

    # Step 3: Scrape only NEW articles
    added = 0
    skipped = 0
    errors = 0

    for url in MISSING_URLS:
        if url in existing_urls:
            print(f"⊘ SKIP (already exists): {url}")
            skipped += 1
            continue

        print(f"→ Scraping: {url}")
        try:
            article = extract_article_metadata(url)
            if article:
                existing['articles'].append(article)
                added += 1
                print(f"  ✓ Added: {article.get('headline', 'Unknown')[:60]}")
                print(f"     Date: {article.get('date', 'N/A')}, Sources: {article.get('quoted_sources', 0)}")
            else:
                print(f"  ✗ Failed to extract article")
                errors += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            errors += 1
        print()

    # Step 4: Update timestamp and save ONLY if articles were added
    if added > 0:
        existing['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        existing['total_articles'] = len(existing['articles'])

        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)

        print("=" * 80)
        print(f"✓ SUCCESS: Added {added} new articles")
        print(f"  Total articles: {len(existing['articles'])}")
        print(f"  Skipped (duplicates): {skipped}")
        print(f"  Errors: {errors}")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. python3 verify.py")
        print("  2. python3 compare.py")
        print("  3. Verify article count matches expected")
    else:
        print("=" * 80)
        print("ℹ No new articles added")
        print(f"  Skipped (duplicates): {skipped}")
        print(f"  Errors: {errors}")
        print("=" * 80)

if __name__ == '__main__':
    main()

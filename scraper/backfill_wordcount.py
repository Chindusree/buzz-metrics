#!/usr/bin/env python3
"""
Sprint 8.6: Word Count Backfill Script

Re-extracts word counts for all articles using the fixed extraction logic.
Updates metrics_verified.json with correct word counts.

Usage:
    python3 backfill_wordcount.py [--test slug1 slug2 ...]
"""

import json
import sys
from datetime import datetime
from scrape import extract_article_metadata

def load_data():
    """Load metrics_verified.json"""
    with open('../data/metrics_verified.json', 'r') as f:
        return json.load(f)

def save_data(data):
    """Save to both data/ and docs/"""
    with open('../data/metrics_verified.json', 'w') as f:
        json.dump(data, f, indent=2)
    with open('../docs/metrics_verified.json', 'w') as f:
        json.dump(data, f, indent=2)

def backfill_wordcount(test_slugs=None):
    """
    Backfill word counts for all articles (or test articles only).

    Args:
        test_slugs: List of URL slugs to test on (optional)
    """
    print("=" * 80)
    print("SPRINT 8.6: WORD COUNT BACKFILL")
    print("=" * 80)
    print()

    data = load_data()
    articles = data['articles']

    # Filter to test articles if specified
    if test_slugs:
        articles = [a for a in articles if any(slug in a.get('url', '') for slug in test_slugs)]
        print(f"TEST MODE: Processing {len(articles)} article(s)")
    else:
        print(f"PRODUCTION MODE: Processing all {len(articles)} articles")

    print()

    # Statistics
    updated_count = 0
    error_count = 0
    no_change_count = 0
    total_old_wc = 0
    total_new_wc = 0

    # Track changes for changelog
    changes = []

    for idx, article in enumerate(articles, 1):
        url = article.get('url', '')
        headline = article.get('headline', 'Unknown')
        old_wc = article.get('word_count', 0)

        # Extract slug for display
        slug = url.split('/')[-2] if url else 'unknown'

        print(f"[{idx}/{len(articles)}] {headline[:60]}...")
        print(f"  URL: {slug}")
        print(f"  Old WC: {old_wc}")

        # Fetch fresh word count
        try:
            metadata = extract_article_metadata(url)
            if not metadata:
                print(f"  ✗ Extraction failed")
                error_count += 1
                continue

            new_wc = metadata.get('word_count', 0)
            print(f"  New WC: {new_wc}")

            if new_wc == old_wc:
                print(f"  → No change")
                no_change_count += 1
            else:
                diff = new_wc - old_wc
                pct_change = ((new_wc - old_wc) / old_wc * 100) if old_wc > 0 else 0
                print(f"  ✓ Updated: {old_wc} → {new_wc} ({diff:+d}, {pct_change:+.1f}%)")

                # Update article
                article['word_count'] = new_wc
                updated_count += 1

                # Track change
                changes.append({
                    'url': url,
                    'headline': headline,
                    'old_wc': old_wc,
                    'new_wc': new_wc,
                    'diff': diff
                })

                total_old_wc += old_wc
                total_new_wc += new_wc

        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1

        print()

    # Save updated data
    if updated_count > 0 and not test_slugs:
        print("=" * 80)
        print("SAVING UPDATED DATA")
        print("=" * 80)
        save_data(data)
        print(f"✓ Saved to data/metrics_verified.json")
        print(f"✓ Saved to docs/metrics_verified.json")
        print()

        # Save changelog
        changelog_path = f'../data/wordcount_changelog_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(changelog_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'updated_count': updated_count,
                'total_old_wc': total_old_wc,
                'total_new_wc': total_new_wc,
                'avg_reduction': (total_old_wc - total_new_wc) / updated_count if updated_count > 0 else 0,
                'changes': changes
            }, f, indent=2)
        print(f"✓ Changelog: {changelog_path}")
        print()

    # Summary
    print("=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print(f"Total processed:  {len(articles)}")
    print(f"Updated:          {updated_count}")
    print(f"No change:        {no_change_count}")
    print(f"Errors:           {error_count}")

    if updated_count > 0:
        avg_old = total_old_wc / updated_count
        avg_new = total_new_wc / updated_count
        avg_reduction = avg_old - avg_new
        pct_reduction = (avg_reduction / avg_old * 100) if avg_old > 0 else 0

        print()
        print(f"Average old WC:   {avg_old:.0f}")
        print(f"Average new WC:   {avg_new:.0f}")
        print(f"Average reduction: {avg_reduction:.0f} words ({pct_reduction:.1f}%)")

    print()

    return updated_count > 0

if __name__ == '__main__':
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_slugs = sys.argv[2:] if len(sys.argv) > 2 else [
            'homelessness-issue',
            'residents-call-for-safer',
            'bournemouth-oaks'
        ]
        backfill_wordcount(test_slugs)
    else:
        backfill_wordcount()

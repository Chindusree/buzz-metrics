#!/usr/bin/env python3
"""
Sprint 7.34: Re-process existing articles with new source filtering.
SAFE: Creates backup before any changes.

This script applies Sprint 7.33 filtering to existing source_evidence,
without re-fetching articles (which would be slow and error-prone).
"""

import json
import os
from datetime import datetime

def backup_file(filepath):
    """Create timestamped backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = filepath.replace('.json', f'.backup.{timestamp}.json')

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Backup created: {backup_path}")
    return backup_path

def filter_sources(article):
    """
    Apply Sprint 7.33 filtering to existing source_evidence.

    Returns updated article with filtered sources.
    """
    # Get existing source evidence
    source_evidence = article.get('source_evidence', [])

    if not source_evidence:
        # No sources to filter
        return article, 0, 0

    original_count = len(source_evidence)

    # Sprint 7.33: Filter to only include direct quotes
    DIRECT_QUOTE_POSITIONS = {'after', 'before', 'blockquote-inline', 'lastname_verb', 'standalone_dash'}
    filtered_sources = [s for s in source_evidence if s.get('position') in DIRECT_QUOTE_POSITIONS]

    # Update article
    article['source_evidence'] = filtered_sources
    article['quoted_sources'] = len(filtered_sources)

    # Recalculate gender counts
    sources_male = sum(1 for s in filtered_sources if s.get('gender') == 'male')
    sources_female = sum(1 for s in filtered_sources if s.get('gender') == 'female')
    sources_they = sum(1 for s in filtered_sources if s.get('gender') == 'they')
    sources_unknown = sum(1 for s in filtered_sources if s.get('gender') == 'unknown')

    article['sources_male'] = sources_male
    article['sources_female'] = sources_female
    article['sources_they'] = sources_they
    article['sources_unknown'] = sources_unknown

    filtered_count = len(filtered_sources)

    return article, original_count, filtered_count

def main():
    print("=" * 80)
    print("Sprint 7.34: Safe Data Migration")
    print("=" * 80)
    print()

    data_path = '../data/metrics_verified.json'
    docs_path = '../docs/metrics_verified.json'

    # Check files exist
    if not os.path.exists(data_path):
        print(f"✗ ERROR: {data_path} not found!")
        return

    # Step 1: Backup
    print("Step 1: Creating backups...")
    backup_file(data_path)
    if os.path.exists(docs_path):
        backup_file(docs_path)
    print()

    # Step 2: Load data
    print("Step 2: Loading data...")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_articles = len(data.get('articles', []))
    print(f"✓ Loaded {total_articles} articles")
    print()

    # Step 3: Apply filtering
    print("Step 3: Applying Sprint 7.33 source filtering...")
    print("-" * 80)

    stats = {
        'processed': 0,
        'unchanged': 0,
        'reduced': 0,
        'total_before': 0,
        'total_after': 0
    }

    for i, article in enumerate(data['articles'], 1):
        headline = article.get('headline', 'Unknown')[:50]

        filtered_article, before, after = filter_sources(article)
        data['articles'][i-1] = filtered_article

        stats['processed'] += 1
        stats['total_before'] += before
        stats['total_after'] += after

        if before == after:
            stats['unchanged'] += 1
            status = "unchanged"
        else:
            stats['reduced'] += 1
            status = f"{before} → {after}"
            print(f"  [{i}/{total_articles}] {headline}... → {status}")

    print()
    print("-" * 80)
    print("Migration Statistics:")
    print(f"  Total articles: {stats['processed']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Reduced: {stats['reduced']}")
    print(f"  Total sources before: {stats['total_before']}")
    print(f"  Total sources after: {stats['total_after']}")
    print(f"  Sources removed: {stats['total_before'] - stats['total_after']}")
    print()

    # Step 4: Save
    print("Step 4: Saving updated data...")
    data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved: {data_path}")

    if os.path.exists(docs_path):
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved: {docs_path}")

    print()
    print("=" * 80)
    print("✓ Migration complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Verify results (see verification script below)")
    print("  2. Check a few articles manually")
    print("  3. If all looks good, push to GitHub")
    print()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Sprint 7.28: Add display_category to existing articles.
SAFE: Only adds new field, doesn't modify anything else.
"""

import json
from datetime import datetime


def get_display_category(raw_category, headline, tags=None):
    """
    Sprint 7.28: Determine display category for dashboard visualization.

    Returns 'Sport' or 'General News' based on category, headline, and tags.
    This is computed once per article and stored in display_category field.

    Args:
        raw_category: Original category from article
        headline: Article headline
        tags: List of article tags (optional)

    Returns:
        str: 'Sport' or 'General News'
    """
    cat = (raw_category or '').lower()
    headline_lower = (headline or '').lower()
    tags_text = ' '.join(tags or []).lower()

    text_to_check = f"{cat} {headline_lower} {tags_text}"

    SPORT_KEYWORDS = [
        'sport', 'football', 'afc bournemouth', 'cherries', 'cricket',
        'rugby', 'basketball', 'swimming', 'swimmers', 'swim', 'tennis',
        'golf', 'boxing', 'f1', 'formula', 'lions', 'rec', 'hamworthy',
        'athletic', 'fc', 'united', 'match', 'league', 'cup',
        'player', 'signing', 'transfer', 'goal', 'score', 'defeat',
        'play-off', 'playoff', 'quarter final', 'semi final',
        'nba', 'nfl', 'olympics', 'commonwealth', 'spurs', 'tottenham',
        'solanke', 'jimenez', 'tavernier', 'rating', 'ratings'
    ]

    if any(kw in text_to_check for kw in SPORT_KEYWORDS):
        return 'Sport'
    return 'General News'


def migrate_file(filepath):
    """
    Add display_category field to all articles in a JSON file.

    Args:
        filepath: Path to JSON file to migrate

    Returns:
        dict: Statistics about the migration
    """
    print(f"\n{'='*80}")
    print(f"Migrating: {filepath}")
    print(f"{'='*80}")

    # Backup first
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    backup_path = filepath.replace('.json', f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Backup created: {backup_path}")

    # Add display_category to each article
    sport_count = 0
    news_count = 0

    for article in data.get('articles', []):
        display_category = get_display_category(
            article.get('category'),
            article.get('headline'),
            article.get('tags', [])
        )
        article['display_category'] = display_category

        if display_category == 'Sport':
            sport_count += 1
        else:
            news_count += 1

    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Migration complete")
    print(f"  Total articles: {len(data.get('articles', []))}")
    print(f"  Sport: {sport_count}")
    print(f"  General News: {news_count}")

    return {
        'total': len(data.get('articles', [])),
        'sport': sport_count,
        'news': news_count
    }


def main():
    print("\n" + "="*80)
    print("Sprint 7.28: Safe Category Migration")
    print("="*80)

    # Migrate all data files
    files = [
        '../data/metrics_raw.json',
        '../data/metrics_verified.json',
        '../docs/metrics_verified.json'
    ]

    total_stats = {'total': 0, 'sport': 0, 'news': 0}

    for filepath in files:
        try:
            stats = migrate_file(filepath)
            # Only count once (all files should have same data)
            if filepath == '../data/metrics_verified.json':
                total_stats = stats
        except FileNotFoundError:
            print(f"\n⚠ Warning: {filepath} not found, skipping")
        except Exception as e:
            print(f"\n✗ Error migrating {filepath}: {e}")
            return

    # Final summary
    print("\n" + "="*80)
    print("✓ ALL FILES MIGRATED SUCCESSFULLY")
    print("="*80)
    print(f"Total articles: {total_stats['total']}")
    print(f"Sport: {total_stats['sport']}")
    print(f"General News: {total_stats['news']}")
    print("\nVerify with:")
    print('python3 -c "import json; d=json.load(open(\'../data/metrics_verified.json\')); print({a[\'display_category\'] for a in d[\'articles\']})"')
    print("="*80)


if __name__ == '__main__':
    main()

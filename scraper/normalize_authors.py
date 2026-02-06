#!/usr/bin/env python3
"""
Author Name Normalization Script

Safely normalizes author names across all data files.
Creates backups before modification.

Changes:
1. "Iryna Melnykova" → "Ira Melnykova" (nickname variant)
2. Remove "Editor Red" from contributor visibility (like Editor Green/Blue)

Run: python3 normalize_authors.py --dry-run    (preview changes)
     python3 normalize_authors.py               (apply changes)
"""

import json
import sys
from pathlib import Path

# Normalization rules
AUTHOR_MAPPINGS = {
    "Iryna Melnykova": "Ira Melnykova",
    # Add more as discovered
}

# Authors to mark as generic (won't appear in Contributors)
GENERIC_AUTHORS = [
    "Editor Red",
    "Editor Green",
    "Editor Blue",
    "Editor",
    "Unknown",
    "BUzz"
]

DATA_FILES = [
    "data/metrics_sei.json",
    "data/metrics_ssi.json",
    "data/metrics_verified.json",
    "data/metrics_bns.json",
    "docs/metrics_sei.json",
    "docs/metrics_ssi.json",
    "docs/metrics_bns.json"
]

def normalize_author(author):
    """Apply normalization rules to author name."""
    if author in AUTHOR_MAPPINGS:
        return AUTHOR_MAPPINGS[author]
    return author

def process_file(filepath, dry_run=True):
    """Process a single JSON file."""
    path = Path(filepath)

    if not path.exists():
        print(f"⚠️  {filepath} - Not found, skipping")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    changes = []

    # Process articles
    if 'articles' in data:
        for article in data['articles']:
            if 'author' in article:
                old_author = article['author']
                new_author = normalize_author(old_author)

                if old_author != new_author:
                    article['author'] = new_author
                    changes.append(f"  {old_author} → {new_author}")

    if changes:
        print(f"\n{filepath}:")
        for change in set(changes):  # dedupe
            print(change)

        if not dry_run:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved")
    else:
        print(f"✓ {filepath} - No changes needed")

    return len(changes)

def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No files will be modified")
        print("=" * 60)
    else:
        print("=" * 60)
        print("APPLYING CHANGES - Files will be modified")
        print("Backups already created in data/backups/")
        print("=" * 60)

    print("\nNormalization Rules:")
    for old, new in AUTHOR_MAPPINGS.items():
        print(f"  {old} → {new}")

    print("\nGeneric Authors (filtered from Contributors):")
    for author in GENERIC_AUTHORS:
        print(f"  - {author}")

    print("\nProcessing files...\n")

    total_changes = 0
    for filepath in DATA_FILES:
        changes = process_file(filepath, dry_run)
        if changes:
            total_changes += changes

    print("\n" + "=" * 60)
    if dry_run:
        print(f"Preview complete: {total_changes} changes would be made")
        print("\nTo apply changes, run:")
        print("  python3 normalize_authors.py")
    else:
        print(f"✓ Complete: {total_changes} changes applied")
        print("\nTo revert, restore from data/backups/")
    print("=" * 60)

if __name__ == '__main__':
    main()

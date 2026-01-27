#!/usr/bin/env python3
"""
Sprint 8.4: Backfill Source Detection (Groq-powered)
Re-processes all historical articles using Groq LLM for source detection.

This matches production scraper logic exactly:
- Uses analyze_article_with_groq() from scrape.py
- Handles curly quotes, cross-paragraph attribution, all edge cases
- Groq fallback to regex if API fails

Safety features:
- Dry run mode (--dry-run)
- Article limit for testing (--limit N)
- URL filter for specific articles (--urls URL1 URL2 ...)
- Automatic backup with validation
- Detailed changelog file
- Incremental saves every 20 articles
- Rate limiting between Groq API calls
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import shutil
import sys
import argparse
from pathlib import Path

# Add scraper directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrape import analyze_article_with_groq

# Configuration
DATA_FILE = 'data/metrics_verified.json'
BACKUP_DIR = 'data/backups'
BATCH_SIZE = 20  # Save progress every 20 articles
GROQ_DELAY = 1.5  # seconds between Groq API calls (rate limiting)
REQUEST_TIMEOUT = 30  # seconds

def create_backup(data_file):
    """Create timestamped backup of data file and validate it"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{BACKUP_DIR}/metrics_verified_{timestamp}.json"

    # Copy file
    shutil.copy2(data_file, backup_path)
    print(f"✓ Backup created: {backup_path}")

    # Validate backup
    print("  Validating backup...")
    try:
        with open(data_file, 'r') as f:
            original = json.load(f)
        with open(backup_path, 'r') as f:
            backup = json.load(f)

        original_count = len(original.get('articles', []))
        backup_count = len(backup.get('articles', []))

        if original_count != backup_count:
            raise ValueError(f"Article count mismatch: {original_count} vs {backup_count}")

        print(f"  ✓ Backup validated ({backup_count} articles)")
        return backup_path, timestamp
    except Exception as e:
        print(f"  ✗ Backup validation failed: {e}")
        sys.exit(1)

def fetch_article_text(url):
    """Fetch article HTML and extract body text"""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find article body
        article_body = soup.find('div', class_='entry-content') or soup.find('article')
        if not article_body:
            return None, "Could not find article body"

        # Extract text
        text = article_body.get_text(separator=' ', strip=True)
        return text, None
    except requests.RequestException as e:
        return None, f"Request failed: {e}"
    except Exception as e:
        return None, f"Parse error: {e}"

def update_article_sources_groq(article):
    """
    Re-fetch article and update source data using Groq LLM.

    This uses the SAME logic as production scraper:
    - analyze_article_with_groq() handles quote normalization, all patterns
    - Returns None if Groq fails (we skip the article)
    - Returns [] if no sources found
    """
    url = article.get('url')
    if not url:
        return None, "No URL"

    # Fetch article text
    text, error = fetch_article_text(url)
    if error:
        return None, error

    # Extract sources using Groq (same as production)
    groq_sources = analyze_article_with_groq(text)

    if groq_sources is None:
        # Groq API failed - skip this article
        return None, "Groq API failed (None returned)"

    # Convert Groq results to standard format
    sources = []
    for groq_src in groq_sources:
        sources.append({
            'name': groq_src.get('name', 'Unknown'),
            'gender': groq_src.get('gender', 'unknown'),
            'type': groq_src.get('type', 'unknown')
        })

    # Count by gender
    male = sum(1 for s in sources if s.get('gender') == 'male')
    female = sum(1 for s in sources if s.get('gender') == 'female')
    unknown = sum(1 for s in sources if s.get('gender') not in ['male', 'female'])

    # Build new source data
    new_data = {
        'quoted_sources': len(sources),
        'quoted_sources_confirmed': len(sources),
        'sources_male': male,
        'sources_female': female,
        'sources_unknown': unknown,
        'source_evidence': [
            {
                'name': s['name'],
                'gender': s.get('gender', 'unknown'),
                'position': 'groq_detected'  # Indicate Groq was used
            }
            for s in sources
        ]
    }
    new_data['source_evidence_confirmed'] = new_data['source_evidence']

    return new_data, None

def save_incremental_progress(data, data_file, timestamp):
    """Save progress to temporary file"""
    temp_file = f"data/backfill_temp_{timestamp}.json"
    with open(temp_file, 'w') as f:
        json.dump(data, f, indent=2)
    return temp_file

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Backfill source detection using Groq LLM')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without saving')
    parser.add_argument('--limit', type=int, help='Limit processing to N articles (for testing)')
    parser.add_argument('--urls', nargs='+', help='Process only articles matching these URL slugs')
    args = parser.parse_args()

    print("=" * 80)
    print("SPRINT 8.4: BACKFILL SOURCE DETECTION (GROQ-POWERED)")
    print("=" * 80)
    if args.dry_run:
        print("MODE: DRY RUN (no changes will be saved)")
    if args.limit:
        print(f"LIMIT: Processing first {args.limit} articles only")
    if args.urls:
        print(f"FILTER: Processing only articles matching {len(args.urls)} URL slugs")
    print("=" * 80)
    print()

    # Load data
    print(f"Loading {DATA_FILE}...")
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    total_articles = len(data['articles'])
    print(f"✓ Loaded {total_articles} articles")
    print()

    # Create backup (even in dry-run mode, for safety)
    backup_path, timestamp = create_backup(DATA_FILE)
    print()

    # Prepare changelog
    changelog_path = f"data/backfill_changelog_{timestamp}.json"
    changelog = []

    # Determine which articles to process
    articles_to_process = data['articles']

    # Filter by URLs if specified
    if args.urls:
        filtered = []
        for article in articles_to_process:
            url = article.get('url', '')
            if any(slug in url for slug in args.urls):
                filtered.append(article)
        articles_to_process = filtered
        print(f"Filtered to {len(articles_to_process)} articles matching URL slugs")
        print()

    # Apply limit
    if args.limit:
        articles_to_process = articles_to_process[:args.limit]

    process_count = len(articles_to_process)

    if process_count == 0:
        print("No articles to process!")
        sys.exit(0)

    # Process articles
    print("=" * 80)
    print(f"PROCESSING ARTICLES (0/{process_count})")
    print("=" * 80)
    print()

    stats = {
        'processed': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
        'groq_failures': 0,
        'source_changes': []
    }

    for idx, article in enumerate(articles_to_process, 1):
        headline = article.get('headline', 'Unknown')
        url = article.get('url', '')
        old_sources = article.get('quoted_sources_confirmed', 0)
        old_evidence = article.get('source_evidence_confirmed', [])

        # Progress indicator
        if idx % 10 == 0 or idx == 1:
            print(f"\n[{idx}/{process_count}] Processing articles...")

        print(f"  {headline[:70]}")

        # Update article sources using Groq
        new_data, error = update_article_sources_groq(article)

        if error:
            print(f"    ✗ Error: {error}")
            stats['errors'] += 1

            if "Groq API failed" in error:
                stats['groq_failures'] += 1

            # Log error to changelog
            changelog.append({
                'url': url,
                'headline': headline,
                'status': 'error',
                'error': error
            })

            # Add delay even on error to avoid hammering server
            time.sleep(GROQ_DELAY / 2)
            continue

        # Check if sources changed
        new_sources = new_data['quoted_sources_confirmed']
        new_evidence = new_data['source_evidence_confirmed']

        # Create changelog entry
        change_entry = {
            'url': url,
            'headline': headline,
            'old_quoted_sources': old_sources,
            'new_quoted_sources': new_sources,
            'old_source_evidence': old_evidence,
            'new_source_evidence': new_evidence,
            'changed': new_sources != old_sources
        }
        changelog.append(change_entry)

        if new_sources != old_sources:
            stats['updated'] += 1
            diff = new_sources - old_sources
            diff_str = f"+{diff}" if diff > 0 else str(diff)

            stats['source_changes'].append({
                'headline': headline,
                'url': url,
                'old': old_sources,
                'new': new_sources,
                'diff': diff
            })

            print(f"    ↻ Sources: {old_sources} → {new_sources} ({diff_str})")

            # Show source names
            if new_evidence:
                source_names = [s['name'] for s in new_evidence]
                print(f"       Detected: {', '.join(source_names)}")
        else:
            stats['unchanged'] += 1
            print(f"    ✓ Unchanged ({new_sources} sources)")

        # Update article in data (only if not dry-run)
        if not args.dry_run:
            article_idx = data['articles'].index(article)
            for key, value in new_data.items():
                data['articles'][article_idx][key] = value

        stats['processed'] += 1

        # Incremental save every BATCH_SIZE articles
        if not args.dry_run and idx % BATCH_SIZE == 0:
            temp_file = save_incremental_progress(data, DATA_FILE, timestamp)
            print(f"    💾 Progress saved to {temp_file}")

        # Rate limiting - delay between Groq API calls
        if idx < process_count:
            time.sleep(GROQ_DELAY)

    # Save changelog
    print()
    print("=" * 80)
    print("SAVING CHANGELOG")
    print("=" * 80)
    print()

    print(f"Writing changelog to {changelog_path}...")
    with open(changelog_path, 'w') as f:
        json.dump(changelog, f, indent=2)
    print(f"✓ Changelog saved ({len(changelog)} entries)")

    # Save updated data (only if not dry-run)
    if not args.dry_run:
        print()
        print("=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)
        print()

        print(f"Writing to {DATA_FILE}...")
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print("✓ Saved")

        # Also update docs version
        docs_file = 'docs/metrics_verified.json'
        print(f"\nCopying to {docs_file}...")
        shutil.copy2(DATA_FILE, docs_file)
        print("✓ Copied")

        # Clean up temp file
        temp_file = f"data/backfill_temp_{timestamp}.json"
        if Path(temp_file).exists():
            Path(temp_file).unlink()
            print(f"\n✓ Cleaned up temporary file")
    else:
        print()
        print("=" * 80)
        print("DRY RUN - NO CHANGES SAVED")
        print("=" * 80)
        print()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Articles processed: {stats['processed']}/{process_count}")
    print(f"Updated:            {stats['updated']}")
    print(f"Unchanged:          {stats['unchanged']}")
    print(f"Errors:             {stats['errors']}")
    if stats['groq_failures'] > 0:
        print(f"  Groq API failures: {stats['groq_failures']}")
    print()

    if stats['source_changes']:
        print("=" * 80)
        print(f"SOURCE COUNT CHANGES ({len(stats['source_changes'])} articles)")
        print("=" * 80)
        print()

        # Show all changes
        for change in stats['source_changes']:
            diff_str = f"+{change['diff']}" if change['diff'] > 0 else str(change['diff'])
            print(f"{change['old']} → {change['new']} ({diff_str}): {change['headline'][:60]}")

    print()
    print("=" * 80)
    if args.dry_run:
        print("DRY RUN COMPLETE - Review changelog before running for real")
    else:
        print("BACKFILL COMPLETE")
    print("=" * 80)
    print()
    print(f"Backup:    {backup_path}")
    print(f"Changelog: {changelog_path}")
    print()

    if args.dry_run:
        print("To apply changes, run without --dry-run flag")
        print()

if __name__ == '__main__':
    main()

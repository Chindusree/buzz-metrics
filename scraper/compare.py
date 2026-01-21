#!/usr/bin/env python3
"""
BUzz Metrics Comparator - Sprint 6.5.2
Compares scrape.py and verify.py outputs using intelligent reconciliation.
Uses reconcile.py to merge sources with fuzzy matching and person validation.
Adds editorial metrics tracking (word count status, breaking news, daily stats).
"""

import json
import re
import shutil
import os
from datetime import datetime
from collections import defaultdict
from reconcile import reconcile_sources


def normalise_category(category):
    """
    Normalize category to one of three sections: General News, Sport, Features.
    Sprint 6.7.2: Provides consistent section grouping.
    """
    if not category:
        return 'General News'

    cat_lower = category.lower()

    sport_keywords = ['afc bournemouth', 'football', 'boxing', 'rugby',
                      'cricket', 'tennis', 'sport', 'athletic', 'cherries',
                      "men's football", 'racing', 'match racing', 'formula', 'wheelchair basketball']
    if any(kw in cat_lower for kw in sport_keywords):
        return 'Sport'

    if 'feature' in cat_lower or 'lifestyle' in cat_lower or 'health' in cat_lower:
        return 'Features'

    return 'General News'


def is_breaking_news(headline):
    """
    Detect breaking news using fuzzy pattern matching.
    Looks for: break, breaking, urgent, just in
    """
    pattern = r'\b(break|breaking|urgent|just\s?in)\b'
    return bool(re.search(pattern, headline.lower()))


def calculate_word_count_status(word_count, is_breaking):
    """
    Calculate word count status based on editorial guidelines.
    - None → unknown
    - Breaking news → standard (exempt from minimum)
    - Below 350 → below_minimum
    - 800+ → long_form
    - Otherwise → standard
    """
    if word_count is None:
        return 'unknown'

    if is_breaking:
        return 'standard'  # Breaking news exempt from minimum

    if word_count < 350:
        return 'below_minimum'
    elif word_count >= 800:
        return 'long_form'
    else:
        return 'standard'


def calculate_confidence(confirmed_count, possible_count):
    """
    Calculate confidence score based on reconciled source counts.
    New logic for Sprint 6.5:
    - If confirmed >= 2 → high (strong evidence)
    - If confirmed == 1 → medium (some evidence)
    - If confirmed == 0 and possible > 0 → low (weak evidence from verify only)
    - If confirmed == 0 and possible == 0 → medium (no sources, but not necessarily wrong)
    """
    if confirmed_count >= 2:
        return "high"
    elif confirmed_count == 1:
        return "medium"
    elif possible_count > 0:
        return "low"
    else:
        return "medium"


def main():
    print("=" * 80)
    print("BUzz Metrics Comparator - Sprint 6.5.2")
    print("=" * 80)
    print()

    # Load scrape results
    print("Loading metrics_raw.json...")
    with open('../data/metrics_raw.json', 'r', encoding='utf-8') as f:
        scrape_data = json.load(f)

    # Load verify results
    print("Loading verify_results.json...")
    with open('../data/verify_results.json', 'r', encoding='utf-8') as f:
        verify_data = json.load(f)

    # Create lookup dict for verify results by ID
    verify_lookup = {result['id']: result for result in verify_data['results']}

    # Process each article with reconciliation
    flagged_articles = []
    verified_articles = []

    print("Reconciling sources...")
    for i, article in enumerate(scrape_data['articles'], 1):
        article_id = article['id']
        scrape_count = article['quoted_sources']
        scrape_evidence = article.get('source_evidence', [])

        # Get verify result
        verify_result = verify_lookup.get(article_id, {})
        verify_count = verify_result.get('verify_quoted_sources', 0)
        verify_evidence = verify_result.get('verify_evidence', [])

        # Reconcile sources using fuzzy matching
        reconciled = reconcile_sources(scrape_evidence, verify_evidence)

        # Sprint 7.35: Apply position filter AFTER reconciliation
        # This is the ONLY place filtering happens - single source of truth
        from constants import DIRECT_QUOTE_POSITIONS, FALSE_POSITIVE_NAMES

        def is_valid_confirmed_source(source):
            """Source must have valid position AND not be a known false positive."""
            position = source.get('position', '')
            name = source.get('name', '')
            return position in DIRECT_QUOTE_POSITIONS and name not in FALSE_POSITIVE_NAMES

        reconciled['confirmed'] = [s for s in reconciled['confirmed'] if is_valid_confirmed_source(s)]
        reconciled['possible'] = [s for s in reconciled['possible'] if s.get('name', '') not in FALSE_POSITIVE_NAMES]

        confirmed_count = len(reconciled['confirmed'])
        possible_count = len(reconciled['possible'])
        filtered_count = len(reconciled['filtered'])

        # Calculate new confidence based on reconciled counts
        new_confidence = calculate_confidence(confirmed_count, possible_count)

        # Calculate editorial metrics
        is_breaking = is_breaking_news(article['headline'])
        word_count_status = calculate_word_count_status(article.get('word_count'), is_breaking)
        word_count_value = article.get('word_count') or 0
        is_long_form = word_count_value >= 800

        # Create verified article with new reconciliation fields
        verified_article = article.copy()
        verified_article['quoted_sources_confirmed'] = confirmed_count
        verified_article['quoted_sources_possible'] = possible_count
        verified_article['quoted_sources_confidence'] = new_confidence
        # Sprint 6.7.2: reconciled sources now include gender
        verified_article['source_evidence_confirmed'] = reconciled['confirmed']
        verified_article['source_evidence_possible'] = reconciled['possible']
        verified_article['sources_filtered_out'] = reconciled['filtered']

        # Add editorial metrics fields
        verified_article['is_breaking_news'] = is_breaking
        verified_article['is_long_form'] = is_long_form
        verified_article['word_count_status'] = word_count_status

        # Add normalized category (Sprint 6.7.2)
        verified_article['category_normalised'] = normalise_category(article.get('category_primary'))

        # Flag if there are filtered sources or possible sources (for manual review)
        if filtered_count > 0 or possible_count > 0:
            scrape_sources = [s['name'] for s in scrape_evidence]
            verify_sources = [s['name'] for s in verify_evidence]

            flagged_articles.append({
                'id': article_id,
                'url': article['url'],
                'headline': article['headline'],
                'scrape_count': scrape_count,
                'verify_count': verify_count,
                'confirmed_count': confirmed_count,
                'possible_count': possible_count,
                'filtered_count': filtered_count,
                'scrape_evidence': scrape_sources,
                'verify_evidence': verify_sources,
                'confirmed': reconciled['confirmed'],
                'possible': reconciled['possible'],
                'filtered': reconciled['filtered'],
                'review_status': 'pending'
            })

        verified_articles.append(verified_article)

    print(f"  Processed {len(verified_articles)} articles")

    # Calculate summary statistics
    total_word_count = sum(a.get('word_count', 0) for a in verified_articles if a.get('word_count'))
    articles_with_word_count = sum(1 for a in verified_articles if a.get('word_count'))
    avg_word_count = round(total_word_count / articles_with_word_count) if articles_with_word_count > 0 else 0

    total_sources = sum(a.get('quoted_sources_confirmed', 0) for a in verified_articles)
    avg_quoted_sources = round(total_sources / len(verified_articles), 1) if verified_articles else 0

    below_minimum_count = sum(1 for a in verified_articles if a.get('word_count_status') == 'below_minimum')
    long_form_count = sum(1 for a in verified_articles if a.get('word_count_status') == 'long_form')
    breaking_news_count = sum(1 for a in verified_articles if a.get('is_breaking_news'))

    # Calculate image statistics
    total_images = sum(a.get('images', {}).get('total', 0) for a in verified_articles)
    original_images = sum(a.get('images', {}).get('original', 0) for a in verified_articles)
    stock_images = sum(a.get('images', {}).get('stock', 0) for a in verified_articles)
    uncredited_images = sum(a.get('images', {}).get('uncredited', 0) for a in verified_articles)

    # Calculate by_section stats (Sprint 6.7.2)
    by_section = defaultdict(lambda: {'count': 0, 'total_word_count': 0, 'total_sources': 0})
    for a in verified_articles:
        section = a.get('category_normalised', 'General News')
        by_section[section]['count'] += 1
        by_section[section]['total_word_count'] += a.get('word_count', 0) or 0
        by_section[section]['total_sources'] += a.get('quoted_sources_confirmed', 0)

    by_section_formatted = {}
    for section, stats in by_section.items():
        by_section_formatted[section] = {
            'count': stats['count'],
            'words': stats['total_word_count'],
            'sources': stats['total_sources']
        }

    # Calculate gender breakdown (Sprint 6.7.2)
    gender_counts = {'male': 0, 'female': 0, 'unknown': 0}
    for a in verified_articles:
        confirmed_sources = a.get('source_evidence_confirmed', [])
        for source in confirmed_sources:
            gender = source.get('gender', 'unknown')
            if gender in gender_counts:
                gender_counts[gender] += 1

    # Calculate by_category stats
    by_category = defaultdict(lambda: {'count': 0, 'total_word_count': 0, 'total_sources': 0})
    for a in verified_articles:
        cat = a.get('category_primary', 'Unknown')
        by_category[cat]['count'] += 1
        by_category[cat]['total_word_count'] += a.get('word_count', 0) or 0
        by_category[cat]['total_sources'] += a.get('quoted_sources_confirmed', 0)

    by_category_formatted = {}
    for cat, stats in by_category.items():
        avg_wc = round(stats['total_word_count'] / stats['count']) if stats['count'] > 0 else 0
        avg_src = round(stats['total_sources'] / stats['count'], 1) if stats['count'] > 0 else 0
        by_category_formatted[cat] = {
            'count': stats['count'],
            'avg_word_count': avg_wc,
            'avg_sources': avg_src
        }

    # Calculate daily stats
    by_date = defaultdict(list)
    for a in verified_articles:
        by_date[a['date']].append(a)

    daily_stats = []
    for date, day_articles in sorted(by_date.items()):
        times = [a['time'] for a in day_articles if a.get('time')]
        first_publish = min(times) if times else None

        daily_stats.append({
            'date': date,
            'article_count': len(day_articles),
            'target': 12,
            'meets_target': len(day_articles) >= 12,
            'first_publish_time': first_publish,
            'first_publish_on_time': first_publish and first_publish < '10:00' if first_publish else None,
            'below_minimum_count': sum(1 for a in day_articles if a.get('word_count_status') == 'below_minimum'),
            'long_form_count': sum(1 for a in day_articles if a.get('word_count_status') == 'long_form')
        })

    # Save verified metrics (production data with updated confidence)
    verified_output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_articles': len(verified_articles),
        'summary': {
            'avg_word_count': avg_word_count,
            'avg_quoted_sources': avg_quoted_sources,
            'below_minimum_count': below_minimum_count,
            'long_form_count': long_form_count,
            'breaking_news_count': breaking_news_count,
            'total_images': total_images,
            'original_images': original_images,
            'stock_images': stock_images,
            'uncredited_images': uncredited_images,
            'gender_breakdown': gender_counts,
            'by_section': by_section_formatted,
            'by_category': by_category_formatted
        },
        'daily_stats': daily_stats,
        'articles': verified_articles
    }

    verified_path = '../data/metrics_verified.json'
    with open(verified_path, 'w', encoding='utf-8') as f:
        json.dump(verified_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved verified metrics to {verified_path}")

    # Auto-copy to docs for dashboard
    docs_path = os.path.join(os.path.dirname(verified_path), '..', 'docs', 'metrics_verified.json')
    shutil.copy(verified_path, docs_path)
    print(f"✓ Copied to {docs_path}")

    # Save flagged articles
    flagged_output = {
        'generated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_flagged': len(flagged_articles),
        'flagged_articles': flagged_articles
    }

    flagged_path = '../data/flagged.json'
    with open(flagged_path, 'w', encoding='utf-8') as f:
        json.dump(flagged_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved flagged articles to {flagged_path}")

    # Print summary
    print()
    print("=" * 80)
    print("RECONCILIATION SUMMARY")
    print("=" * 80)
    print(f"Total articles: {len(verified_articles)}")
    print(f"Flagged for review: {len(flagged_articles)}")
    print()

    # Show confidence distribution
    confidence_dist = {}
    for article in verified_articles:
        conf = article['quoted_sources_confidence']
        confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

    print("Confidence distribution:")
    for conf in ['high', 'medium', 'low']:
        count = confidence_dist.get(conf, 0)
        print(f"  {conf}: {count}")

    # Show reconciliation stats
    total_confirmed = sum(article['quoted_sources_confirmed'] for article in verified_articles)
    total_possible = sum(article['quoted_sources_possible'] for article in verified_articles)
    total_filtered = sum(len(article.get('sources_filtered_out', [])) for article in verified_articles)

    print()
    print("Reconciliation stats:")
    print(f"  Confirmed sources: {total_confirmed}")
    print(f"  Possible sources: {total_possible}")
    print(f"  Filtered sources: {total_filtered}")

    # Show editorial metrics
    print()
    print("Editorial metrics:")
    print(f"  Average word count: {avg_word_count}")
    print(f"  Average sources: {avg_quoted_sources}")
    print(f"  Below minimum (<350): {below_minimum_count}")
    print(f"  Long form (800+): {long_form_count}")
    print(f"  Breaking news: {breaking_news_count}")

    # Show daily stats
    print()
    print("Daily stats:")
    for day in daily_stats:
        target_status = "✓" if day['meets_target'] else "✗"
        time_status = "✓" if day['first_publish_on_time'] else "✗" if day['first_publish_on_time'] is not None else "?"
        print(f"  {day['date']}: {day['article_count']}/12 {target_status}, first: {day['first_publish_time'] or 'N/A'} {time_status}, below_min: {day['below_minimum_count']}, long: {day['long_form_count']}")

    # Show flagged articles
    if flagged_articles:
        print()
        print("Flagged articles (first 5):")
        for article in flagged_articles[:5]:
            print(f"  - {article['headline'][:60]}...")
            print(f"    Confirmed: {article['confirmed_count']}, Possible: {article['possible_count']}, Filtered: {article['filtered_count']}")
            if article['filtered']:
                print(f"    Filtered: {', '.join(article['filtered'])}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

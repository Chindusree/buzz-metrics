#!/usr/bin/env python3
"""
Controlled Test Dataset Scraper

Scrapes all 31 articles from January 16th, 2026 for verification.

Uses all existing extraction functions from scrape.py.
Outputs to metrics_raw.json as normal.
"""

import sys
import os
import json
from datetime import datetime

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

# Import extraction function from scrape.py
from scrape import extract_article_metadata

# Test URLs - All Jan 16th articles
TEST_URLS = [
    "https://buzz.bournemouth.ac.uk/2026/01/celebrating-the-rnlis-work-in-poole/",
    "https://buzz.bournemouth.ac.uk/2026/01/can-upfs-be-avoided-on-a-budget/",
    "https://buzz.bournemouth.ac.uk/2026/01/veganuary-not-just-a-trend-but-a-sustainable-goal/",
    "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-vitality-stadium-expansion-raises-light-pollution-concerns/",
    "https://buzz.bournemouth.ac.uk/2026/01/hotel-staff-take-the-plunge-for-charity/",
    "https://buzz.bournemouth.ac.uk/2026/01/podcast-the-toll-of-homelessness/",
    "https://buzz.bournemouth.ac.uk/2026/01/tonight-stitch-and-movie-night/",
    "https://buzz.bournemouth.ac.uk/2026/01/disconnect-to-reconnect-removing-smartphones-from-dorset-schools/",
    "https://buzz.bournemouth.ac.uk/2026/01/youngcherriesfall/",
    "https://buzz.bournemouth.ac.uk/2026/01/watch-live-345pm-sports-bulletin-january-16/",
    "https://buzz.bournemouth.ac.uk/2026/01/kevin-bales-tells-us-how-the-dementia-workshops-came-to-be/",
    "https://buzz.bournemouth.ac.uk/2026/01/poole-racing-driver-reza-seewooruthun-kicks-off-his-2026-season/",
    "https://buzz.bournemouth.ac.uk/2026/01/finding-strength-through-boxing-a-bournemouth-fighters-story/",
    "https://buzz.bournemouth.ac.uk/2026/01/var-errors-have-afc-bournemouth-in-the-forefront/",
    "https://buzz.bournemouth.ac.uk/2026/01/when-education-takes-a-stand/",
    "https://buzz.bournemouth.ac.uk/2026/01/lymingtons-sailor-extends-record-championship-reign-in-shenzhen/",
    "https://buzz.bournemouth.ac.uk/2026/01/oliver-glasner-set-to-leave-crystal-palace-in-june/",
    "https://buzz.bournemouth.ac.uk/2026/01/watch-live-2-30pm-bulletin-january-16/",
    "https://buzz.bournemouth.ac.uk/2026/01/military-microphone-business-in-upton-hit-by-tariffs/",
    "https://buzz.bournemouth.ac.uk/2026/01/breaking-oliver-glasner-confirms-marc-guehi-departure/",
    "https://buzz.bournemouth.ac.uk/2026/01/council-ramp-up-action-on-online-sales-of-age-restricted-products/",
    "https://buzz.bournemouth.ac.uk/2026/01/dorset-demons-wheelchair-basketball-at-heart-of-dorset/",
    "https://buzz.bournemouth.ac.uk/2026/01/dorset-police-are-appealing-for-dashcam-footage-of-a356-accident/",
    "https://buzz.bournemouth.ac.uk/2026/01/running-together-how-bournemouths-run-clubs-are-building-community/",
    "https://buzz.bournemouth.ac.uk/2026/01/southern-league-premier-south-preview/",
    "https://buzz.bournemouth.ac.uk/2026/01/afc-bournemouth-submit-bid-for-highly-rated-brazilian-teenager/",
    "https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/",
    "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/",
    "https://buzz.bournemouth.ac.uk/2026/01/poole-towns-kitmen-aiming-to-complete-the-92/",
    "https://buzz.bournemouth.ac.uk/2026/01/andoni-iraola-looks-ahead-to-brighton-test/",
    "https://buzz.bournemouth.ac.uk/2026/01/the-fast-fashion-disconnect/",
]


def main():
    print("=" * 80)
    print(f"Controlled Test Dataset Scraper - {len(TEST_URLS)} Articles")
    print("=" * 80)
    print()

    print(f"Scraping {len(TEST_URLS)} test articles...")
    print()

    articles = []

    for i, url in enumerate(TEST_URLS, 1):
        print(f"[{i}/{len(TEST_URLS)}] {url}")

        article = extract_article_metadata(url)

        if article:
            articles.append(article)
            print(f"  ✓ Success: {article['headline']}")
            print(f"    Author: {article['author']}")
            print(f"    Words: {article['word_count']}")
            print(f"    Sources: {len(article.get('source_evidence', []))}")
            print(f"    Type: {article['content_type']}")
        else:
            print(f"  ✗ Failed to extract article")

        print()

    print("-" * 80)
    print(f"Successfully extracted: {len(articles)} articles")
    print("-" * 80)
    print()

    # Save to metrics_raw.json (same format as scrape.py)
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_articles': len(articles),
        'articles': articles
    }

    output_path = '../data/metrics_raw.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Data saved to {output_path}")
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Quick test of exemption logic on sample articles
"""

import requests
import json
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
import sys
sys.path.insert(0, '/Users/creedharan/buzz-metrics/scraper')

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MODEL = "llama-3.3-70b-versatile"

# Import from production script
from sei_production import (
    prescreen_exempt,
    fetch_article_content,
    analyze_with_groq,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE
)

# Test articles
TEST_ARTICLES = [
    {
        'headline': 'Southampton end winless run with victory over Sheffield United',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/southampton-end-winless-run-with-victory-over-sheffield-united/',
        'expected_exempt': 'match_report'
    },
    {
        'headline': 'Wonderkid Mayes hits record breaking 191',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/wonderkid-mayes-hits-record-breaking-191/',
        'expected_exempt': None
    },
    {
        'headline': 'BREAKING: Carrick agrees to Manchester United job',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/breaking-carrick-agrees-to-manchester-united-job/',
        'expected_exempt': 'breaking_news'
    },
    {
        'headline': 'LIVE BLOG: Andoni Iraola previews Liverpool clash',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/live-blog-andoni-iraola-previews-liverpool-clash/',
        'expected_exempt': 'live_blog'
    }
]

def main():
    results = []

    for article in TEST_ARTICLES:
        print(f"\n{'='*80}")
        print(f"Testing: {article['headline']}")
        print(f"Expected: {article['expected_exempt']}")
        print(f"{'='*80}")

        # Test Layer 1
        prescreen = prescreen_exempt(article)
        print(f"Layer 1 (regex): {prescreen}")

        if prescreen:
            results.append({
                'headline': article['headline'],
                'expected': article['expected_exempt'],
                'actual': prescreen,
                'layer': 'regex',
                'match': prescreen == article['expected_exempt']
            })
            continue

        # Test Layer 2
        try:
            body, is_shorthand = fetch_article_content(article['url'])
            if not body:
                print("ERROR: Could not fetch content")
                continue

            word_count = len(body.split())
            content_type = 'shorthand' if is_shorthand else 'standard'

            print(f"Fetched: {word_count} words, {content_type}")

            groq_response = analyze_with_groq(body, content_type, word_count, 'Unknown')

            groq_exempt = groq_response.get('sei_exempt')
            print(f"Layer 2 (Groq): {groq_exempt}")

            results.append({
                'headline': article['headline'],
                'expected': article['expected_exempt'],
                'actual': groq_exempt if groq_exempt else 'not_exempt',
                'layer': 'groq',
                'match': groq_exempt == article['expected_exempt']
            })

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for r in results:
        status = "✓" if r['match'] else "✗"
        print(f"{status} {r['headline'][:50]}")
        print(f"  Expected: {r['expected']}, Got: {r['actual']} ({r['layer']})")

    # Save results
    with open('scraper/exemption_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to scraper/exemption_test_results.json")

if __name__ == "__main__":
    main()

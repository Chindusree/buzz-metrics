#!/usr/bin/env python3
"""
FULL SCAN: Find ALL Shorthand articles in the dataset
"""
import json
import requests
from bs4 import BeautifulSoup
import re
import time

print("="*100)
print("FULL SHORTHAND SCAN - ALL 215 ARTICLES")
print("="*100)

with open('data/metrics_verified.json', 'r') as f:
    verified = json.load(f)

with open('data/metrics_sei.json', 'r') as f:
    sei = json.load(f)

print(f"\nTotal articles: {len(verified['articles'])}")
print("\nScanning all Buzz pages for Shorthand iframes...")
print("(This will take ~2-3 minutes)\n")

shorthand_found = []
errors = []

for i, article in enumerate(verified['articles'], 1):
    url = article['url']
    headline = article['headline']

    if i % 20 == 0:
        print(f"Progress: {i}/215...")

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))

        if iframe:
            shorthand_url = iframe['src']

            # Get SEI data for this article
            sei_article = None
            for s in sei['articles']:
                if s['url'] == url:
                    sei_article = s
                    break

            metadata = sei_article.get('metadata', {}) if sei_article else {}
            content_type = metadata.get('content_type', 'UNKNOWN')
            word_count = metadata.get('word_count', 0)
            sei_score = sei_article.get('sei_score') if sei_article else None

            shorthand_found.append({
                'headline': headline,
                'url': url,
                'shorthand_url': shorthand_url,
                'content_type_in_sei': content_type,
                'word_count_in_sei': word_count,
                'sei_score': sei_score
            })

            print(f"{len(shorthand_found)}. {headline[:60]}")
            print(f"   Content type in SEI: {content_type}")
            print(f"   Word count in SEI: {word_count}")

    except Exception as e:
        errors.append({'url': url, 'error': str(e)})

    time.sleep(0.1)  # Rate limiting

print("\n" + "="*100)
print("SCAN COMPLETE")
print("="*100)

print(f"\n✓ Found {len(shorthand_found)} Shorthand articles")
print(f"✗ Errors: {len(errors)}")

# Analysis
print("\n" + "="*100)
print("ANALYSIS: Which Shorthand articles were NOT marked as 'shorthand' in SEI?")
print("="*100)

missed = [s for s in shorthand_found if s['content_type_in_sei'] != 'shorthand']

print(f"\nMissed: {len(missed)} articles")

if missed:
    print("\nArticles where sei_production.py did NOT detect Shorthand:")
    for i, article in enumerate(missed, 1):
        print(f"\n{i}. {article['headline'][:70]}")
        print(f"   URL: {article['url']}")
        print(f"   Content type marked as: {article['content_type_in_sei']}")
        print(f"   Word count: {article['word_count_in_sei']}")
        print(f"   SEI score: {article['sei_score']}")

# Save results
results = {
    'total_checked': len(verified['articles']),
    'shorthand_found': len(shorthand_found),
    'properly_detected': len([s for s in shorthand_found if s['content_type_in_sei'] == 'shorthand']),
    'missed_detection': len(missed),
    'all_shorthand': shorthand_found,
    'missed': missed
}

with open('scraper/full_shorthand_scan.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to: scraper/full_shorthand_scan.json")

# Summary
print("\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"Total articles scanned: {results['total_checked']}")
print(f"Shorthand articles found: {results['shorthand_found']}")
print(f"Properly detected by SEI: {results['properly_detected']}")
print(f"MISSED by SEI: {results['missed_detection']}")
print(f"Detection rate: {results['properly_detected']/results['shorthand_found']*100:.1f}%")

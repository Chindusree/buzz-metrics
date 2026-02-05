#!/usr/bin/env python3
"""
SHORTHAND CONTENT INTEGRITY AUDIT
Identify all Shorthand articles and verify content completeness
"""
import json
import requests
from bs4 import BeautifulSoup
import re

print("="*100)
print("TASK 1: FIND ALL SHORTHAND ARTICLES IN METRICS_SEI.JSON")
print("="*100)

# Load SEI data
with open('data/metrics_sei.json', 'r') as f:
    sei_data = json.load(f)

# Find all Shorthand articles
shorthand_articles = []

for article in sei_data['articles']:
    metadata = article.get('metadata', {})
    content_type = metadata.get('content_type', '')

    if content_type == 'shorthand':
        word_count = metadata.get('word_count', 0)
        sei_score = article.get('sei_score')

        shorthand_articles.append({
            'headline': article['headline'],
            'url': article['url'],
            'word_count': word_count,
            'sei_score': sei_score,
            'sei_exempt': article.get('sei_exempt', False)
        })

print(f"\nFound {len(shorthand_articles)} Shorthand articles\n")

for i, article in enumerate(shorthand_articles, 1):
    print(f"{i}. {article['headline'][:70]}")
    print(f"   URL: {article['url']}")
    print(f"   Word count: {article['word_count']}")
    print(f"   SEI score: {article['sei_score']}")
    print(f"   Exempt: {article['sei_exempt']}")
    print()

# TASK 2: IDENTIFY SUSPECTS
print("\n" + "="*100)
print("TASK 2: IDENTIFY INCOMPLETE FETCHES (word_count < 200)")
print("="*100)

suspects = [a for a in shorthand_articles if a['word_count'] < 200]

print(f"\nFound {len(suspects)} suspect articles:\n")

for i, article in enumerate(suspects, 1):
    print(f"{i}. {article['headline'][:70]}")
    print(f"   Word count: {article['word_count']} ⚠️ SUSPECT")
    print(f"   SEI score: {article['sei_score']}")
    print()

# TASK 3: ROOT CAUSE ANALYSIS
print("\n" + "="*100)
print("TASK 3: ROOT CAUSE - HOW IS CONTENT BEING FETCHED?")
print("="*100)

print("\nChecking fetch_article_content() in sei_production.py...")

with open('scraper/sei_production.py', 'r') as f:
    production_code = f.read()

# Find the fetch function
fetch_start = production_code.find('def fetch_article_content(url):')
fetch_end = production_code.find('\ndef ', fetch_start + 1)
fetch_function = production_code[fetch_start:fetch_end]

print("\nFetch function analysis:")
print("-" * 100)

if 'shorthandstories.com' in fetch_function:
    print("✓ Function DOES check for Shorthand iframes")
else:
    print("✗ Function DOES NOT check for Shorthand iframes")

if 'iframe' in fetch_function:
    print("✓ Function looks for iframe tags")
else:
    print("✗ Function does NOT look for iframe tags")

# Check if it fetches from Shorthand URL
if 'iframe[' in fetch_function or "find('iframe'" in fetch_function:
    print("✓ Function extracts iframe src")
else:
    print("✗ Function does NOT extract iframe src")

print("\nNow checking metrics_verified.json source...")

with open('data/metrics_verified.json', 'r') as f:
    verified_data = json.load(f)

# Check a suspect article in verified data
if suspects:
    test_url = suspects[0]['url']
    test_article = None

    for article in verified_data['articles']:
        if article['url'] == test_url:
            test_article = article
            break

    if test_article:
        print(f"\nSample suspect in metrics_verified.json:")
        print(f"Headline: {test_article['headline'][:70]}")
        print(f"Has 'content' field: {'content' in test_article}")
        print(f"Has 'word_count' field: {'word_count' in test_article}")

        if 'word_count' in test_article:
            print(f"Word count in verified: {test_article['word_count']}")

        if 'content' in test_article and test_article['content']:
            content_preview = test_article['content'][:200]
            print(f"\nContent preview (first 200 chars):")
            print(f"'{content_preview}...'")

print("\n" + "="*100)
print("TASK 4: LIVE TEST - CHECK ACTUAL BUZZ PAGES")
print("="*100)

print("\nTesting first 3 Shorthand articles to see iframe detection...")

for i, article in enumerate(shorthand_articles[:3], 1):
    print(f"\n{i}. Testing: {article['headline'][:60]}")
    print(f"   URL: {article['url']}")

    try:
        response = requests.get(article['url'], timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for Shorthand iframe
        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))

        if iframe:
            shorthand_url = iframe['src']
            print(f"   ✓ HAS SHORTHAND IFRAME")
            print(f"   Shorthand URL: {shorthand_url}")
        else:
            print(f"   ✗ NO SHORTHAND IFRAME FOUND")

            # Check for Shorthand div
            shorthand_div = soup.find('div', {'id': 'app'})
            if shorthand_div:
                print(f"   ✓ Found Shorthand #app div (native embed)")
            else:
                print(f"   ✗ No Shorthand content detected")

    except Exception as e:
        print(f"   ERROR: {e}")

# SUMMARY
print("\n" + "="*100)
print("AUDIT SUMMARY")
print("="*100)

print(f"\n1. Total Shorthand articles: {len(shorthand_articles)}")
print(f"2. Suspect articles (< 200 words): {len(suspects)}")
print(f"3. Percentage suspect: {len(suspects)/len(shorthand_articles)*100:.1f}%")

print("\n4. Content source analysis:")
print("   - Check if sei_production.py fetches from Shorthand iframes")
print("   - Check if it relies on pre-existing metrics_verified.json content")
print("   - Determine if scrape.py is the root cause")

print("\n5. Next steps will be determined after this audit completes.")

# Save results
audit_results = {
    'total_shorthand': len(shorthand_articles),
    'all_shorthand': shorthand_articles,
    'suspects': suspects,
    'suspect_count': len(suspects)
}

with open('scraper/shorthand_audit_results.json', 'w') as f:
    json.dump(audit_results, f, indent=2)

print(f"\n✓ Audit results saved to: scraper/shorthand_audit_results.json")

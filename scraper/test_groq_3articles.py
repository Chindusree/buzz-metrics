#!/usr/bin/env python3
"""
Test Groq integration on 3 diverse articles with sources
"""

import json
from scrape import extract_article_metadata

# Load existing data to find good test articles
with open('../data/metrics_raw.json') as f:
    data = json.load(f)

# Find 3 articles with different characteristics
test_articles = []

# Find an article with multiple sources
for article in reversed(data['articles']):
    if article['quoted_sources'] >= 2 and len(test_articles) == 0:
        test_articles.append({
            'url': article['url'],
            'headline': article['headline'],
            'expected_sources': article['quoted_sources'],
            'type': 'multiple sources'
        })

# Find an article with 1 source
for article in reversed(data['articles']):
    if article['quoted_sources'] == 1 and len(test_articles) == 1:
        test_articles.append({
            'url': article['url'],
            'headline': article['headline'],
            'expected_sources': article['quoted_sources'],
            'type': 'single source'
        })

# Find a sport article
for article in reversed(data['articles']):
    if article['display_category'] == 'Sport' and article['quoted_sources'] > 0 and len(test_articles) == 2:
        test_articles.append({
            'url': article['url'],
            'headline': article['headline'],
            'expected_sources': article['quoted_sources'],
            'type': 'sport article'
        })

print("=" * 80)
print("Testing Groq Integration - 3 Diverse Articles")
print("=" * 80)
print()

results = []
for i, test_article in enumerate(test_articles[:3], 1):
    print(f"\n{'=' * 80}")
    print(f"Article {i}/3 ({test_article['type']})")
    print('=' * 80)
    print(f"Headline: {test_article['headline']}")
    print(f"URL: {test_article['url']}")
    print(f"Expected sources (regex): {test_article['expected_sources']}")
    print()

    metadata = extract_article_metadata(test_article['url'])

    if metadata:
        print(f"\n✓ Extraction successful")
        print(f"Content Type: {metadata['content_type']}")
        print(f"Word Count: {metadata['word_count']}")
        print(f"\nGroq Results:")
        print(f"  Total Sources: {metadata['quoted_sources']}")
        print(f"  Male: {metadata['sources_male']}")
        print(f"  Female: {metadata['sources_female']}")
        print(f"  Unknown: {metadata['sources_unknown']}")

        if metadata['source_evidence']:
            print(f"\n  Source Details:")
            for j, source in enumerate(metadata['source_evidence'], 1):
                print(f"    {j}. {source['name']}")
                print(f"       Gender: {source['gender']} (method: {source.get('gender_method', 'N/A')})")
                print(f"       Type: {source.get('type', 'N/A')}")

        results.append({
            'headline': test_article['headline'][:60],
            'url': test_article['url'],
            'type': test_article['type'],
            'expected': test_article['expected_sources'],
            'groq': metadata['quoted_sources'],
            'sources': [s['name'] for s in metadata['source_evidence']]
        })
    else:
        print("✗ Failed to extract metadata")
        results.append({
            'headline': test_article['headline'][:60],
            'url': test_article['url'],
            'type': test_article['type'],
            'expected': test_article['expected_sources'],
            'groq': 0,
            'sources': []
        })

# Summary
print(f"\n\n{'=' * 80}")
print("COMPARISON SUMMARY")
print('=' * 80)
print(f"\n{'Type':<20} {'Expected':<10} {'Groq':<10} {'Match':<10}")
print('-' * 80)

for result in results:
    match = '✓' if result['expected'] == result['groq'] else '✗'
    print(f"{result['type']:<20} {result['expected']:<10} {result['groq']:<10} {match:<10}")

print('\n' + '=' * 80)
print("DETAILED RESULTS")
print('=' * 80)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['headline']}...")
    print(f"   Type: {result['type']}")
    print(f"   Expected: {result['expected']} | Groq: {result['groq']}")
    if result['sources']:
        print(f"   Sources detected: {', '.join(result['sources'])}")
    else:
        print(f"   Sources detected: None")

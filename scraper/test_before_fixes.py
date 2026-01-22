#!/usr/bin/env python3
"""
Test BEFORE fixes - show current Groq behavior
"""

from scrape import extract_article_metadata

test_articles = [
    {
        'name': 'Rapist sentenced',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/rapist-sentenced-following-assault-in-bournemouth-home/',
        'issue': 'Anonymous victim handling'
    },
    {
        'name': 'Poole sailors',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/poole-sailors-win-first-sailgp-race/',
        'issue': '"Three Poole sailors" incorrectly detected as source'
    }
]

print("=" * 80)
print("BEFORE FIXES - Current Groq Behavior")
print("=" * 80)

for i, article in enumerate(test_articles, 1):
    print(f"\n{'=' * 80}")
    print(f"Article {i}: {article['name']}")
    print('=' * 80)
    print(f"URL: {article['url']}")
    print(f"Issue: {article['issue']}")
    print()

    metadata = extract_article_metadata(article['url'])

    if metadata:
        print(f"Sources found: {metadata['quoted_sources']}")

        if metadata['source_evidence']:
            print("\nSource details:")
            for j, source in enumerate(metadata['source_evidence'], 1):
                print(f"  {j}. {source['name']}")
                print(f"     Gender: {source['gender']}")
                print(f"     Type: {source.get('type', 'N/A')}")
        else:
            print("No sources detected")
    else:
        print("Failed to extract metadata")

print("\n" + "=" * 80)
print("END BEFORE FIXES TEST")
print("=" * 80)

#!/usr/bin/env python3
"""
Test AFTER fixes - show new Groq behavior
"""

from scrape import extract_article_metadata

test_articles = [
    {
        'name': 'Rapist sentenced',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/rapist-sentenced-following-assault-in-bournemouth-home/',
        'expected_fix': '"The victim" should become "Anonymous victim"'
    },
    {
        'name': 'Poole sailors',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/poole-sailors-win-first-sailgp-race/',
        'expected_fix': 'Should not detect "Three Poole" as a source'
    }
]

print("=" * 80)
print("AFTER FIXES - New Groq Behavior")
print("=" * 80)

for i, article in enumerate(test_articles, 1):
    print(f"\n{'=' * 80}")
    print(f"Article {i}: {article['name']}")
    print('=' * 80)
    print(f"URL: {article['url']}")
    print(f"Expected fix: {article['expected_fix']}")
    print()

    metadata = extract_article_metadata(article['url'])

    if metadata:
        print(f"✓ Sources found: {metadata['quoted_sources']}")

        if metadata['source_evidence']:
            print("\nSource details:")
            for j, source in enumerate(metadata['source_evidence'], 1):
                print(f"  {j}. Name: '{source['name']}'")
                print(f"     Gender: {source['gender']}")
                print(f"     Type: {source.get('type', 'N/A')}")

                # Check for fixes
                if i == 1:  # Rapist article
                    if 'anonymous' in source['name'].lower() or 'unnamed' in source['name'].lower():
                        print(f"     ✓ FIX APPLIED: Anonymous source properly labeled")
                    elif source['name'].lower() in ['the victim', 'victim']:
                        print(f"     ✗ FIX NOT APPLIED: Still using generic label")

                if i == 2:  # Poole sailors
                    if 'three' in source['name'].lower() and 'poole' in source['name'].lower():
                        print(f"     ✗ ISSUE: Group descriptor detected as source")
                    elif source['name'] in ['Dylan Fletcher', 'Hannah Mills', 'Tom Slingsby', 'Stuart Bithell', 'Ellie Aldridge']:
                        print(f"     ✓ CORRECT: Individual sailor name")
        else:
            print("No sources detected")
    else:
        print("Failed to extract metadata")

print("\n" + "=" * 80)
print("END AFTER FIXES TEST")
print("=" * 80)

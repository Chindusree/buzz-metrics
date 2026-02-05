#!/usr/bin/env python3
"""
Test Groq integration on a single article with known sources
"""

from scrape import extract_article_metadata

# Test URL with known source
test_url = "https://buzz.bournemouth.ac.uk/2026/01/rapist-sentenced-following-assault-in-bournemouth-home/"

print("=" * 80)
print("Testing Groq on article with known source")
print("=" * 80)
print(f"\nURL: {test_url}\n")

metadata = extract_article_metadata(test_url)

if metadata:
    print(f"\nHeadline: {metadata['headline']}")
    print(f"Author: {metadata['author']}")
    print(f"Category: {metadata['category']}")
    print(f"Word Count: {metadata['word_count']}")
    print(f"Content Type: {metadata['content_type']}")
    print(f"\nQuoted Sources: {metadata['quoted_sources']}")
    print(f"  Male: {metadata['sources_male']}")
    print(f"  Female: {metadata['sources_female']}")
    print(f"  Unknown: {metadata['sources_unknown']}")

    if metadata['source_evidence']:
        print(f"\n{'=' * 80}")
        print(f"SOURCE DETAILS")
        print('=' * 80)
        for j, source in enumerate(metadata['source_evidence'], 1):
            print(f"\n{j}. {source['name']}")
            print(f"   Gender: {source['gender']}")
            print(f"   Gender Method: {source.get('gender_method', 'N/A')}")
            print(f"   Type: {source.get('type', 'N/A')}")
            print(f"   Position: {source.get('position', 'N/A')}")
            if 'quote_snippet' in source:
                print(f"   Quote: {source['quote_snippet'][:150]}...")
            if 'full_attribution' in source:
                print(f"   Attribution: {source['full_attribution']}")
    else:
        print("\nNo sources detected!")
else:
    print("Failed to extract metadata")

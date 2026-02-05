#!/usr/bin/env python3
"""
Verify: Anne Marie Moriarty detection in full article extraction
"""

from scrape import extract_article_metadata

# The BUzz article URL that embeds this Shorthand
article_url = "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-and-poole-college-strikes-feature/"

print("=" * 80)
print("VERIFYING ANNE MARIE MORIARTY DETECTION")
print("=" * 80)
print(f"\nArticle URL: {article_url}\n")

metadata = extract_article_metadata(article_url)

if metadata:
    print(f"✓ Metadata extracted successfully")
    print(f"\nContent type: {metadata['content_type']}")
    print(f"Word count: {metadata['word_count']}")
    print(f"Sources found: {metadata['quoted_sources']}")

    print("\n" + "=" * 80)
    print("SOURCE DETAILS")
    print("=" * 80)

    if metadata['source_evidence']:
        for i, source in enumerate(metadata['source_evidence'], 1):
            print(f"\n{i}. Name: {source['name']}")
            print(f"   Gender: {source['gender']}")
            print(f"   Gender Method: {source.get('gender_method', 'N/A')}")
            print(f"   Type: {source.get('type', 'N/A')}")
            print(f"   Position: {source.get('position', 'N/A')}")

        # Check if Anne Marie is there
        anne_marie_found = any('moriarty' in s['name'].lower() for s in metadata['source_evidence'])

        print("\n" + "=" * 80)
        if anne_marie_found:
            print("✅ RESULT: Anne Marie Moriarty WAS SUCCESSFULLY DETECTED")
        else:
            print("❌ RESULT: Anne Marie Moriarty WAS NOT DETECTED")
            print("\nExpected sources:")
            print("  - Ivan Darley")
            print("  - Anne Marie Moriarty")
            print("\nFound sources:")
            for s in metadata['source_evidence']:
                print(f"  - {s['name']}")
    else:
        print("No sources detected")
else:
    print("Failed to extract metadata")

print("=" * 80)

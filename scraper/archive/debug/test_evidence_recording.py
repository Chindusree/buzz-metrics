#!/usr/bin/env python3
"""
Test evidence recording exclusion in Groq prompt
Expected: 2 sources (Anonymous victim, Judge Fuller KC)
NOT 3 - Callender's words were from a recording, not a statement
"""

from scrape import extract_article_metadata

url = "https://buzz.bournemouth.ac.uk/2026/01/rapist-sentenced-following-assault-in-bournemouth-home/"

print("=" * 80)
print("EVIDENCE RECORDING TEST")
print("=" * 80)
print(f"URL: {url}")
print("\nExpected: 2 sources")
print("  1. Anonymous victim (quoted)")
print("  2. Judge Fuller KC (quoted)")
print("\nShould EXCLUDE: Callender (words from evidence recording, not direct statement)")
print("\n" + "-" * 80)

metadata = extract_article_metadata(url)

if metadata and metadata.get('source_evidence'):
    sources = metadata['source_evidence']
    print(f"\n✓ Groq detected: {len(sources)} sources\n")

    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   Gender: {source['gender']}")
        print(f"   Type: {source.get('type', 'N/A')}")
        print()

    # Check if correct
    expected_count = 2
    has_victim = any('victim' in s['name'].lower() for s in sources)
    has_judge = any('fuller' in s['name'].lower() for s in sources)
    has_callender = any('callender' in s['name'].lower() for s in sources)

    print("-" * 80)
    if len(sources) == expected_count and has_victim and has_judge and not has_callender:
        print("✅ PASS: Correctly detected 2 sources, excluded evidence recording")
    else:
        print("❌ FAIL:")
        if len(sources) != expected_count:
            print(f"  - Expected {expected_count} sources, got {len(sources)}")
        if not has_victim:
            print("  - Missing: Anonymous victim")
        if not has_judge:
            print("  - Missing: Judge Fuller KC")
        if has_callender:
            print("  - Incorrectly included: Callender (evidence recording should be excluded)")
else:
    print("✗ No sources detected or extraction failed")

print("=" * 80)

#!/usr/bin/env python3
"""
Test name parsing and gender value fixes
"""

from scrape import extract_article_metadata

url = "https://buzz.bournemouth.ac.uk/2026/01/ellingham-and-ringwood-vs-petersfield-preview/"

print("=" * 80)
print("NAME PARSING & GENDER VALUE TEST")
print("=" * 80)
print(f"URL: {url}")
print("\nExpected after fixes:")
print("  1. Matt (unknown) — not 'Says Matt', not gender='they'")
print("  2. Adam Higgins (male)")
print("\n" + "-" * 80)
print("AFTER FIXES:")
print("-" * 80)

metadata = extract_article_metadata(url)

if metadata and metadata.get('source_evidence'):
    sources = metadata['source_evidence']
    print(f"\nSources found: {len(sources)}\n")

    for i, source in enumerate(sources, 1):
        print(f"{i}. Name: '{source['name']}'")
        print(f"   Gender: {source['gender']}")
        print(f"   Type: {source.get('type', 'N/A')}")
        print()

    # Check for issues
    issues = []
    for source in sources:
        name = source['name']
        gender = source['gender']

        # Check for attribution verbs in name
        attribution_words = ['says', 'said', 'told', 'added', 'explained', 'confirmed']
        name_lower = name.lower()
        if any(name_lower.startswith(word) for word in attribution_words):
            issues.append(f"❌ '{name}' has attribution verb at start")

        # Check for "they" as gender value
        if gender == 'they':
            issues.append(f"❌ '{name}' has gender='they' (should be 'nonbinary' or 'unknown')")

    if issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✓ No issues found")

else:
    print("✗ No sources detected or extraction failed")

print("=" * 80)

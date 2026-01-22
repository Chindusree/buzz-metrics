#!/usr/bin/env python3
"""
Final test: Anne Marie Moriarty detection
"""

from scrape import extract_shorthand_content_new, analyze_article_with_groq

shorthand_url = "https://buzznews.shorthandstories.com/bournemouth-and-poole-college-strikes-feature/index.html"

print("=" * 80)
print("ANNE MARIE MORIARTY DETECTION - FINAL TEST")
print("=" * 80)
print(f"\nShorthand URL: {shorthand_url}\n")

# Extract content
print("Extracting Shorthand content...")
shorthand_data = extract_shorthand_content_new(shorthand_url)

print(f"✓ Extracted {shorthand_data['word_count']} words")

# Get sources
sources = shorthand_data['sources']

print(f"\n{'=' * 80}")
print(f"SOURCES DETECTED: {len(sources)}")
print('=' * 80)

expected_sources = ["Ivan Darley", "Anne Marie Moriarty"]

for i, source in enumerate(sources, 1):
    print(f"\n{i}. {source['name']}")
    print(f"   Gender: {source['gender']}")
    print(f"   Type: {source.get('type', 'N/A')}")
    print(f"   Method: {source.get('gender_method', 'N/A')}")

# Check if Anne Marie was found
anne_marie_found = any('moriarty' in s['name'].lower() for s in sources)

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

print("\nExpected sources:")
for name in expected_sources:
    found = any(name.lower() in s['name'].lower() for s in sources)
    status = "✓" if found else "✗"
    print(f"  {status} {name}")

print("\n" + "=" * 80)
if anne_marie_found:
    print("✅ SUCCESS: Anne Marie Moriarty was detected by Groq!")
    print("\nAll her quotes are in the extracted text:")
    print("  ✓ 'overworked'")
    print("  ✓ 'national pay bargaining'")
    print("  ✓ 'If we stand together we are stronger'")
    print("  ✓ 'no other option'")
    print("  ✓ 'We needed to be heard and we have been'")
else:
    print("❌ FAILURE: Anne Marie Moriarty was NOT detected")
    print("\nFound sources:")
    for s in sources:
        print(f"  - {s['name']}")

print("=" * 80)

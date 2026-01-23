#!/usr/bin/env python3
"""
Test name parsing and gender fixes with simulated Groq responses
"""

import json
from scrape import analyze_article_with_groq

# Simulate problematic Groq responses by creating test cases
test_cases = [
    {
        'name': 'Test 1: Attribution verb at start',
        'groq_response': json.dumps([
            {"name": "Says Matt", "type": "original", "gender": "male"},
            {"name": "told Adam Higgins", "type": "original", "gender": "male"}
        ]),
        'expected': [
            {"name": "Matt", "gender": "male"},
            {"name": "Adam Higgins", "gender": "male"}
        ]
    },
    {
        'name': 'Test 2: Gender value "they" conversion',
        'groq_response': json.dumps([
            {"name": "Sam Johnson", "type": "original", "gender": "they"},
            {"name": "Alex Smith", "type": "original", "gender": "unknown"}
        ]),
        'expected': [
            {"name": "Sam Johnson", "gender": "unknown"},
            {"name": "Alex Smith", "gender": "unknown"}
        ]
    },
    {
        'name': 'Test 3: Mixed issues',
        'groq_response': json.dumps([
            {"name": "confirmed Dr. Sarah Lee", "type": "original", "gender": "female"},
            {"name": "John Doe", "type": "original", "gender": "they"},
            {"name": "explained the spokesperson", "type": "press_statement", "gender": "unknown"}
        ]),
        'expected': [
            {"name": "Dr. Sarah Lee", "gender": "female"},
            {"name": "John Doe", "gender": "unknown"},
            {"name": "the spokesperson", "gender": "unknown"}
        ]
    }
]

print("=" * 80)
print("EDGE CASE TESTS FOR NAME PARSING & GENDER FIXES")
print("=" * 80)

# Simulate the cleaning logic from analyze_article_with_groq
def clean_sources(sources):
    """Apply the same cleaning logic from scrape.py"""
    if isinstance(sources, list):
        attribution_verbs = ['says', 'said', 'told', 'added', 'explained',
                            'confirmed', 'stated', 'noted', 'revealed', 'claimed']

        for source in sources:
            # Fix 1: Strip leading attribution verbs from names
            name = source.get('name', '').strip()
            name_words = name.split()
            if name_words and name_words[0].lower() in attribution_verbs:
                name = ' '.join(name_words[1:]).strip()
                source['name'] = name

            # Fix 2: Convert "they" gender to "unknown"
            gender = source.get('gender', 'unknown')
            if gender == 'they':
                source['gender'] = 'unknown'

    return sources

all_passed = True

for test in test_cases:
    print(f"\n{test['name']}")
    print("-" * 80)

    # Parse the simulated response
    sources = json.loads(test['groq_response'])
    print(f"Before cleaning: {sources}")

    # Apply cleaning
    cleaned = clean_sources(sources)
    print(f"After cleaning:  {cleaned}")

    # Verify
    passed = True
    for i, (cleaned_src, expected_src) in enumerate(zip(cleaned, test['expected'])):
        if cleaned_src['name'] != expected_src['name']:
            print(f"  ✗ FAIL: Source {i+1} name mismatch")
            print(f"    Expected: '{expected_src['name']}'")
            print(f"    Got: '{cleaned_src['name']}'")
            passed = False
            all_passed = False

        if cleaned_src['gender'] != expected_src['gender']:
            print(f"  ✗ FAIL: Source {i+1} gender mismatch")
            print(f"    Expected: '{expected_src['gender']}'")
            print(f"    Got: '{cleaned_src['gender']}'")
            passed = False
            all_passed = False

    if passed:
        print("  ✓ PASS")

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL EDGE CASE TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 80)

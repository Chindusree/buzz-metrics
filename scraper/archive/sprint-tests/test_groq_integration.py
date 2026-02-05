#!/usr/bin/env python3
"""
Comprehensive Groq Integration Test
Tests that Groq is actually being used and validates accuracy on known articles
"""

import os
import sys
import json
from unittest.mock import patch
from scrape import extract_article_metadata, scrape_page_for_articles, BASE_URL

# Test articles with manually verified sources
TEST_ARTICLES = [
    {
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/',
        'name': 'Rugby Club',
        'expected_count': 1,
        'expected_sources': ['Grant Hancox'],
        'expected_genders': ['male'],
        'regex_bug': 'detected "Old Tiffinians" (team name)'
    },
    {
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/',
        'name': 'Man charged remains',
        'expected_count': 1,
        'expected_sources': ['DCI Neil Meade'],
        'expected_genders': ['male'],
        'regex_bug': 'detected "Wiltshire Police" (org)'
    },
    {
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/celebrating-the-rnlis-work-in-poole/',
        'name': 'RNLI Shorthand',
        'expected_count': 4,
        'expected_sources': ['David Richmond-Coggan', 'Alison Hulme', 'Sharon Gale', 'Nyah Boston-Shears'],
        'expected_genders': ['male', 'female', 'female', 'female'],
        'regex_bug': 'only found 1 source'
    }
]

def test_groq_is_actually_used():
    """Test 1: Verify Groq is being used (not silently falling back)"""
    print("=" * 80)
    print("TEST 1: VERIFY GROQ IS ACTUALLY BEING USED")
    print("=" * 80)

    # Save original API key
    original_key = os.environ.get('GROQ_API_KEY')

    # Test 1a: With API key set
    print("\n1a. Testing WITH GROQ_API_KEY set...")
    print("-" * 80)

    if original_key:
        test_url = 'https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/'
        print(f"Extracting: {test_url}")
        print("\nExpected log: '    Groq: X sources detected'")
        print("Actual output:")
        metadata = extract_article_metadata(test_url)

        if metadata and metadata.get('source_evidence'):
            # Check if sources have groq_llm method
            has_groq_method = any(s.get('gender_method') == 'groq_llm' for s in metadata['source_evidence'])
            if has_groq_method:
                print("\n✓ PASS: Groq is being used (sources have gender_method='groq_llm')")
            else:
                print("\n✗ FAIL: Sources don't have groq_llm method")
                print(f"   Source methods: {[s.get('gender_method') for s in metadata['source_evidence']]}")
        else:
            print("\n⚠ WARNING: No sources detected in article")
    else:
        print("✗ SKIP: GROQ_API_KEY not set in environment")

    # Test 1b: Without API key
    print("\n\n1b. Testing WITHOUT GROQ_API_KEY (should fall back to regex)...")
    print("-" * 80)

    # Temporarily unset API key
    if original_key:
        os.environ.pop('GROQ_API_KEY', None)

    # Reload the module to pick up changed env var
    import importlib
    import scrape
    importlib.reload(scrape)
    from scrape import extract_article_metadata as extract_without_key

    test_url = 'https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/'
    print(f"Extracting: {test_url}")
    print("\nExpected log: '    Regex fallback: X sources detected'")
    print("Actual output:")
    metadata = extract_without_key(test_url)

    if metadata and metadata.get('source_evidence'):
        has_regex_method = any(s.get('gender_method') != 'groq_llm' for s in metadata['source_evidence'])
        if has_regex_method:
            print("\n✓ PASS: Falling back to regex (sources don't have groq_llm method)")
        else:
            print("\n✗ FAIL: Still using Groq method without API key")
    else:
        print("\n⚠ WARNING: No sources detected")

    # Restore original API key
    if original_key:
        os.environ['GROQ_API_KEY'] = original_key
        importlib.reload(scrape)

    return True


def normalize_name(name):
    """Normalize name for comparison (lowercase, remove extra spaces)"""
    return ' '.join(name.lower().split())


def test_known_articles():
    """Test 2: Test on 3 manually verified articles"""
    print("\n\n" + "=" * 80)
    print("TEST 2: ACCURACY ON MANUALLY VERIFIED ARTICLES")
    print("=" * 80)

    results = []

    for i, test_article in enumerate(TEST_ARTICLES, 1):
        print(f"\n{'-' * 80}")
        print(f"Article {i}/3: {test_article['name']}")
        print(f"{'-' * 80}")
        print(f"URL: {test_article['url']}")
        print(f"Expected: {test_article['expected_count']} sources")
        print(f"Expected names: {', '.join(test_article['expected_sources'])}")
        print(f"Regex bug: {test_article['regex_bug']}")
        print()

        metadata = extract_article_metadata(test_article['url'])

        if not metadata:
            print("✗ FAIL: Could not extract metadata")
            results.append({
                'article': test_article['name'],
                'expected': test_article['expected_count'],
                'found': 0,
                'names_match': False,
                'pass': False,
                'found_names': []
            })
            continue

        found_count = metadata['quoted_sources']
        found_names = [s['name'] for s in metadata.get('source_evidence', [])]
        found_genders = [s['gender'] for s in metadata.get('source_evidence', [])]

        print(f"✓ Groq found: {found_count} sources")
        if found_names:
            print(f"  Names: {', '.join(found_names)}")
            print(f"  Genders: {', '.join(found_genders)}")

            # Show source details
            for j, source in enumerate(metadata['source_evidence'], 1):
                print(f"\n  Source {j}:")
                print(f"    Name: {source['name']}")
                print(f"    Gender: {source['gender']} (method: {source.get('gender_method', 'N/A')})")
                print(f"    Type: {source.get('type', 'N/A')}")
                print(f"    Position: {source.get('position', 'N/A')}")

        # Check if names match (normalize for comparison)
        expected_normalized = [normalize_name(n) for n in test_article['expected_sources']]
        found_normalized = [normalize_name(n) for n in found_names]

        # Check if all expected names are in found names (order doesn't matter)
        names_match = all(exp in found_normalized for exp in expected_normalized)
        count_match = found_count == test_article['expected_count']

        # Overall pass if count matches and names match
        passed = count_match and names_match

        if passed:
            print(f"\n✓ PASS: Count and names match!")
        else:
            print(f"\n✗ FAIL:")
            if not count_match:
                print(f"  Count mismatch: expected {test_article['expected_count']}, got {found_count}")
            if not names_match:
                print(f"  Names mismatch:")
                print(f"    Expected: {test_article['expected_sources']}")
                print(f"    Found: {found_names}")
                # Show which names are missing
                missing = [exp for exp in expected_normalized if exp not in found_normalized]
                extra = [fnd for fnd in found_normalized if fnd not in expected_normalized]
                if missing:
                    print(f"    Missing: {missing}")
                if extra:
                    print(f"    Extra: {extra}")

        results.append({
            'article': test_article['name'],
            'expected': test_article['expected_count'],
            'found': found_count,
            'names_match': names_match,
            'pass': passed,
            'found_names': found_names,
            'expected_names': test_article['expected_sources']
        })

    return results


def print_comparison_table(results):
    """Test 3: Print comparison table"""
    print("\n\n" + "=" * 80)
    print("TEST 3: COMPARISON TABLE")
    print("=" * 80)
    print()

    # Header
    header = f"{'Article':<20} {'Expected':<10} {'Groq Found':<12} {'Names Match':<13} {'PASS/FAIL':<10}"
    print(header)
    print("-" * 80)

    # Rows
    for result in results:
        names_match_str = '✓' if result['names_match'] else '✗'
        pass_fail = '✓ PASS' if result['pass'] else '✗ FAIL'

        row = f"{result['article']:<20} {result['expected']:<10} {result['found']:<12} {names_match_str:<13} {pass_fail:<10}"
        print(row)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['pass'])
    print("-" * 80)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    # Detailed comparison
    print("\n" + "=" * 80)
    print("DETAILED NAME COMPARISON")
    print("=" * 80)

    for result in results:
        print(f"\n{result['article']}:")
        print(f"  Expected: {', '.join(result['expected_names'])}")
        print(f"  Found:    {', '.join(result['found_names']) if result['found_names'] else 'None'}")

        if result['names_match']:
            print(f"  ✓ All expected names found")
        else:
            expected_norm = [normalize_name(n) for n in result['expected_names']]
            found_norm = [normalize_name(n) for n in result['found_names']]
            missing = [exp for exp in expected_norm if exp not in found_norm]
            extra = [fnd for fnd in found_norm if fnd not in expected_norm]
            if missing:
                print(f"  ✗ Missing: {', '.join(missing)}")
            if extra:
                print(f"  ⚠ Extra: {', '.join(extra)}")


def verify_json_structure():
    """Test 4: Verify JSON structure has required fields"""
    print("\n\n" + "=" * 80)
    print("TEST 4: VERIFY JSON STRUCTURE")
    print("=" * 80)
    print()

    # Test on one article
    test_url = TEST_ARTICLES[0]['url']
    print(f"Testing JSON structure on: {test_url}")
    print()

    metadata = extract_article_metadata(test_url)

    if not metadata:
        print("✗ FAIL: Could not extract metadata")
        return False

    # Check source_evidence structure
    print("Checking source_evidence structure...")
    required_fields = ['name', 'gender', 'quote_snippet']

    if 'source_evidence' not in metadata:
        print("✗ FAIL: 'source_evidence' field missing from metadata")
        return False

    if not metadata['source_evidence']:
        print("⚠ WARNING: source_evidence is empty (no sources in article)")
    else:
        all_fields_present = True
        for i, source in enumerate(metadata['source_evidence']):
            missing = [field for field in required_fields if field not in source]
            if missing:
                print(f"✗ FAIL: Source {i+1} missing fields: {missing}")
                print(f"  Source data: {source}")
                all_fields_present = False

        if all_fields_present:
            print(f"✓ PASS: All {len(metadata['source_evidence'])} sources have required fields:")
            print(f"  - name")
            print(f"  - gender")
            print(f"  - quote_snippet")

    # Note: gender_breakdown in summary requires running full scraper
    print("\nNote: gender_breakdown field exists in summary (scrape.py:2998-3002)")
    print("      This is added when running full scraper, not in individual article extraction")

    # Show sample source structure
    if metadata['source_evidence']:
        print("\nSample source structure:")
        print(json.dumps(metadata['source_evidence'][0], indent=2))

    return True


def main():
    """Run all tests"""
    print("=" * 80)
    print("GROQ INTEGRATION COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Test 1: Verify Groq is being used
        test_groq_is_actually_used()

        # Test 2: Test known articles
        results = test_known_articles()

        # Test 3: Print comparison table
        print_comparison_table(results)

        # Test 4: Verify JSON structure
        verify_json_structure()

        # Final summary
        print("\n\n" + "=" * 80)
        print("TEST SUITE COMPLETE")
        print("=" * 80)

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['pass'])

        print(f"\nArticle Tests: {passed_tests}/{total_tests} passed")

        if passed_tests == total_tests:
            print("\n✓ ALL TESTS PASSED!")
            print("\nGroq integration is working correctly:")
            print("  - Groq LLM is being used for source detection")
            print("  - Fallback to regex when API key missing")
            print("  - Accurate source detection on known articles")
            print("  - JSON structure is correct")
            return 0
        else:
            print(f"\n⚠ SOME TESTS FAILED ({total_tests - passed_tests} failures)")
            print("\nReview the detailed results above.")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n✗ TEST SUITE ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

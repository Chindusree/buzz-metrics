#!/usr/bin/env python3
"""
Sprint 7.35: Regression test suite for source detection.

Run before EVERY push: python test_regression.py
All tests must pass or push is blocked.
"""

import json
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    """Load the verified metrics data."""
    with open('../data/metrics_verified.json', 'r') as f:
        return json.load(f)

def find_article(data, slug):
    """Find article by URL slug."""
    for a in data['articles']:
        if slug in a.get('url', '').lower():
            return a
    return None

def get_confirmed_names(article):
    """Get list of confirmed source names."""
    return [s.get('name', '') for s in article.get('source_evidence_confirmed', [])]

def test_pirates_no_false_positives(data):
    """Pirates article should have 1 source, no false positives."""
    article = find_article(data, 'pirates')
    if not article:
        return False, "Pirates article not found"

    confirmed = article.get('quoted_sources_confirmed', 0)
    names = get_confirmed_names(article)

    # Must have exactly 1 source
    if confirmed != 1:
        return False, f"Expected 1 source, got {confirmed}"

    # Must not include these false positives
    bad_names = ['David', 'Guy', 'Nigel', 'Kerr', 'Lawson', 'Wessex', 'AFC Bournemouth']
    for name in names:
        if name in bad_names:
            return False, f"False positive found: {name}"

    # Dan Ford should be the one source
    if 'Dan Ford' not in names:
        return False, f"Expected Dan Ford, got {names}"

    return True, "OK"

def test_array_count_match(data):
    """quoted_sources_confirmed must equal len(source_evidence_confirmed) for all articles."""
    mismatches = []
    for a in data['articles']:
        count = a.get('quoted_sources_confirmed', 0)
        array_len = len(a.get('source_evidence_confirmed', []))
        if count != array_len:
            mismatches.append(f"{a.get('headline', '')[:30]}: count={count}, array={array_len}")

    if mismatches:
        return False, f"Mismatches: {mismatches[:3]}"  # Show first 3
    return True, "OK"

def test_no_global_false_positives(data):
    """No known false positives in any article."""
    bad_names = {'AFC Bournemouth', 'Poole Harbour', 'Dorset Police', 'Tottenham Hotspur', 'COVID', 'Lambrini'}
    found = []
    for a in data['articles']:
        for s in a.get('source_evidence_confirmed', []):
            if s.get('name', '') in bad_names:
                found.append(f"{s['name']} in {a.get('headline', '')[:20]}")

    if found:
        return False, f"False positives: {found[:3]}"
    return True, "OK"

def test_upfs_has_sources(data):
    """UPFs article should detect Rebecca Brown."""
    article = find_article(data, 'upfs')
    if not article:
        return None, "UPFs article not in dataset (skip)"

    names = get_confirmed_names(article)
    if 'Rebecca Brown' not in names:
        return False, f"Missing Rebecca Brown, got: {names}"
    return True, "OK"

def main():
    print("=" * 60)
    print("SPRINT 7.35 REGRESSION TESTS")
    print("=" * 60)

    try:
        data = load_data()
    except FileNotFoundError:
        print("ERROR: data/metrics_verified.json not found")
        print("Run the pipeline first: python scrape.py && python verify.py && python compare.py")
        sys.exit(1)

    tests = [
        ("Array/Count Match", test_array_count_match),
        ("No Global False Positives", test_no_global_false_positives),
        ("Pirates: No False Positives", test_pirates_no_false_positives),
        ("UPFs: Has Sources", test_upfs_has_sources),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_func in tests:
        result, message = test_func(data)
        if result is None:
            print(f"  SKIP: {name} - {message}")
            skipped += 1
        elif result:
            print(f"  ✓ PASS: {name}")
            passed += 1
        else:
            print(f"  ✗ FAIL: {name} - {message}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        print("✗ REGRESSION DETECTED - DO NOT PUSH")
        sys.exit(1)
    else:
        print("✓ ALL TESTS PASSED - SAFE TO PUSH")
        sys.exit(0)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Sprint 7.16: Test Definitive Source Detection Fix

Problem: Sources detected by verify.py (spaCy NER) are demoted to "possible" even when valid.
This causes false negatives like "Abi Paler" showing 0 confirmed sources.

Root cause: reconcile_sources() treats scrape.py as authoritative and verify.py as supplementary.
But NER is actually better at finding names than regex.

Fix: Trust both detection methods equally. If either method finds a valid source, it's confirmed.

Test cases:
✓ Abi Paler (found by verify.py only) → CONFIRMED (was "possible" before)
✓ Becca Parker (found by both) → CONFIRMED
✓ AFC Bournemouth (found by scrape.py) → FILTERED
✓ COVID (found by verify.py) → FILTERED
"""

import sys
import os

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

from reconcile import reconcile_sources


def test_abi_paler_case():
    """
    Test the exact scenario from the bug report:
    - scrape.py misses "Abi Paler"
    - verify.py (NER) finds "Abi Paler"
    - Should be CONFIRMED, not "possible"
    """
    print("=" * 70)
    print("Test 1: Abi Paler Case - NER-Only Detection")
    print("=" * 70)
    print()

    # Simulate scrape.py finding nothing
    scrape = []

    # Simulate verify.py finding Abi Paler via NER
    verify = [
        {'name': 'Abi Paler'}
    ]

    result = reconcile_sources(scrape, verify)

    print("Input:")
    print(f"  scrape.py: {scrape}")
    print(f"  verify.py: {verify}")
    print()
    print("Output:")
    print(f"  confirmed: {result['confirmed']}")
    print(f"  possible: {result['possible']}")
    print(f"  filtered: {result['filtered']}")
    print()

    # Check result
    if len(result['confirmed']) == 1 and result['confirmed'][0]['name'] == 'Abi Paler':
        print("✓ PASS - Abi Paler in CONFIRMED (not 'possible')")
        print("  This is the definitive fix - NER detection trusted equally")
        return True
    else:
        print("✗ FAIL - Abi Paler not confirmed")
        if len(result['possible']) > 0:
            print(f"  ✗ Still in 'possible': {result['possible']}")
        return False


def test_both_methods_find_same_person():
    """
    Test when both scrape.py and verify.py find the same person
    Should appear once in confirmed, not duplicated
    """
    print("=" * 70)
    print("Test 2: Both Methods Find Same Person - Deduplication")
    print("=" * 70)
    print()

    scrape = [
        {'name': 'Becca Parker'}
    ]

    verify = [
        {'name': 'Becca Parker'}
    ]

    result = reconcile_sources(scrape, verify)

    print("Input:")
    print(f"  scrape.py: {scrape}")
    print(f"  verify.py: {verify}")
    print()
    print("Output:")
    print(f"  confirmed: {result['confirmed']}")
    print(f"  possible: {result['possible']}")
    print(f"  filtered: {result['filtered']}")
    print()

    # Should have exactly 1 entry in confirmed
    if len(result['confirmed']) == 1 and result['confirmed'][0]['name'] == 'Becca Parker':
        print("✓ PASS - No duplication, appears once in confirmed")
        return True
    else:
        print(f"✗ FAIL - Expected 1 confirmed, got {len(result['confirmed'])}")
        return False


def test_filtered_sources():
    """
    Test that obvious non-persons are still filtered out
    regardless of which method found them
    """
    print("=" * 70)
    print("Test 3: Filtering - Both Methods Respect is_obvious_non_person()")
    print("=" * 70)
    print()

    scrape = [
        {'name': 'AFC Bournemouth'},
        {'name': 'Becca Parker'}
    ]

    verify = [
        {'name': 'COVID'},
        {'name': 'John Smith'}
    ]

    result = reconcile_sources(scrape, verify)

    print("Input:")
    print(f"  scrape.py: {scrape}")
    print(f"  verify.py: {verify}")
    print()
    print("Output:")
    print(f"  confirmed: {result['confirmed']}")
    print(f"  possible: {result['possible']}")
    print(f"  filtered: {result['filtered']}")
    print()

    # Check results
    passed = True

    # Should have 2 confirmed: Becca Parker, John Smith
    confirmed_names = [s['name'] for s in result['confirmed']]
    if 'Becca Parker' not in confirmed_names or 'John Smith' not in confirmed_names:
        print("✗ FAIL - Missing valid sources in confirmed")
        passed = False
    else:
        print("✓ PASS - Valid sources confirmed")

    # Should have 2 filtered: AFC Bournemouth, COVID
    if 'AFC Bournemouth' not in result['filtered'] or 'COVID' not in result['filtered']:
        print("✗ FAIL - Missing non-persons in filtered")
        passed = False
    else:
        print("✓ PASS - Non-persons filtered")

    # Should have 0 in possible
    if len(result['possible']) > 0:
        print(f"✗ FAIL - 'possible' should be empty, got: {result['possible']}")
        passed = False
    else:
        print("✓ PASS - 'possible' is empty (deprecated)")

    return passed


def test_multiple_sources():
    """
    Test realistic scenario with multiple sources from both methods
    """
    print("=" * 70)
    print("Test 4: Multiple Sources - Realistic Scenario")
    print("=" * 70)
    print()

    scrape = [
        {'name': 'Becca Parker'},
        {'name': 'Simon Bull'}
    ]

    verify = [
        {'name': 'Becca Parker'},  # Duplicate of scrape
        {'name': 'Abi Paler'},      # New from NER
        {'name': 'Run Club'},       # Should be filtered
        {'name': 'John Smith'}      # New from NER
    ]

    result = reconcile_sources(scrape, verify)

    print("Input:")
    print(f"  scrape.py: {scrape}")
    print(f"  verify.py: {verify}")
    print()
    print("Output:")
    print(f"  confirmed: {result['confirmed']}")
    print(f"  possible: {result['possible']}")
    print(f"  filtered: {result['filtered']}")
    print()

    # Expected results
    expected_confirmed = ['Becca Parker', 'Simon Bull', 'Abi Paler', 'John Smith']
    expected_filtered = ['Run Club']

    confirmed_names = [s['name'] for s in result['confirmed']]

    # Check all expected confirmed sources present
    all_confirmed = all(name in confirmed_names for name in expected_confirmed)
    # Check no unexpected sources
    no_extras = len(confirmed_names) == len(expected_confirmed)

    if all_confirmed and no_extras:
        print(f"✓ PASS - All {len(expected_confirmed)} valid sources confirmed")
        for name in expected_confirmed:
            print(f"  ✓ {name}")
    else:
        print("✗ FAIL - Confirmed sources mismatch")
        print(f"  Expected: {expected_confirmed}")
        print(f"  Got: {confirmed_names}")
        return False

    if result['filtered'] == expected_filtered:
        print(f"✓ PASS - Filtered: {expected_filtered}")
    else:
        print("✗ FAIL - Filtered sources mismatch")
        print(f"  Expected: {expected_filtered}")
        print(f"  Got: {result['filtered']}")
        return False

    if len(result['possible']) == 0:
        print("✓ PASS - 'possible' is empty")
    else:
        print(f"✗ FAIL - 'possible' should be empty, got: {result['possible']}")
        return False

    return True


def test_philosophy_change():
    """
    Demonstrate the philosophy change with before/after comparison
    """
    print("=" * 70)
    print("Test 5: Philosophy Change - Before vs After")
    print("=" * 70)
    print()

    scrape = []
    verify = [{'name': 'Abi Paler'}]

    result = reconcile_sources(scrape, verify)

    print("Scenario: scrape.py finds nothing, verify.py (NER) finds 'Abi Paler'")
    print()
    print("BEFORE Sprint 7.16:")
    print("  confirmed: [] ← EMPTY")
    print("  possible: [{'name': 'Abi Paler', 'gender': 'unknown'}]")
    print("  Result: 0 confirmed sources ✗ FALSE NEGATIVE")
    print()
    print("AFTER Sprint 7.16:")
    print(f"  confirmed: {result['confirmed']}")
    print(f"  possible: {result['possible']}")
    print(f"  Result: 1 confirmed source ✓ CORRECT")
    print()

    if len(result['confirmed']) == 1 and result['confirmed'][0]['name'] == 'Abi Paler':
        print("✓ PASS - Philosophy change successful")
        print("  NER detection now trusted equally with pattern matching")
        return True
    else:
        print("✗ FAIL - Philosophy change not applied")
        return False


if __name__ == '__main__':
    print("Sprint 7.16: Definitive Source Detection Fix - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_abi_paler_case()
    print()
    all_passed &= test_both_methods_find_same_person()
    print()
    all_passed &= test_filtered_sources()
    print()
    all_passed &= test_multiple_sources()
    print()
    all_passed &= test_philosophy_change()
    print()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.16 DEFINITIVE FIX working correctly")
        print()
        print("Summary:")
        print("- NER-detected sources (verify.py) now CONFIRMED, not 'possible'")
        print("- Both scrape.py and verify.py trusted equally")
        print("- 'possible' category deprecated (always empty)")
        print("- Abi Paler and similar NER-only sources now show as confirmed")
        print("- No more false negatives from NER-only detection")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

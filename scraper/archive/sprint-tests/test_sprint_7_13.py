#!/usr/bin/env python3
"""
Sprint 7.13: Test NER Trust Fix

Bug: Real people rejected because first name not in gender-guesser database
Example: "Abi Paler" - valid person, but "Abi" returns unknown from gender-guesser

Root cause: is_likely_person() in reconcile.py rejects names where gender-guesser
returns unknown.

Fix: Trust NER more. If verify.py found it (spaCy PERSON entity), accept it even
if gender-guesser doesn't recognize the name.

Test cases:
✓ Should ACCEPT: "Abi Paler" (NER validated, gender unknown)
✓ Should ACCEPT: "Becca Parker" (NER validated, gender known)
✗ Should REJECT: "AFC Bournemouth" (org word "afc")
✗ Should REJECT: "Poole Harbour" (place suffix "harbour")
✗ Should REJECT: "COVID" (brand name)
"""

import sys
import os

# Add parent directory to path to import reconcile
sys.path.insert(0, os.path.dirname(__file__))

from reconcile import (
    is_obvious_non_person,
    is_likely_person,
    get_gender,
    reconcile_sources
)


def test_is_obvious_non_person():
    """Test the new is_obvious_non_person() function"""
    print("=" * 70)
    print("Test 1: is_obvious_non_person() - Conservative filtering")
    print("=" * 70)
    print()

    test_cases = [
        # Should ACCEPT (False = not obvious non-person)
        ('Abi Paler', False, 'Unknown name, but could be person'),
        ('Becca Parker', False, 'Known name, definitely person'),
        ('John Smith', False, 'Common name'),
        ('Xyz Abc', False, 'Unusual name, but no org/place indicators'),

        # Should REJECT (True = obvious non-person)
        ('AFC Bournemouth', True, 'Contains org word "afc"'),
        ('Poole Harbour', True, 'Ends with place suffix "harbour"'),
        ('Town Centre', True, 'Ends with place suffix "centre"'),
        ('COVID', True, 'Brand/product keyword'),
        ('Lambrini', True, 'Brand/product keyword'),
        ('Bournemouth University', True, 'Contains org word "university"'),
        ('Police Department', True, 'Contains org word "police"'),
    ]

    passed = 0
    failed = 0

    for name, expected_non_person, reason in test_cases:
        result = is_obvious_non_person(name)
        status = "✓" if result == expected_non_person else "✗"
        outcome = "PASS" if result == expected_non_person else "FAIL"

        print(f"{status} '{name}'")
        print(f"   Expected: {expected_non_person} (reason: {reason})")
        print(f"   Got: {result}")
        print(f"   Result: {outcome}")
        print()

        if result == expected_non_person:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_comparison_with_old_function():
    """Compare is_obvious_non_person() with old is_likely_person()"""
    print("=" * 70)
    print("Test 2: Comparison - Old vs New Validation")
    print("=" * 70)
    print()

    test_cases = [
        ('Abi Paler', 'Should accept (gender unknown but valid name)'),
        ('Becca Parker', 'Should accept (gender known)'),
        ('John Smith', 'Should accept (gender known)'),
        ('AFC Bournemouth', 'Should reject (organization)'),
        ('COVID', 'Should reject (brand)'),
    ]

    print(f"{'Name':<25} {'Old (is_likely_person)':<25} {'New (is_obvious_non_person)':<30}")
    print("-" * 80)

    for name, expected_behavior in test_cases:
        old_result = is_likely_person(name)  # True = accept
        new_result = is_obvious_non_person(name)  # True = reject

        # For new function, invert the result for comparison
        new_accept = not new_result

        old_status = "ACCEPT" if old_result else "REJECT"
        new_status = "ACCEPT" if new_accept else "REJECT"

        # Check if new function behaves correctly
        correct = True
        if 'should accept' in expected_behavior.lower():
            correct = new_accept
        elif 'should reject' in expected_behavior.lower():
            correct = not new_accept

        marker = "✓" if correct else "✗"

        print(f"{name:<25} {old_status:<25} {new_status:<30} {marker}")

    print()
    print("Key finding: Old function rejects 'Abi Paler' (gender unknown),")
    print("             New function accepts it (trusts NER validation)")
    print()


def test_reconcile_with_abi_paler():
    """Test full reconciliation with Abi Paler case"""
    print("=" * 70)
    print("Test 3: Full Reconciliation - Abi Paler Case")
    print("=" * 70)
    print()

    # Simulate scrape.py found nothing (pattern matching missed it)
    scrape = []

    # Simulate verify.py found "Abi Paler" via NER (spaCy PERSON entity)
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
    if len(result['possible']) == 1 and result['possible'][0]['name'] == 'Abi Paler':
        print("✓ PASS - Abi Paler correctly added to possible")
        print(f"  Gender: {result['possible'][0]['gender']} (may be 'unknown', that's OK)")
        return True
    else:
        print("✗ FAIL - Abi Paler not in possible sources")
        return False


def test_reconcile_filters_orgs():
    """Test that reconciliation still filters organizations"""
    print("=" * 70)
    print("Test 4: Full Reconciliation - Organization Filtering")
    print("=" * 70)
    print()

    scrape = []
    verify = [
        {'name': 'AFC Bournemouth'},
        {'name': 'Poole Harbour'},
        {'name': 'Becca Parker'},
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

    # Becca Parker should be in possible
    if not any(s['name'] == 'Becca Parker' for s in result['possible']):
        print("✗ FAIL - Becca Parker not in possible")
        passed = False
    else:
        print("✓ PASS - Becca Parker in possible")

    # AFC Bournemouth should be filtered
    if 'AFC Bournemouth' not in result['filtered']:
        print("✗ FAIL - AFC Bournemouth not filtered")
        passed = False
    else:
        print("✓ PASS - AFC Bournemouth filtered")

    # Poole Harbour should be filtered
    if 'Poole Harbour' not in result['filtered']:
        print("✗ FAIL - Poole Harbour not filtered")
        passed = False
    else:
        print("✓ PASS - Poole Harbour filtered")

    return passed


if __name__ == '__main__':
    print("Sprint 7.13: NER Trust Fix - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_is_obvious_non_person()
    test_comparison_with_old_function()
    all_passed &= test_reconcile_with_abi_paler()
    all_passed &= test_reconcile_filters_orgs()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.13 fix working correctly")
        print()
        print("Summary:")
        print("- Abi Paler (gender unknown) now accepted via NER trust")
        print("- Organizations still correctly filtered")
        print("- Gender detection still works (may return 'unknown')")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

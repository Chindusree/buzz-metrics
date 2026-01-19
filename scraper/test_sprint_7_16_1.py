#!/usr/bin/env python3
"""
Sprint 7.16.1: Test Single-Word Name Handling

Problem: Single-word names like "Gabrielle" and "Becca" are being filtered
because spaCy NER misclassifies them (Gabrielle → ORG, Becca → GPE).

Root cause: spaCy NER is unreliable for single-word names without context.

Fix: For single-word names, use gender-guesser as tiebreaker BEFORE checking NER.
Check brand blacklist first to prevent "Lambrini" → kept.

Test cases:
✓ "Gabrielle" → KEEP (recognized female name, despite NER → ORG)
✓ "Becca" → KEEP (recognized female name, despite NER → GPE)
✓ "Lambrini" → FILTER (brand blacklist)
✓ "COVID" → FILTER (brand blacklist)
✓ "David" → KEEP (recognized male name)
✓ "XYZ" → FILTER (unknown single word, likely abbreviation)
✓ "David Richmond" → KEEP (multi-word, NER works fine)
✓ "Run Club" → FILTER (multi-word, NER → ORG)
"""

import sys
import os

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

from reconcile import is_obvious_non_person


def test_single_word_names():
    """
    Test that single-word first names are kept despite NER misclassification
    """
    print("=" * 70)
    print("Test 1: Single-Word Name Handling (Sprint 7.16.1)")
    print("=" * 70)
    print()

    test_cases = [
        # Single-word names that should be KEPT (recognized by gender-guesser)
        {
            'name': 'Gabrielle',
            'expected': False,  # False = keep (not obvious non-person)
            'reason': 'Recognized female name (gender-guesser), despite NER → ORG'
        },
        {
            'name': 'Becca',
            'expected': False,
            'reason': 'Recognized female name (gender-guesser), despite NER → GPE'
        },
        {
            'name': 'David',
            'expected': False,
            'reason': 'Recognized male name (gender-guesser)'
        },
        {
            'name': 'Rebecca',
            'expected': False,
            'reason': 'Recognized female name (gender-guesser)'
        },
        {
            'name': 'John',
            'expected': False,
            'reason': 'Recognized male name (gender-guesser)'
        },

        # Single-word brands that should be FILTERED (blacklist)
        {
            'name': 'Lambrini',
            'expected': True,  # True = filter (obvious non-person)
            'reason': 'Brand in blacklist'
        },
        {
            'name': 'COVID',
            'expected': True,
            'reason': 'Brand in blacklist'
        },
        {
            'name': 'Guinness',
            'expected': True,
            'reason': 'Brand in blacklist'
        },

        # Unknown single words that should be FILTERED
        {
            'name': 'XYZ',
            'expected': True,
            'reason': 'Unknown single word, likely org abbreviation'
        },
        {
            'name': 'ABC',
            'expected': True,
            'reason': 'Unknown single word, likely org abbreviation'
        },
    ]

    passed = 0
    failed = 0

    print(f"{'Name':<15} {'Expected':<12} {'Result':<12} {'Status':<10}")
    print("-" * 70)

    for test in test_cases:
        name = test['name']
        expected = test['expected']
        reason = test['reason']

        result = is_obvious_non_person(name)

        expected_str = "FILTER" if expected else "KEEP"
        result_str = "FILTER" if result else "KEEP"

        if result == expected:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"{name:<15} {expected_str:<12} {result_str:<12} {status:<10}")
        print(f"  → {reason}")

    print()
    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_multi_word_names_unchanged():
    """
    Test that multi-word names still work correctly (no regression)
    """
    print("=" * 70)
    print("Test 2: Multi-Word Names (Regression Check)")
    print("=" * 70)
    print()

    test_cases = [
        # Multi-word person names (should be KEPT)
        {
            'name': 'David Richmond',
            'expected': False,
            'reason': 'NER → PERSON'
        },
        {
            'name': 'Abi Paler',
            'expected': False,
            'reason': 'No NER match, trusted'
        },
        {
            'name': 'Becca Parker',
            'expected': False,
            'reason': 'NER → PERSON'
        },

        # Multi-word organizations (should be FILTERED)
        {
            'name': 'Run Club',
            'expected': True,
            'reason': 'NER → ORG'
        },
        {
            'name': 'India Council',
            'expected': True,
            'reason': 'NER → ORG'
        },
        {
            'name': 'Poole Harbour',
            'expected': True,
            'reason': 'Fallback: ends with "harbour"'
        },
        {
            'name': 'AFC Bournemouth',
            'expected': True,
            'reason': 'NER → ORG'
        },
    ]

    passed = 0
    failed = 0

    print(f"{'Name':<20} {'Expected':<12} {'Result':<12} {'Status':<10}")
    print("-" * 70)

    for test in test_cases:
        name = test['name']
        expected = test['expected']
        reason = test['reason']

        result = is_obvious_non_person(name)

        expected_str = "FILTER" if expected else "KEEP"
        result_str = "FILTER" if result else "KEEP"

        if result == expected:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"{name:<20} {expected_str:<12} {result_str:<12} {status:<10}")
        print(f"  → {reason}")

    print()
    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_problem_cases_from_brief():
    """
    Test the specific cases mentioned in the Sprint 7.16.1 brief
    """
    print("=" * 70)
    print("Test 3: Problem Cases from Brief")
    print("=" * 70)
    print()

    test_cases = [
        {
            'name': 'Gabrielle',
            'expected': False,
            'before': 'FILTERED (NER → ORG)',
            'after': 'KEPT (gender-guesser → female)'
        },
        {
            'name': 'Becca',
            'expected': False,
            'before': 'FILTERED (NER → GPE)',
            'after': 'KEPT (gender-guesser → female)'
        },
        {
            'name': 'Lambrini',
            'expected': True,
            'before': 'FILTERED (brand)',
            'after': 'FILTERED (blacklist)'
        },
        {
            'name': 'COVID',
            'expected': True,
            'before': 'FILTERED (brand)',
            'after': 'FILTERED (blacklist)'
        },
    ]

    print("Scenario: verify.py (NER) finds single-word name")
    print()

    all_passed = True

    for test in test_cases:
        name = test['name']
        expected = test['expected']
        before = test['before']
        after = test['after']

        result = is_obvious_non_person(name)

        expected_str = "FILTER" if expected else "KEEP"
        result_str = "FILTER" if result else "KEEP"

        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False

        print(f"Name: {name}")
        print(f"  BEFORE Sprint 7.16.1: {before}")
        print(f"  AFTER Sprint 7.16.1: {after}")
        print(f"  Expected: {expected_str}, Got: {result_str} - {status}")
        print()

    return all_passed


def test_priority_order():
    """
    Test that the priority order is correct:
    1. Brand blacklist
    2. Single-word → gender-guesser
    3. Multi-word → spaCy NER
    """
    print("=" * 70)
    print("Test 4: Priority Order Verification")
    print("=" * 70)
    print()

    print("Priority order:")
    print("1. Brand check (brands list)")
    print("2. Single-word check → gender-guesser")
    print("3. spaCy NER (multi-word)")
    print("4. Fallback heuristics (suffixes)")
    print("5. Default (trust it)")
    print()

    test_cases = [
        {
            'name': 'COVID',
            'priority': 1,
            'expected': True,
            'reason': 'Brand check catches it BEFORE single-word check'
        },
        {
            'name': 'Gabrielle',
            'priority': 2,
            'expected': False,
            'reason': 'Single-word → gender-guesser → female → KEEP'
        },
        {
            'name': 'Run Club',
            'priority': 3,
            'expected': True,
            'reason': 'Multi-word → spaCy NER → ORG → FILTER'
        },
        {
            'name': 'Poole Harbour',
            'priority': 4,
            'expected': True,
            'reason': 'Fallback: ends with "harbour" → FILTER'
        },
        {
            'name': 'Unknown Person',
            'priority': 5,
            'expected': False,
            'reason': 'Default: no match → trust it → KEEP'
        },
    ]

    all_passed = True

    for test in test_cases:
        name = test['name']
        priority = test['priority']
        expected = test['expected']
        reason = test['reason']

        result = is_obvious_non_person(name)

        expected_str = "FILTER" if expected else "KEEP"
        result_str = "FILTER" if result else "KEEP"

        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False

        print(f"Priority {priority}: {name}")
        print(f"  Expected: {expected_str}, Got: {result_str} - {status}")
        print(f"  → {reason}")
        print()

    return all_passed


if __name__ == '__main__':
    print("Sprint 7.16.1: Single-Word Name Handling - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_single_word_names()
    all_passed &= test_multi_word_names_unchanged()
    all_passed &= test_problem_cases_from_brief()
    all_passed &= test_priority_order()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.16.1 single-word name handling working")
        print()
        print("Summary:")
        print("- Single-word names (Gabrielle, Becca) now KEPT via gender-guesser")
        print("- Brand blacklist checked BEFORE gender-guesser")
        print("- Multi-word names still work correctly (no regression)")
        print("- Unknown single words filtered (likely org abbreviations)")
        print("- Priority order: brands → single-word → NER → fallback → default")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

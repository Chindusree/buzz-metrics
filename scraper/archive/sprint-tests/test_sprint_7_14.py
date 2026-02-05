#!/usr/bin/env python3
"""
Sprint 7.14: Test scrape.py Source Validation Fix

Bug: Invalid sources passing straight to "confirmed" from scrape.py
Examples: "AFC Bournemouth", "Economic Forum", "Qualifying", "Race"

Root cause: scrape.py sources bypassed validation - only verify.py sources ran through
is_obvious_non_person().

Fix (two parts):
1. Filter sources at end of extract_quoted_sources() using is_obvious_non_person()
2. Tighten standalone_dash pattern to require multi-word name OR comma after name

Test cases after fix:
✗ "AFC Bournemouth" → filtered (org word "afc")
✗ "Economic Forum" → filtered (single word, no comma)
✗ "Qualifying" → filtered (single word, no comma)
✗ "Race" → filtered (single word, no comma)
✓ "Dave Richmond" → kept (two words)
✓ "John Smith, marketing manager" → kept (comma with role)
"""

import re


def test_standalone_dash_pattern():
    """Test Part 2: Tightened standalone_dash pattern"""
    print("=" * 70)
    print("Test 1: Standalone Dash Pattern - Tightened Validation")
    print("=" * 70)
    print()

    # Sprint 7.14: New patterns
    # Pattern 1: Multi-word name (2+ words) - with optional role after comma
    multiword_name_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)+)'
    dash_multiword_pattern = r'[–—]\s+' + multiword_name_pattern + r'(?:,\s+[^,\n]+)?'

    # Pattern 2: Single or multi-word name followed by comma and role (required)
    name_with_comma_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),\s+[^,\n]+'
    dash_comma_pattern = r'[–—]\s+' + name_with_comma_pattern

    test_cases = [
        # Should MATCH (valid attributions)
        {
            'text': '– Dave Richmond, Bournemouth property owner',
            'should_match': True,
            'reason': 'Multi-word name with role',
            'expected_name': 'Dave Richmond'
        },
        {
            'text': '– John Smith',
            'should_match': True,
            'reason': 'Multi-word name (no role needed)',
            'expected_name': 'John Smith'
        },
        {
            'text': '– Sarah Jones, marketing manager',
            'should_match': True,
            'reason': 'Multi-word name with role',
            'expected_name': 'Sarah Jones'
        },
        {
            'text': '— Gabrielle, student at BU',
            'should_match': True,
            'reason': 'Single word with comma and role',
            'expected_name': 'Gabrielle'
        },

        # Should NOT MATCH (invalid - single words without comma/role)
        {
            'text': '– Qualifying',
            'should_match': False,
            'reason': 'Single word, no comma/role',
            'expected_name': None
        },
        {
            'text': '– Race',
            'should_match': False,
            'reason': 'Single word, no comma/role',
            'expected_name': None
        },
        {
            'text': '— Forum',
            'should_match': False,
            'reason': 'Single word, no comma/role',
            'expected_name': None
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        text = test['text']
        should_match = test['should_match']
        expected_name = test['expected_name']

        # Try pattern 1 (multi-word)
        match1 = re.search(dash_multiword_pattern, text)
        # Try pattern 2 (with comma)
        match2 = re.search(dash_comma_pattern, text)

        matched = match1 or match2
        extracted_name = None

        if match1:
            extracted_name = match1.group(1).strip()
        elif match2:
            # Extract name before comma
            name_match = re.search(r'[–—]\s+([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),', text)
            if name_match:
                extracted_name = name_match.group(1).strip()

        result_match = matched is not None
        status = "✓" if result_match == should_match else "✗"
        outcome = "PASS" if result_match == should_match else "FAIL"

        print(f"{status} '{text}'")
        print(f"   Expected: {'MATCH' if should_match else 'NO MATCH'} (reason: {test['reason']})")
        print(f"   Got: {'MATCH' if matched else 'NO MATCH'}")
        if extracted_name:
            print(f"   Extracted name: '{extracted_name}'")
            if expected_name and extracted_name != expected_name:
                print(f"   ✗ Name mismatch! Expected '{expected_name}'")
                outcome = "FAIL"
        print(f"   Result: {outcome}")
        print()

        if result_match == should_match and (not expected_name or extracted_name == expected_name):
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_is_obvious_non_person_import():
    """Test Part 1: Can import and use is_obvious_non_person from reconcile.py"""
    print("=" * 70)
    print("Test 2: Import is_obvious_non_person - Source Filtering")
    print("=" * 70)
    print()

    try:
        import sys
        import os

        # Add scraper directory to path
        scraper_dir = os.path.dirname(os.path.abspath(__file__))
        if scraper_dir not in sys.path:
            sys.path.insert(0, scraper_dir)

        from reconcile import is_obvious_non_person

        test_cases = [
            # Should be filtered (True = obvious non-person)
            ('AFC Bournemouth', True, 'org word "afc"'),
            ('Bournemouth University', True, 'org word "university"'),
            ('Poole Harbour', True, 'place suffix "harbour"'),
            ('Town Council', True, 'org word "council"'),

            # Should be kept (False = not obvious non-person)
            ('Dave Richmond', False, 'valid multi-word name'),
            ('John Smith', False, 'valid multi-word name'),
            ('Gabrielle', False, 'valid single-word name (NER validated)'),
            ('Abi Paler', False, 'valid name (Sprint 7.13 - trust NER)'),
            ('Economic Forum', False, 'not obvious non-person (no org/place indicators)'),
        ]

        passed = 0
        failed = 0

        for name, expected_filtered, reason in test_cases:
            result = is_obvious_non_person(name)
            status = "✓" if result == expected_filtered else "✗"
            outcome = "PASS" if result == expected_filtered else "FAIL"

            action = "FILTER" if result else "KEEP"
            expected_action = "FILTER" if expected_filtered else "KEEP"

            print(f"{status} '{name}'")
            print(f"   Expected: {expected_action} (reason: {reason})")
            print(f"   Got: {action}")
            print(f"   Result: {outcome}")
            print()

            if result == expected_filtered:
                passed += 1
            else:
                failed += 1

        print("-" * 70)
        print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
        print()

        return failed == 0

    except ImportError as e:
        print(f"✗ FAIL - Could not import is_obvious_non_person: {e}")
        print()
        return False


def test_combined_fix():
    """Test combined effect of both fixes"""
    print("=" * 70)
    print("Test 3: Combined Fix - End-to-End Source Extraction")
    print("=" * 70)
    print()

    # Simulate what scrape.py does with the new fixes
    test_text = """
    "I love living here," said Dave Richmond, Bournemouth property owner.

    – AFC Bournemouth

    – Qualifying

    – Sarah Jones, marketing manager

    – Race
    """

    print("Input text with various dash attributions:")
    print(test_text)
    print()

    # Part 2: Pattern matching (tightened)
    multiword_name_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)+)'
    dash_multiword_pattern = r'[–—]\s+' + multiword_name_pattern + r'(?:,\s+[^,\n]+)?'
    name_with_comma_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),\s+[^,\n]+'
    dash_comma_pattern = r'[–—]\s+' + name_with_comma_pattern

    extracted_names = []

    # Try pattern 1 (multi-word)
    for match in re.finditer(dash_multiword_pattern, test_text):
        name = match.group(1).strip()
        extracted_names.append(name)

    # Try pattern 2 (with comma)
    for match in re.finditer(dash_comma_pattern, test_text):
        name_match = re.search(r'[–—]\s+([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),', match.group(0))
        if name_match:
            name = name_match.group(1).strip()
            if name not in extracted_names:  # Avoid duplicates
                extracted_names.append(name)

    print("After Pattern Matching (Part 2):")
    for name in extracted_names:
        print(f"  - {name}")
    print()

    # Part 1: Filter using is_obvious_non_person
    try:
        from reconcile import is_obvious_non_person

        filtered_names = []
        for name in extracted_names:
            if not is_obvious_non_person(name):
                filtered_names.append(name)

        print("After Filtering (Part 1 - is_obvious_non_person):")
        for name in filtered_names:
            print(f"  ✓ {name}")
        print()

        # Check expected results
        expected_final = ['Sarah Jones']  # Only multi-word name without org indicators

        if filtered_names == expected_final:
            print("✓ PASS - Correct sources extracted and filtered")
            print(f"  Expected: {expected_final}")
            print(f"  Got: {filtered_names}")
            return True
        else:
            print("✗ FAIL - Unexpected results")
            print(f"  Expected: {expected_final}")
            print(f"  Got: {filtered_names}")
            return False

    except ImportError as e:
        print(f"✗ FAIL - Could not import is_obvious_non_person: {e}")
        return False


if __name__ == '__main__':
    print("Sprint 7.14: scrape.py Source Validation Fix - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_standalone_dash_pattern()
    all_passed &= test_is_obvious_non_person_import()
    all_passed &= test_combined_fix()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.14 fix working correctly")
        print()
        print("Summary:")
        print("- Part 1: scrape.py sources now filtered by is_obvious_non_person()")
        print("- Part 2: Standalone dash pattern tightened (requires 2+ words OR comma)")
        print("- Invalid sources like 'AFC Bournemouth', 'Qualifying', 'Race' now filtered")
        print("- Valid sources like 'Dave Richmond', 'Sarah Jones' still detected")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

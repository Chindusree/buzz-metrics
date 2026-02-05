#!/usr/bin/env python3
"""
Sprint 7.16.2: Test Non-Person Entity Descriptor Filtering

Problem: False positives "Anxious Generation" and "Dorset Mind" are leaking through
as sources because the pattern [Name], a [description] matches both people and entities.

Examples:
- "Anxious Generation, a book by Jonathan Haidt..." → Book (entity)
- "Dorset Mind, a local charity that..." → Charity (entity)
- "Sophia Lloyd, a Poole-based nutritionist who..." → Person (valid)

Root cause: We check IF the pattern matches but not WHAT the description describes.

Fix: Check for non-person entity descriptors at the START of the description.
Use startswith() to distinguish:
- "a charity that..." → Entity (reject)
- "a charity worker who..." → Person's role (accept)

Test cases:
✓ "Sophia Lloyd, a Poole-based nutritionist who..." → ACCEPT (person)
✓ "John Smith, a charity worker at..." → ACCEPT (person's role)
✗ "Dorset Mind, a local charity that..." → REJECT (entity)
✗ "Anxious Generation, a book by Jonathan Haidt..." → REJECT (entity)
✓ "Rebecca Brown, a researcher who..." → ACCEPT (person)
"""

import sys
import os

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

from scrape import is_valid_role_description


def test_entity_descriptors():
    """
    Test that entity descriptors (book, charity, etc) are rejected
    """
    print("=" * 70)
    print("Test 1: Entity Descriptor Filtering (Sprint 7.16.2)")
    print("=" * 70)
    print()

    test_cases = [
        # Should REJECT - entities, not people
        {
            'role_text': 'a book by Jonathan Haidt',
            'expected': False,
            'reason': 'Entity: book'
        },
        {
            'role_text': 'a local charity that challenges',
            'expected': False,
            'reason': 'Entity: local charity'
        },
        {
            'role_text': 'a charity that supports',
            'expected': False,
            'reason': 'Entity: charity'
        },
        {
            'role_text': 'an organization that provides',
            'expected': False,
            'reason': 'Entity: organization'
        },
        {
            'role_text': 'a company based in London',
            'expected': False,
            'reason': 'Entity: company'
        },
        {
            'role_text': 'a campaign to raise awareness',
            'expected': False,
            'reason': 'Entity: campaign'
        },
        {
            'role_text': 'a report published by',
            'expected': False,
            'reason': 'Entity: report'
        },
        {
            'role_text': 'a documentary exploring',
            'expected': False,
            'reason': 'Entity: documentary'
        },
        {
            'role_text': 'the book that examines',
            'expected': False,
            'reason': 'Entity: the book'
        },

        # Should ACCEPT - person roles (descriptor + role)
        {
            'role_text': 'a charity worker at Dorset Mind',
            'expected': True,
            'reason': 'Person: charity worker'
        },
        {
            'role_text': 'a book editor who',
            'expected': True,
            'reason': 'Person: book editor'
        },
        {
            'role_text': 'a company director based in',
            'expected': True,
            'reason': 'Person: company director'
        },
        {
            'role_text': 'a campaign manager for',
            'expected': True,
            'reason': 'Person: campaign manager'
        },
        {
            'role_text': 'a Poole-based nutritionist who',
            'expected': True,
            'reason': 'Person: nutritionist'
        },
        {
            'role_text': 'a researcher who specialises in',
            'expected': True,
            'reason': 'Person: researcher'
        },
    ]

    passed = 0
    failed = 0

    print(f"{'Role Text':<45} {'Expected':<10} {'Result':<10} {'Status':<10}")
    print("-" * 85)

    for test in test_cases:
        role_text = test['role_text']
        expected = test['expected']
        reason = test['reason']

        result = is_valid_role_description(role_text)

        expected_str = "ACCEPT" if expected else "REJECT"
        result_str = "ACCEPT" if result else "REJECT"

        if result == expected:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        # Truncate role_text if too long
        display_text = role_text if len(role_text) <= 43 else role_text[:40] + "..."

        print(f"{display_text:<45} {expected_str:<10} {result_str:<10} {status:<10}")
        print(f"  → {reason}")

    print()
    print("-" * 85)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_problem_cases_from_brief():
    """
    Test the specific problem cases mentioned in Sprint 7.16.2 brief
    """
    print("=" * 70)
    print("Test 2: Problem Cases from Brief")
    print("=" * 70)
    print()

    problem_cases = [
        {
            'name': 'Anxious Generation',
            'role_text': 'a book by Jonathan Haidt',
            'expected': False,
            'before': 'LEAKED (false positive)',
            'after': 'FILTERED (entity descriptor)'
        },
        {
            'name': 'Dorset Mind',
            'role_text': 'a local charity that',
            'expected': False,
            'before': 'LEAKED (false positive)',
            'after': 'FILTERED (entity descriptor)'
        },
        {
            'name': 'Sophia Lloyd',
            'role_text': 'a Poole-based nutritionist who',
            'expected': True,
            'before': 'ACCEPTED',
            'after': 'ACCEPTED (person role)'
        },
        {
            'name': 'John Smith',
            'role_text': 'a charity worker at',
            'expected': True,
            'before': 'ACCEPTED',
            'after': 'ACCEPTED (person role)'
        },
        {
            'name': 'Rebecca Brown',
            'role_text': 'a researcher who',
            'expected': True,
            'before': 'ACCEPTED',
            'after': 'ACCEPTED (person role)'
        },
    ]

    all_passed = True

    for case in problem_cases:
        name = case['name']
        role_text = case['role_text']
        expected = case['expected']
        before = case['before']
        after = case['after']

        result = is_valid_role_description(role_text)

        expected_str = "ACCEPT" if expected else "REJECT"
        result_str = "ACCEPT" if result else "REJECT"

        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False

        print(f"Name: {name}")
        print(f"  Role text: \"{role_text}\"")
        print(f"  BEFORE Sprint 7.16.2: {before}")
        print(f"  AFTER Sprint 7.16.2: {after}")
        print(f"  Expected: {expected_str}, Got: {result_str} - {status}")
        print()

    return all_passed


def test_startswith_vs_contains():
    """
    Test that startswith() correctly distinguishes entities from person roles
    """
    print("=" * 70)
    print("Test 3: startswith() vs contains() - Critical Distinction")
    print("=" * 70)
    print()

    print("Why startswith() is critical:")
    print("- 'a charity that...' → Entity (reject)")
    print("- 'a charity worker who...' → Person (accept)")
    print()

    test_cases = [
        {
            'role_text': 'a charity that supports',
            'expected': False,
            'reason': 'Starts with "a charity" → entity'
        },
        {
            'role_text': 'a charity worker who helps',
            'expected': True,
            'reason': 'Starts with "a charity worker" → person role'
        },
        {
            'role_text': 'a book published in 2024',
            'expected': False,
            'reason': 'Starts with "a book" → entity'
        },
        {
            'role_text': 'a book editor at Penguin',
            'expected': True,
            'reason': 'Starts with "a book editor" → person role'
        },
        {
            'role_text': 'a company that operates',
            'expected': False,
            'reason': 'Starts with "a company" → entity'
        },
        {
            'role_text': 'a company director based in',
            'expected': True,
            'reason': 'Starts with "a company director" → person role'
        },
    ]

    all_passed = True

    for test in test_cases:
        role_text = test['role_text']
        expected = test['expected']
        reason = test['reason']

        result = is_valid_role_description(role_text)

        expected_str = "ACCEPT" if expected else "REJECT"
        result_str = "ACCEPT" if result else "REJECT"

        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False

        print(f"Role text: \"{role_text}\"")
        print(f"  Expected: {expected_str}, Got: {result_str} - {status}")
        print(f"  → {reason}")
        print()

    return all_passed


def test_regression_valid_roles():
    """
    Test that previously valid roles still work (no regression)
    """
    print("=" * 70)
    print("Test 4: Regression Check - Valid Roles Still Work")
    print("=" * 70)
    print()

    valid_roles = [
        ('a Poole-based nutritionist who', 'Sprint 7.16: nutritionist'),
        ('also known as The Food Educator,', 'Sprint 7.16: alias'),
        ('marketing manager at BU', 'Sprint 7.12: manager'),
        ('a registered nutritionist based in', 'Sprint 7.16: registered nutritionist'),
        ('an educator specialising in', 'Sprint 7.16: educator'),
        ('a student at the university', 'Sprint 7.12: student'),
        ('director of public health at', 'Sprint 7.12: director'),
    ]

    passed = 0
    failed = 0

    for role_text, sprint in valid_roles:
        result = is_valid_role_description(role_text)

        if result:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL (REGRESSION)"
            failed += 1

        display_text = role_text if len(role_text) <= 40 else role_text[:37] + "..."
        print(f"{display_text:<40} {status:<20} ({sprint})")

    print()
    print(f"SUMMARY: {passed}/{len(valid_roles)} valid roles still work")
    print()

    return failed == 0


if __name__ == '__main__':
    print("Sprint 7.16.2: Non-Person Entity Descriptor Filtering - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_entity_descriptors()
    all_passed &= test_problem_cases_from_brief()
    all_passed &= test_startswith_vs_contains()
    all_passed &= test_regression_valid_roles()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.16.2 entity filtering working")
        print()
        print("Summary:")
        print("- Entity descriptors (book/charity/org) now rejected via startswith()")
        print("- Person roles (charity worker, book editor) still accepted")
        print("- 'Anxious Generation' and 'Dorset Mind' should now be filtered")
        print("- No regressions on previously valid roles")
        print()
        print("Next step: Run full pipeline to verify:")
        print("  cd ~/buzz-metrics/scraper")
        print("  python3 scrape.py && python3 verify.py && python3 compare.py")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

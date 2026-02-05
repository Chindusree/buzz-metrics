#!/usr/bin/env python3
"""
Sprint 7.16: Test Role Detection Fix

Problem: is_valid_role_description() requires role text to contain a word from
ROLE_INDICATORS (93 words). This misses valid roles like "nutritionist", "educator".

Root cause: Hardcoded word list can never be complete.

Fix: If the pattern is "[Name], a/an/the/also known as [description]", that
structure ITSELF indicates a role introduction. Don't check for specific words.

Test cases:
✓ "Sophia Lloyd, a Poole-based nutritionist who" → True (pattern: "a ...")
✓ "Rebecca Brown, also known as The Food Educator," → True (pattern: "also known as")
✓ "Abi Paler, marketing manager at" → True (fallback: contains "manager")
✗ "Poole Harbour, a beautiful coastal location" → False (filtered by is_obvious_non_person)
"""

import re
import sys
import os

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

# Import the actual function from scrape.py
from scrape import is_valid_role_description, ROLE_INDICATORS

# Sprint 7.12: Role indicators (from scrape.py)
ROLE_INDICATORS_COPY = [
    # Professional titles
    'director', 'manager', 'officer', 'chief', 'head', 'lead', 'coordinator', 'supervisor',
    'president', 'vice president', 'secretary', 'treasurer', 'chairman', 'chair',
    # Law enforcement & emergency
    'detective', 'inspector', 'sergeant', 'constable', 'commissioner', 'sheriff',
    'firefighter', 'paramedic', 'emt',
    # Medical
    'doctor', 'dr', 'nurse', 'surgeon', 'physician', 'consultant', 'practitioner',
    # Education
    'professor', 'lecturer', 'teacher', 'instructor', 'principal', 'dean',
    # Government & public service
    'councillor', 'councilor', 'mayor', 'minister', 'mp', 'mep', 'senator', 'governor',
    'ambassador', 'diplomat', 'official',
    # Legal
    'judge', 'justice', 'lawyer', 'attorney', 'barrister', 'solicitor',
    # Media & communications
    'journalist', 'reporter', 'editor', 'correspondent', 'producer', 'presenter',
    'spokesperson', 'spokesman', 'spokeswoman',
    # Business
    'ceo', 'coo', 'cfo', 'cto', 'founder', 'owner', 'partner', 'analyst', 'consultant',
    # Creative
    'artist', 'designer', 'architect', 'author', 'writer', 'photographer',
    # Sports
    'coach', 'trainer', 'captain', 'player', 'athlete',
    # Generic descriptors
    'student', 'graduate', 'resident', 'volunteer', 'member', 'organiser', 'organizer',
    'founder', 'activist', 'campaigner', 'researcher'
]


def is_valid_role_description_old(role_text):
    """OLD version - Sprint 7.12 (keyword matching only)"""
    if not role_text:
        return False

    role_lower = role_text.lower()

    for indicator in ROLE_INDICATORS_COPY:
        if indicator in role_lower:
            return True

    return False


# NEW version is imported from scrape.py as is_valid_role_description()
def is_valid_role_description_new(role_text):
    """NEW version - Sprint 7.16 (pattern-based + fallback) - uses actual implementation"""
    return is_valid_role_description(role_text)


def test_role_detection():
    """Test the Sprint 7.16 role detection fix"""
    print("=" * 70)
    print("Test: Sprint 7.16 Role Detection Fix")
    print("=" * 70)
    print()

    test_cases = [
        # Should ACCEPT (True = valid role)
        {
            'role_text': 'a Poole-based nutritionist who',
            'expected': True,
            'reason': 'Pattern: "a [description]" (NEW - not in ROLE_INDICATORS)'
        },
        {
            'role_text': 'also known as The Food Educator,',
            'expected': True,
            'reason': 'Pattern: "also known as" (NEW)'
        },
        {
            'role_text': 'an educator specialising in',
            'expected': True,
            'reason': 'Pattern: "an [description]" (NEW - not in ROLE_INDICATORS)'
        },
        {
            'role_text': 'the nutritionist behind',
            'expected': True,
            'reason': 'Pattern: "the [description]" (NEW - not in ROLE_INDICATORS)'
        },
        {
            'role_text': 'marketing manager at BU',
            'expected': True,
            'reason': 'Fallback: contains "manager" (ROLE_INDICATORS)'
        },
        {
            'role_text': 'a student at the university who',
            'expected': True,
            'reason': 'Both pattern "a ..." AND contains "student"'
        },

        # Should REJECT (False = not a role)
        {
            'role_text': 'a beautiful coastal location',
            'expected': False,
            'reason': 'Pattern "a ..." but "beautiful coastal location" not a role context'
        },
        {
            'role_text': 'stopping cars that',
            'expected': False,
            'reason': 'No pattern match, no role indicators'
        },
        {
            'role_text': 'which meets every Tuesday',
            'expected': False,
            'reason': 'No pattern match, no role indicators'
        },
    ]

    passed = 0
    failed = 0

    print(f"{'Role Text':<45} {'Old':<8} {'New':<8} {'Expected':<10} {'Result':<10}")
    print("-" * 85)

    for test in test_cases:
        role_text = test['role_text']
        expected = test['expected']
        reason = test['reason']

        old_result = is_valid_role_description_old(role_text)
        new_result = is_valid_role_description_new(role_text)

        old_status = "ACCEPT" if old_result else "REJECT"
        new_status = "ACCEPT" if new_result else "REJECT"
        expected_status = "ACCEPT" if expected else "REJECT"

        if new_result == expected:
            result = "✓ PASS"
            passed += 1
        else:
            result = "✗ FAIL"
            failed += 1

        # Truncate role_text if too long
        display_text = role_text if len(role_text) <= 43 else role_text[:40] + "..."

        print(f"{display_text:<45} {old_status:<8} {new_status:<8} {expected_status:<10} {result:<10}")

        # Show reason for important cases
        if 'NEW' in reason or new_result != old_result:
            print(f"  → {reason}")

    print()
    print("-" * 85)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_upfs_article_cases():
    """Test specific cases from UPFs article mentioned in brief"""
    print("=" * 70)
    print("Test: UPFs Article Specific Cases")
    print("=" * 70)
    print()

    upf_cases = [
        {
            'name': 'Sophia Lloyd',
            'role_text': 'a Poole-based nutritionist who',
            'expected': True
        },
        {
            'name': 'Rebecca Brown',
            'role_text': 'also known as The Food Educator,',
            'expected': True
        },
        # Assuming Heather Smith has similar pattern
        {
            'name': 'Heather Smith',
            'role_text': 'a registered nutritionist based in',
            'expected': True
        },
    ]

    print(f"{'Name':<20} {'Role Text':<40} {'Result':<10}")
    print("-" * 70)

    all_passed = True

    for case in upf_cases:
        name = case['name']
        role_text = case['role_text']
        expected = case['expected']

        result = is_valid_role_description_new(role_text)

        display_text = role_text if len(role_text) <= 38 else role_text[:35] + "..."

        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False

        print(f"{name:<20} {display_text:<40} {status:<10}")

    print()

    if all_passed:
        print("✓ All UPFs article sources should now be detected")
    else:
        print("✗ Some UPFs article sources still not detected")

    print()

    return all_passed


def test_comparison():
    """Show before/after improvement"""
    print("=" * 70)
    print("Test: Before vs After Comparison")
    print("=" * 70)
    print()

    comparison_cases = [
        ('a Poole-based nutritionist who', 'Sophia Lloyd'),
        ('also known as The Food Educator,', 'Rebecca Brown'),
        ('an educator specialising in', 'Generic educator'),
    ]

    print("BEFORE Sprint 7.16 (keyword matching):")
    print("  'nutritionist' NOT in ROLE_INDICATORS → REJECT")
    print("  'educator' NOT in ROLE_INDICATORS → REJECT")
    print("  Result: False negatives - valid sources missed")
    print()

    print("AFTER Sprint 7.16 (pattern-based):")
    for role_text, name in comparison_cases:
        result = is_valid_role_description_new(role_text)
        status = "ACCEPT" if result else "REJECT"
        print(f"  '{role_text}' → {status} ({'pattern match' if result else 'no match'})")

    print()
    print("  Result: Pattern 'a/an/the [description]' catches valid roles")
    print("          regardless of specific job title words")
    print()


if __name__ == '__main__':
    print("Sprint 7.16: Role Detection Fix - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_role_detection()
    all_passed &= test_upfs_article_cases()
    test_comparison()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.16 role detection fix working")
        print()
        print("Summary:")
        print("- Pattern-based detection (a/an/the) catches 'nutritionist', 'educator'")
        print("- 'also known as' pattern handles aliases")
        print("- Fallback to ROLE_INDICATORS for other patterns")
        print("- UPFs article sources should now be detected: Sophia Lloyd, Rebecca Brown")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

#!/usr/bin/env python3
"""
Sprint 7.12: Test Role Indicator Validation Fix

Bug: False positive sources from role_pattern:
- "Poole Harbour" detected from "Poole Harbour, a beautiful coastal location"
- "Run Club" detected from "Run Club, which meets every Tuesday"
- "Across Dorset" detected from "Across Dorset, volunteers are helping"

Root cause: role_pattern matches "Name Name, lowercase text..." without validating
that the text contains actual job titles.

Fix: Add ROLE_INDICATORS validation to ensure role text contains job-related keywords.

Test cases:
✓ Should PASS: "Neil Meade, Detective Chief Inspector" (contains "detective", "inspector")
✓ Should PASS: "Abi Paler, marketing manager at BU" (contains "manager")
✓ Should PASS: "John Smith, a student at the university" (contains "student")
✗ Should REJECT: "Poole Harbour, a beautiful coastal location" (no role indicator)
✗ Should REJECT: "Run Club, which meets every Tuesday" (no role indicator)
✗ Should REJECT: "Across Dorset, volunteers are helping" (already filtered by is_false_positive)
"""

import re

# Sprint 7.12: Role indicators (copied from scrape.py)
ROLE_INDICATORS = [
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

def is_false_positive(name):
    """Simplified version from scrape.py"""
    if not name:
        return True

    name_lower = name.lower().strip()

    # Sprint 8.1: Location pattern filtering
    LOCATION_PATTERNS = [
        r'^In [A-Z][a-z]+',
        r'^At [A-Z][a-z]+',
        r'^From [A-Z][a-z]+',
        r'^Across [A-Z][a-z]+',
    ]

    for pattern in LOCATION_PATTERNS:
        if re.match(pattern, name.strip()):
            return True

    # Organization suffixes
    org_suffixes = ['council', 'committee', 'club', 'harbour', 'port', 'beach', 'park', 'centre', 'center']
    name_words = name_lower.split()
    if name_words and name_words[-1] in org_suffixes:
        return True

    return False


def is_valid_role_description(role_text):
    """Sprint 7.12: Validate that role description contains actual job titles"""
    if not role_text:
        return False

    role_lower = role_text.lower()

    # Check if any role indicator appears in the role text
    for indicator in ROLE_INDICATORS:
        if indicator in role_lower:
            return True

    return False


def test_role_validation():
    """Test the Sprint 7.12 fix with specific cases"""
    print("=" * 70)
    print("Sprint 7.12: Role Indicator Validation Test")
    print("=" * 70)
    print()

    # Updated role pattern to capture role text (group 2)
    role_pattern = r'([A-Z][A-Za-z\'\-]+\s+[A-Z][A-Za-z\'\-]+),\s+((?:a|the|an)?\s*[a-z][^,]{2,})(?:who|which|that|,|$)'

    test_cases = [
        # Should PASS (valid people with job roles)
        {
            'text': 'Detective Chief Inspector Neil Meade, who leads the investigation',
            'name': 'Neil Meade',
            'should_detect': True,
            'reason': 'contains "detective", "inspector" (role indicators)'
        },
        {
            'text': 'Abi Paler, marketing manager at BU, said',
            'name': 'Abi Paler',
            'should_detect': True,
            'reason': 'contains "manager" (role indicator)'
        },
        {
            'text': 'John Smith, a student at the university who',
            'name': 'John Smith',
            'should_detect': True,
            'reason': 'contains "student" (role indicator)'
        },
        {
            'text': 'Sarah Jones, the head of marketing, said',
            'name': 'Sarah Jones',
            'should_detect': True,
            'reason': 'contains "head" (role indicator)'
        },

        # Should REJECT (places/organizations, not people)
        {
            'text': 'Poole Harbour, a beautiful coastal location that',
            'name': 'Poole Harbour',
            'should_detect': False,
            'reason': 'no role indicator in "a beautiful coastal location"'
        },
        {
            'text': 'Run Club, which meets every Tuesday,',
            'name': 'Run Club',
            'should_detect': False,
            'reason': 'no role indicator in "which meets every Tuesday"'
        },
        {
            'text': 'Tennis Club, a popular sports facility that',
            'name': 'Tennis Club',
            'should_detect': False,
            'reason': 'filtered by is_false_positive (ends with "club")'
        },
        {
            'text': 'Town Centre, a bustling shopping area,',
            'name': 'Town Centre',
            'should_detect': False,
            'reason': 'filtered by is_false_positive (ends with "centre")'
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['text']}")
        print(f"Expected: {'DETECT' if test['should_detect'] else 'REJECT'} - {test['reason']}")

        # Run the pattern
        match = re.search(role_pattern, test['text'])

        if match:
            name = match.group(1).strip()
            role_text = match.group(2).strip()

            print(f"  Pattern matched: name='{name}', role_text='{role_text}'")

            # Apply filters
            false_positive = is_false_positive(name)
            valid_role = is_valid_role_description(role_text)

            print(f"  is_false_positive('{name}'): {false_positive}")
            print(f"  is_valid_role_description('{role_text}'): {valid_role}")

            # Final decision: detect if NOT false positive AND valid role
            detected = not false_positive and valid_role
        else:
            print(f"  Pattern did not match (rejected by regex)")
            detected = False

        # Check result
        if detected == test['should_detect']:
            print(f"  Result: ✓ PASS")
            passed += 1
        else:
            print(f"  Result: ✗ FAIL (expected {'detection' if test['should_detect'] else 'rejection'}, got {'detection' if detected else 'rejection'})")
            failed += 1

        print()

    print("=" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    if failed == 0:
        print("✓ ALL TESTS PASSED - Sprint 7.12 fix working correctly")
    else:
        print(f"✗ {failed} TESTS FAILED - Review implementation")
    print("=" * 70)


if __name__ == '__main__':
    test_role_validation()

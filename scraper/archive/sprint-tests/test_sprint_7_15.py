#!/usr/bin/env python3
"""
Sprint 7.15: Test Intelligent Org/Person Detection using spaCy NER

Improvement: Replace hardcoded lists with NER-based detection + minimal fallback

Strategy:
1. spaCy NER says ORG/GPE/LOC → reject (organization/place)
2. spaCy NER says PERSON → accept
3. No NER label → check minimal fallback heuristics
4. Default → trust it (accept)

Test cases:
✓ "Economic Forum" → FILTER (fallback: ends with "forum")
✓ "India Council" → FILTER (NER: ORG)
✓ "Run Club" → FILTER (NER: ORG)
✓ "David Richmond" → ACCEPT (NER: PERSON)
✓ "Abi Paler" → ACCEPT (no flag, trusted)
✓ "Poole Harbour" → FILTER (fallback: ends with "harbour")
"""

import sys
import os

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

from reconcile import is_obvious_non_person, SPACY_AVAILABLE

# Also test NER directly
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    NER_AVAILABLE = True
except (ImportError, OSError):
    NER_AVAILABLE = False


def test_spacy_ner_labels():
    """Test spaCy NER to understand what labels it assigns"""
    print("=" * 70)
    print("Test 1: spaCy NER Label Analysis")
    print("=" * 70)
    print()

    if not NER_AVAILABLE:
        print("✗ spaCy not available - skipping NER label test")
        print()
        return False

    test_cases = [
        "Economic Forum",
        "India Council",
        "Run Club",
        "David Richmond",
        "Abi Paler",
        "Poole Harbour",
        "AFC Bournemouth",
        "Bournemouth University",
        "Town Council",
        "John Smith",
        "Sarah Jones",
    ]

    print(f"{'Name':<30} {'NER Labels':<40}")
    print("-" * 70)

    for name in test_cases:
        doc = nlp(name)
        labels = [(ent.text, ent.label_) for ent in doc.ents]
        labels_str = str(labels) if labels else "(no labels)"
        print(f"{name:<30} {labels_str:<40}")

    print()
    return True


def test_is_obvious_non_person():
    """Test the new NER-based is_obvious_non_person function"""
    print("=" * 70)
    print("Test 2: is_obvious_non_person() - NER-Based Detection")
    print("=" * 70)
    print()

    if not SPACY_AVAILABLE:
        print("⚠ WARNING: spaCy not available - using fallback heuristics only")
        print()

    test_cases = [
        # Should FILTER (True = obvious non-person)
        {
            'name': 'Economic Forum',
            'expected': True,
            'reason': 'fallback: ends with "forum"'
        },
        {
            'name': 'India Council',
            'expected': True,
            'reason': 'NER: ORG (if spaCy available)'
        },
        {
            'name': 'Run Club',
            'expected': True,
            'reason': 'NER: ORG (if spaCy available)'
        },
        {
            'name': 'Poole Harbour',
            'expected': True,
            'reason': 'fallback: ends with "harbour"'
        },
        {
            'name': 'AFC Bournemouth',
            'expected': True,
            'reason': 'NER: ORG'
        },
        {
            'name': 'Bournemouth University',
            'expected': True,
            'reason': 'NER: ORG'
        },
        {
            'name': 'Town Council',
            'expected': True,
            'reason': 'NER: ORG'
        },
        {
            'name': 'COVID',
            'expected': True,
            'reason': 'fallback: brand keyword "covid"'
        },

        # Should ACCEPT (False = not obvious non-person)
        {
            'name': 'David Richmond',
            'expected': False,
            'reason': 'NER: PERSON (if spaCy available)'
        },
        {
            'name': 'Abi Paler',
            'expected': False,
            'reason': 'no flag, trusted (default accept)'
        },
        {
            'name': 'John Smith',
            'expected': False,
            'reason': 'NER: PERSON'
        },
        {
            'name': 'Sarah Jones',
            'expected': False,
            'reason': 'NER: PERSON'
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        name = test['name']
        expected = test['expected']
        reason = test['reason']

        result = is_obvious_non_person(name)
        status = "✓" if result == expected else "✗"
        outcome = "PASS" if result == expected else "FAIL"

        action = "FILTER" if result else "ACCEPT"
        expected_action = "FILTER" if expected else "ACCEPT"

        print(f"{status} '{name}'")
        print(f"   Expected: {expected_action} (reason: {reason})")
        print(f"   Got: {action}")

        # Show what NER detected (if available)
        if NER_AVAILABLE:
            doc = nlp(name)
            if doc.ents:
                ner_info = ', '.join([f"{ent.text}:{ent.label_}" for ent in doc.ents])
                print(f"   NER detected: {ner_info}")
            else:
                print(f"   NER detected: (no entities)")

        print(f"   Result: {outcome}")
        print()

        if result == expected:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_comparison_old_vs_new():
    """Compare hardcoded list approach vs NER-based approach"""
    print("=" * 70)
    print("Test 3: Comparison - Hardcoded Lists vs NER-Based")
    print("=" * 70)
    print()

    if not SPACY_AVAILABLE:
        print("⚠ WARNING: spaCy not available - comparison limited")
        print()

    test_cases = [
        ('Economic Forum', 'Now filtered (fallback suffix)'),
        ('India Council', 'Now filtered (NER: ORG) - hardcoded list missed this'),
        ('Run Club', 'Now filtered (NER: ORG) - hardcoded list missed this'),
        ('Abi Paler', 'Still accepted (trust NER/default)'),
        ('David Richmond', 'Now accepted via NER: PERSON'),
    ]

    print(f"{'Name':<25} {'Old Approach':<30} {'New Approach':<30}")
    print("-" * 85)

    for name, note in test_cases:
        # Old approach: would require "Run" and "Council" in hardcoded org_words list
        # New approach: uses NER
        result = is_obvious_non_person(name)
        new_action = "FILTER" if result else "ACCEPT"

        # For old approach, approximate based on hardcoded lists
        # (this is just for comparison - old function is deprecated)
        old_would_filter = (
            name.lower().endswith(('harbour', 'park', 'centre', 'center', 'street', 'road', 'avenue', 'beach')) or
            'covid' in name.lower() or
            'lambrini' in name.lower()
        )
        old_action = "FILTER" if old_would_filter else "ACCEPT"

        print(f"{name:<25} {old_action:<30} {new_action:<30}")

    print()
    print("Key improvement: NER catches 'India Council' and 'Run Club' as ORG")
    print("                 without needing them in hardcoded lists")
    print()

    return True


def test_edge_cases():
    """Test edge cases and fallback behavior"""
    print("=" * 70)
    print("Test 4: Edge Cases - Fallback Behavior")
    print("=" * 70)
    print()

    test_cases = [
        # Empty/invalid
        ('', True, 'empty string'),
        ('A', True, 'single character (< 2 chars)'),

        # Ambiguous single-word names (Sprint 7.16.1: use gender-guesser)
        ('Smith', True, 'single last name (Sprint 7.16.1: unknown single word, filtered)'),
        ('John', False, 'single first name (Sprint 7.16.1: gender-guesser → male, kept)'),

        # Place suffixes
        ('Central Park', True, 'ends with "park"'),
        ('Main Street', True, 'ends with "street"'),
        ('Olympic Stadium', True, 'ends with "stadium"'),

        # Brand keywords
        ('COVID-19', True, 'contains "covid"'),
        ('Lambrini bottle', True, 'contains "lambrini"'),
    ]

    passed = 0
    failed = 0

    for name, expected, reason in test_cases:
        result = is_obvious_non_person(name)
        status = "✓" if result == expected else "✗"
        outcome = "PASS" if result == expected else "FAIL"

        action = "FILTER" if result else "ACCEPT"
        expected_action = "FILTER" if expected else "ACCEPT"

        print(f"{status} '{name}'")
        print(f"   Expected: {expected_action} (reason: {reason})")
        print(f"   Got: {action}")
        print(f"   Result: {outcome}")
        print()

        if result == expected:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


if __name__ == '__main__':
    print("Sprint 7.15: Intelligent Org/Person Detection - Test Suite")
    print()

    all_passed = True

    # Run tests
    test_spacy_ner_labels()
    all_passed &= test_is_obvious_non_person()
    test_comparison_old_vs_new()
    all_passed &= test_edge_cases()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.15 working correctly")
        print()
        print("Summary:")
        print("- NER-based detection replaces hardcoded org/place lists")
        print("- 'India Council' and 'Run Club' now detected as ORG via NER")
        print("- Minimal fallback for edge cases spaCy misses")
        print("- Default behavior: trust it (accept) if no flags")
        if SPACY_AVAILABLE:
            print("- spaCy NER: ✓ AVAILABLE")
        else:
            print("- spaCy NER: ✗ NOT AVAILABLE (using fallback only)")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

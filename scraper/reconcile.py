#!/usr/bin/env python3
"""
BUzz Metrics Reconciliation - Sprint 6.5.1
Intelligent source reconciliation using fuzzy matching.
Principle: scrape.py is primary. verify.py adds sources only when confident.
"""

import re
from rapidfuzz import fuzz
import gender_guesser.detector as gender

# Initialize gender detector
gd = gender.Detector()

# Pronouns to reject
PRONOUNS = {'he', 'she', 'they', 'it', 'we', 'i', 'you', 'his', 'her', 'their'}

# Prefixes to strip from names
PREFIXES = {'party', 'councillor', 'cllr', 'dr', 'mr', 'mrs', 'ms', 'prof',
            'sir', 'dame', 'lord', 'lady', 'captain', 'cpt', 'sgt', 'rev'}


def clean_name(name):
    """
    Remove garbage from name strings.
    Returns cleaned name or None if invalid.
    """
    if not name or not isinstance(name, str):
        return None

    # Remove newlines, extra spaces
    name = ' '.join(name.split())

    # Reject if contains digits or special chars
    if any(c.isdigit() for c in name):
        return None
    if any(c in name for c in ['@', '#', '/', '\\']):
        return None

    # Reject pronouns (check before stripping prefixes)
    if name.lower() in PRONOUNS:
        return None

    # Strip prefixes from each word
    words = name.split()
    words = [w for w in words if w.lower() not in PREFIXES]

    if not words:
        return None

    name = ' '.join(words)

    # Must have at least 2 characters
    if len(name) < 2:
        return None

    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', name):
        return None

    return name.strip()


def is_likely_person(name):
    """
    Validate if name is likely a person using gender-guesser.
    Returns True if name passes validation, False otherwise.
    """
    if not name:
        return False

    # Clean the name first
    cleaned = clean_name(name)
    if not cleaned:
        return False

    # Reject business-like names
    business_words = ['clothes', 'ltd', 'inc', 'shop', 'store', 'club', 'fc', 'afc']
    cleaned_lower = cleaned.lower()
    if any(bw in cleaned_lower for bw in business_words):
        return False

    # Filter out known brand names and common false positives
    brand_keywords = ['covid', 'lambrini', 'frosty jacks', 'jack daniels',
                      'guinness', 'yate', 'walton']
    for brand in brand_keywords:
        if brand in cleaned_lower:
            return False

    # Extract first name (first word that's capitalized)
    words = cleaned.split()
    first_name = None
    for word in words:
        if word and word[0].isupper():
            first_name = word
            break

    if not first_name:
        return False

    # Check with gender-guesser
    gender_result = gd.get_gender(first_name)

    # Accept: male, female, mostly_male, mostly_female, andy (androgynous)
    # Reject: unknown (not in database)
    if gender_result in ['male', 'female', 'mostly_male', 'mostly_female', 'andy']:
        return True

    return False


def names_match(name1, name2, threshold=85):
    """
    Check if two names match using fuzzy matching.
    Uses token_sort_ratio for flexibility with word order.
    Also handles partial matches (e.g., "Becca" matches "Becca Parker").
    Returns True if match score >= threshold.
    """
    if not name1 or not name2:
        return False

    # Clean both names
    clean1 = clean_name(name1)
    clean2 = clean_name(name2)

    if not clean1 or not clean2:
        return False

    # Normalize to lowercase for comparison
    clean1_lower = clean1.lower()
    clean2_lower = clean2.lower()

    # Exact match
    if clean1_lower == clean2_lower:
        return True

    # Substring match (one name contained in the other)
    # Example: "Becca" in "Becca Parker"
    if clean1_lower in clean2_lower or clean2_lower in clean1_lower:
        return True

    # Fuzzy match using token_sort_ratio (handles word order)
    score = fuzz.token_sort_ratio(clean1_lower, clean2_lower)

    return score >= threshold


def find_match_in_list(name, name_list, threshold=85):
    """
    Find if name matches any name in name_list.
    Returns the matching name from list, or None if no match.
    """
    for existing_name in name_list:
        if names_match(name, existing_name, threshold):
            return existing_name
    return None


def reconcile_sources(scrape_evidence, verify_evidence):
    """
    Reconcile sources from scrape.py and verify.py.

    Principle:
    - scrape.py is primary (pattern matching)
    - verify.py adds sources only when confident (not already in scrape)
    - verify.py sources must pass person validation

    Args:
        scrape_evidence: List of dicts with 'name' from scrape.py
        verify_evidence: List of dicts with 'name' from verify.py

    Returns:
        {
            'confirmed': [name, ...],  # From scrape.py (cleaned)
            'possible': [name, ...],   # New valid sources from verify.py
            'filtered': [name, ...]    # Rejected from verify.py (brands, places, etc.)
        }
    """
    result = {
        'confirmed': [],
        'possible': [],
        'filtered': []
    }

    # Step 1: Add all scrape sources to confirmed (these are primary)
    scrape_names = []
    for source in scrape_evidence:
        name = source.get('name')
        cleaned = clean_name(name)
        if cleaned and cleaned not in scrape_names:
            scrape_names.append(cleaned)

    result['confirmed'] = scrape_names

    # Step 2: Process verify sources
    for source in verify_evidence:
        name = source.get('name')
        cleaned = clean_name(name)

        if not cleaned:
            continue

        # Check if already in scrape (confirmed)
        match = find_match_in_list(cleaned, scrape_names)
        if match:
            # Already in confirmed, skip
            continue

        # Validate as person
        if is_likely_person(cleaned):
            # Valid person not in scrape - add to possible
            # Check not already in possible
            match_in_possible = find_match_in_list(cleaned, result['possible'])
            if not match_in_possible:
                result['possible'].append(cleaned)
        else:
            # Not a person - add to filtered
            # Check not already in filtered
            if cleaned not in result['filtered']:
                result['filtered'].append(cleaned)

    return result


if __name__ == "__main__":
    # Simple test
    print("Testing reconcile.py functions...")
    print()

    # Test 1: Name matching
    print("Test 1: Name matching")
    print(f"  'Becca Parker' vs 'Becca': {names_match('Becca Parker', 'Becca')}")
    print(f"  'Simon Bull' vs 'Party Councillor Simon Bull': {names_match('Simon Bull', 'Party Councillor Simon Bull')}")
    print(f"  'COVID' vs 'Becca': {names_match('COVID', 'Becca')}")
    print()

    # Test 2: Person validation
    print("Test 2: Person validation")
    print(f"  is_likely_person('Becca Parker'): {is_likely_person('Becca Parker')}")
    print(f"  is_likely_person('COVID'): {is_likely_person('COVID')}")
    print(f"  is_likely_person('Frosty Jacks'): {is_likely_person('Frosty Jacks')}")
    print(f"  is_likely_person('Lambrini'): {is_likely_person('Lambrini')}")
    print()

    # Test 3: Full reconciliation
    print("Test 3: Full reconciliation")
    scrape = [
        {'name': 'Wilmot'},
        {'name': 'Wilder'},
        {'name': 'Jeffs'}
    ]
    verify = [
        {'name': 'Wilmot'},
        {'name': 'Wilder'},
        {'name': 'Frosty Jacks'},
        {'name': 'Lambrini'},
        {'name': 'Jeffs'}
    ]
    result = reconcile_sources(scrape, verify)
    print(f"  Confirmed: {result['confirmed']}")
    print(f"  Possible: {result['possible']}")
    print(f"  Filtered: {result['filtered']}")
    print()

    print("reconcile.py ready for integration!")

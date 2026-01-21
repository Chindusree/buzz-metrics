#!/usr/bin/env python3
"""
BUzz Metrics Reconciliation - Sprint 6.5.1
Intelligent source reconciliation using fuzzy matching.
Principle: scrape.py is primary. verify.py adds sources only when confident.
"""

import re
from rapidfuzz import fuzz
import gender_guesser.detector as gender

# Sprint 7.15: Import spaCy for intelligent org/person detection
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False

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
    DEPRECATED: Sprint 7.13 - Use is_obvious_non_person() instead.

    This function is kept for backwards compatibility but should not be used
    for NER validation. It rejects names with unknown gender, causing false
    negatives like "Abi Paler".

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


def is_obvious_non_person(name):
    """
    Sprint 7.15: Intelligently detect non-persons using spaCy NER + minimal fallback.
    Sprint 7.16.1: Single-word name handling using gender-guesser as tiebreaker.

    Strategy:
    1. spaCy NER says ORG/GPE/LOC → reject (organization/place)
    2. spaCy NER says PERSON → accept
    3. Single-word names → use gender-guesser (NER unreliable)
    4. No NER label → check minimal fallback heuristics
    5. If nothing matches → trust it (default accept)

    This replaces hardcoded lists with intelligent NER-based detection, keeping
    only minimal fallbacks for cases spaCy misses.

    Args:
        name: Name string to validate

    Returns:
        True if this is obviously NOT a person (org/brand/place), False otherwise

    Examples:
        "Economic Forum" → True (fallback: ends with "forum")
        "India Council" → True (NER: ORG)
        "Run Club" → True (NER: ORG)
        "David Richmond" → False (NER: PERSON)
        "Abi Paler" → False (no flag, trusted)
        "Poole Harbour" → True (fallback: ends with "harbour")
        "Gabrielle" → False (Sprint 7.16.1: gender-guesser → female)
        "Becca" → False (Sprint 7.16.1: gender-guesser → female)
    """
    if not name or len(name.strip()) < 2:
        return True

    name_lower = name.lower().strip()

    # Step 1: Check known brands FIRST (before NER)
    # NER can misclassify brands like "COVID" as PERSON
    # Sprint 7.18.2: Added Studio Sal, Ralph Lauren, Big Give
    brands = ['covid', 'lambrini', 'frosty jacks', 'jack daniels', 'guinness',
              'studio sal', 'ralph lauren', 'big give']
    if any(brand in name_lower for brand in brands):
        return True

    # Sprint 7.18.2: Check for "Studio " prefix pattern
    if name.startswith('Studio '):
        return True

    # Step 1.5: Sprint 7.16.1 - Single-word name handling
    # spaCy NER misclassifies single-word names (Gabrielle → ORG, Becca → GPE)
    # Use gender-guesser as tiebreaker for these cases
    words = name.strip().split()
    if len(words) == 1:
        # Check brand blacklist first (brands that sound like names)
        single_word_blacklist = ['lambrini', 'covid', 'frosty', 'guinness']
        if name_lower in single_word_blacklist:
            return True

        # Use gender-guesser to check if it's a recognized first name
        gender_result = gd.get_gender(name)
        if gender_result in ['male', 'female', 'mostly_male', 'mostly_female', 'andy']:
            return False  # It's a known name, keep it

        # Unknown single word - filter it (likely org/brand abbreviation)
        return True

    # Step 2: Use spaCy NER if available
    if SPACY_AVAILABLE:
        try:
            doc = nlp(name)
            for ent in doc.ents:
                # ORG: organization (AFC Bournemouth, India Council, Run Club)
                # GPE: geopolitical entity (cities, countries)
                # LOC: location (Poole Harbour, Town Centre)
                if ent.label_ in ['ORG', 'GPE', 'LOC', 'FAC', 'EVENT']:
                    return True  # It's an organization/place/event
                if ent.label_ == 'PERSON':
                    return False  # It's a person (trust NER)
        except Exception:
            # If NER fails, fall through to fallback heuristics
            pass

    # Step 3: Minimal fallback for cases spaCy misses
    # Common org/place suffixes that spaCy sometimes misses
    non_person_suffixes = ['forum', 'harbour', 'harbor', 'centre', 'center',
                           'park', 'street', 'road', 'avenue', 'building',
                           'stadium', 'beach']
    last_word = name_lower.split()[-1] if name_lower.split() else ''
    if last_word in non_person_suffixes:
        return True

    # Step 4: Default - trust it
    # If NER didn't flag it as org/place AND not in fallback list → probably a person
    return False


def get_gender(name):
    """
    Get gender for a name using gender-guesser.
    Sprint 6.7.2: Returns 'male', 'female', or 'unknown'.
    """
    if not name:
        return 'unknown'

    # Extract first name (first word)
    first_name = name.split()[0]

    result = gd.get_gender(first_name)

    # Map to simplified categories
    if result in ['male', 'mostly_male']:
        return 'male'
    elif result in ['female', 'mostly_female']:
        return 'female'

    return 'unknown'


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

    Sprint 6.7.2: Now includes gender detection for all sources.
    Sprint 7.13: Trust NER - accept names even with unknown gender.
    Sprint 7.16: DEFINITIVE FIX - Trust both detection methods equally.

    NEW PHILOSOPHY (Sprint 7.16):
    - Both scrape.py (patterns) and verify.py (NER) are trusted EQUALLY
    - If EITHER finds a valid source, it's CONFIRMED
    - "Possible" is deprecated (no longer used)
    - "Filtered" is for obvious non-persons (orgs, places, brands)

    This fixes the fundamental issue where NER-detected sources like "Abi Paler"
    were demoted to "possible" instead of "confirmed".

    Args:
        scrape_evidence: List of dicts with 'name' from scrape.py
        verify_evidence: List of dicts with 'name' from verify.py

    Returns:
        {
            'confirmed': [{'name': str, 'gender': str}, ...],  # All valid sources (from either method)
            'possible': [],                                     # Deprecated (always empty)
            'filtered': [name, ...]                             # Rejected names (orgs/places/brands)
        }
    """
    result = {
        'confirmed': [],
        'possible': [],  # Deprecated - kept for backward compatibility
        'filtered': []
    }

    all_sources = []
    seen_names = set()

    # Step 1: Collect all sources from both methods
    # From scrape.py (pattern matching)
    for source in scrape_evidence:
        name = clean_name(source.get('name', ''))
        if name and name.lower() not in seen_names:
            all_sources.append({
                'name': name,
                'source': 'scrape',
                'position': source.get('position', '')  # Sprint 7.35: Preserve position
            })
            seen_names.add(name.lower())

    # From verify.py (NER)
    for source in verify_evidence:
        name = clean_name(source.get('name', ''))
        if not name:
            continue

        # Check if already added (use fuzzy matching to avoid duplicates)
        match = find_match_in_list(name, [s['name'] for s in all_sources])
        if not match:
            all_sources.append({
                'name': name,
                'source': 'verify',
                'position': ''  # Sprint 7.35: NER has no position
            })
            seen_names.add(name.lower())

    # Step 2: Validate each source - trust both methods equally
    for source in all_sources:
        name = source['name']

        # Sprint 7.15: Use NER-based validation
        if is_obvious_non_person(name):
            # Org/place/brand - filter it
            if name not in result['filtered']:
                result['filtered'].append(name)
        else:
            # Valid person - CONFIRM it (regardless of which method found it)
            # Check not already in confirmed (fuzzy match)
            confirmed_names = [s['name'] for s in result['confirmed']]
            match = find_match_in_list(name, confirmed_names)
            if not match:
                result['confirmed'].append({
                    'name': name,
                    'gender': get_gender(name),  # May be 'unknown', that's OK
                    'position': source.get('position', '')  # Sprint 7.35: Preserve position
                })

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

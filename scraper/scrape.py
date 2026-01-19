#!/usr/bin/env python3
"""
BUzz Metrics Scraper - Sprint 2
Scrapes front page and first page of category sections to extract article metadata.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import re
from datetime import datetime
from collections import defaultdict
import gender_guesser.detector as gender
import hashlib


BASE_URL = "https://buzz.bournemouth.ac.uk"


def normalize_quotes(text):
    """
    Sprint 8.1: Convert all quote variants to standard straight quotes.
    This prevents hardcoding of quote types in regex patterns.

    Args:
        text: Text containing various quote characters

    Returns:
        str: Text with normalized straight quotes
    """
    quote_chars = {
        '"': '"',  # left double quotation mark
        '"': '"',  # right double quotation mark
        '„': '"',  # double low-9 quotation mark
        '«': '"',  # left-pointing double angle quotation mark
        '»': '"',  # right-pointing double angle quotation mark
        ''': "'",  # left single quotation mark
        ''': "'",  # right single quotation mark
        '‚': "'",  # single low-9 quotation mark
        '‹': "'",  # single left-pointing angle quotation mark
        '›': "'",  # single right-pointing angle quotation mark
    }
    for fancy, standard in quote_chars.items():
        text = text.replace(fancy, standard)
    return text


# Pages to scrape - Sprint 7.3: Homepage only (source of truth)
PAGES = [
    BASE_URL
]

# Valid newsday date ranges (Mon-Fri only)
VALID_NEWSDAY_RANGES = [
    ("2026-01-12", "2026-01-16"),  # Week 1
    ("2026-01-19", "2026-01-23"),  # Week 2
    ("2026-01-26", "2026-01-30"),  # Week 3
]

# Category normalization map
CATEGORY_MAP = {
    # Sport
    "AFC Bournemouth": "Sport",
    "Men's Football": "Sport",
    "Local Football": "Sport",
    "Tennis": "Sport",
    "Boxing": "Sport",
    "Rugby Union": "Sport",
    "Rugby League": "Sport",
    "Cricket": "Sport",
    "Formula 1": "Sport",
    "Golf": "Sport",
    "Sport": "Sport",
    "Opinion & Analysis": "Sport",

    # News
    "News Top": "News",
    "Local": "News",
    "National": "News",
    "World": "News",
    "Bournemouth": "News",
    "Dorset": "News",
    "Poole": "News",
    "Campus": "News",

    # Features
    "New Features": "Features",
    "Lifestyle": "Features",
    "Health": "Features",
    "Entertainment": "Features",
    "Technology": "Features",
    "Sustainability": "Features",
    "Features": "Features",
    "Fashion": "Features",
    "1st News": "News",
}

# Stock photo indicators for Sprint 6.7 + Sprint 7.10 (Uncle Bob three-layer detection)
STOCK_PHOTO_INDICATORS = {
    'credit_keywords': [
        'pixabay', 'unsplash', 'pexels', 'shutterstock', 'getty', 'istock',
        'adobe stock', 'dreamstime', 'alamy', 'reuters', 'pa images', 'pa media',
        'ap photo', 'afp'
    ],
    'filename_patterns': [
        'pexels-', 'unsplash-', 'shutterstock', 'getty-', 'pixabay-', 'stock-', 'shutterstock_', 'istock'
    ],
    'alt_keywords': [
        'stock photo', 'stock image'
    ]
}

# Generic stock photo phrases - Sprint 6.7.2
GENERIC_STOCK_PHRASES = [
    'person on laptop', 'person on phone', 'person typing',
    'woman on laptop', 'man on laptop', 'hands typing',
    'office worker', 'business meeting', 'handshake',
    'stock photo', 'stock image'
]


# =============================================================================
# SPRINT 7.8: SHARED HELPER FUNCTIONS
# =============================================================================

def count_words(text):
    """
    Clean word counting on body text only.
    Excludes navigation, captions, and peripheral content.

    Args:
        text: Clean body text (already filtered)

    Returns:
        int: Word count
    """
    if not text:
        return 0
    words = text.split()
    return len(words)


def is_caption_text(text):
    """
    Detect if text is likely a photo caption (not body content).

    Args:
        text: Text string to check

    Returns:
        bool: True if likely a caption
    """
    if not text:
        return False

    text_lower = text.lower().strip()

    # Check for caption indicators
    caption_indicators = [
        'photo by', 'photo taken by', 'image by', 'photograph by',
        'credit:', 'credits:', 'source:', 'courtesy of',
        'picture by', 'pic by', 'getty', 'shutterstock',
        'unsplash', 'pexels', 'pixabay', 'reuters', 'pa images'
    ]

    if any(indicator in text_lower for indicator in caption_indicators):
        return True

    # Check length - captions are typically short
    word_count = len(text.split())
    if word_count < 5:
        return True

    return False


def clean_source_name(name):
    """
    Remove titles and prefixes from source names.

    Args:
        name: Full name string

    Returns:
        str: Cleaned name
    """
    if not name:
        return name

    # Titles to remove
    titles = [
        'councillor', 'cllr', 'dr', 'detective', 'chief', 'inspector',
        'sergeant', 'professor', 'mr', 'mrs', 'ms', 'miss', 'sir', 'dame',
        'rev', 'reverend', 'father', 'sister', 'brother'
    ]

    words = name.split()
    cleaned_words = []

    for word in words:
        if word.lower() not in titles:
            cleaned_words.append(word)

    return ' '.join(cleaned_words) if cleaned_words else name


# Sprint 7.12: Role indicators for validating job titles in role_pattern
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
    """
    Filter out false positive source names.

    Args:
        name: Name string to check

    Returns:
        bool: True if this is a false positive
    """
    if not name:
        return True

    name_lower = name.lower().strip()

    # Common false positives
    false_positives = [
        'the', 'this', 'that', 'they', 'there', 'these', 'those',
        'what', 'when', 'where', 'which', 'who', 'why', 'how',
        # Sprint 7.9.1: Add pronouns to filter out false positives
        'she', 'he', 'they', 'her', 'him', 'them', 'it', 'we', 'us', 'i', 'you',
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    ]

    if name_lower in false_positives:
        return True

    # Names that are too short (single letter)
    if len(name.strip()) < 2:
        return True

    # Names with only numbers
    if name.strip().isdigit():
        return True

    # Sprint 8.1: Location pattern filtering (not hardcoded - uses regex)
    LOCATION_PATTERNS = [
        r'^In [A-Z][a-z]+',     # "In Ringwood", "In Glasgow"
        r'^At [A-Z][a-z]+',     # "At Westminster"
        r'^From [A-Z][a-z]+',   # "From London"
        r'^Across [A-Z][a-z]+', # "Across Dorset"
    ]

    for pattern in LOCATION_PATTERNS:
        if re.match(pattern, name.strip()):
            return True

    # Sprint 7.9.3: Filter out non-person entities ("Dorset Council", "City Hall", etc.)
    # Sprint 7.12: Enhanced with more place/organization keywords
    org_suffixes = ['council', 'committee', 'department', 'bureau', 'agency', 'office',
                   'association', 'foundation', 'institute', 'organization', 'society',
                   'club', 'harbour', 'port', 'beach', 'park', 'centre', 'center']
    name_words = name_lower.split()
    if name_words and name_words[-1] in org_suffixes:
        return True

    return False


def is_valid_role_description(role_text):
    """
    Sprint 7.12: Validate that role description contains actual job titles.
    Sprint 7.16: Pattern-based detection instead of keyword matching.

    Strategy:
    1. If the structure is "a/an/the [description]", it's a role intro
    2. If structure is "also known as [description]", it's a role intro
    3. Fallback: check for role indicator words (for other patterns)

    The presence of "a/an/the" before a description signals this is
    introducing someone's role, regardless of specific job title words.

    Args:
        role_text: The text after the name in "Name Name, role text" pattern

    Returns:
        bool: True if role_text is a valid role description

    Examples:
        "a Poole-based nutritionist who" → True (pattern: "a [description]")
        "also known as The Food Educator," → True (pattern: "also known as")
        "marketing manager at BU" → True (fallback: contains "manager")
        "a beautiful coastal harbour" → False (no role context)
    """
    if not role_text:
        return False

    role_lower = role_text.lower().strip()

    # Sprint 7.16.2: Check for non-person entity descriptors at START of description
    # These indicate the text is describing an entity (book/charity/org), not a person
    # CRITICAL: Use pattern matching to distinguish:
    #   "a charity that..." → REJECT (entity)
    #   "a charity worker who..." → ACCEPT (person's role has job title after descriptor)
    # Strategy: Check if descriptor is followed by common entity continuations (that/which/who/by/etc)
    # rather than a job role word.
    NON_PERSON_DESCRIPTORS = [
        ('a book', ['by', 'that', 'which', 'about', 'on', 'exploring', 'examining', 'published']),
        ('a charity', ['that', 'which', 'supporting', 'helping', 'providing', 'based']),
        ('a local charity', ['that', 'which', 'supporting', 'helping', 'providing']),
        ('a national charity', ['that', 'which', 'supporting', 'helping', 'providing']),
        ('an organization', ['that', 'which', 'providing', 'supporting', 'based']),
        ('an organisation', ['that', 'which', 'providing', 'supporting', 'based']),
        ('a company', ['that', 'which', 'specialising', 'based', 'providing']),
        ('a foundation', ['that', 'which', 'supporting', 'dedicated']),
        ('a trust', ['that', 'which', 'supporting', 'managing']),
        ('a group', ['that', 'which', 'supporting', 'dedicated']),
        ('a campaign', ['that', 'which', 'to', 'for', 'aiming']),
        ('a movement', ['that', 'which', 'to', 'for', 'aiming']),
        ('a report', ['that', 'which', 'by', 'published', 'examining']),
        ('a study', ['that', 'which', 'by', 'published', 'examining']),
        ('a film', ['that', 'which', 'by', 'about', 'exploring']),
        ('a documentary', ['that', 'which', 'by', 'about', 'exploring']),
        ('a podcast', ['that', 'which', 'by', 'about', 'exploring']),
        ('a programme', ['that', 'which', 'exploring', 'examining']),
        ('a program', ['that', 'which', 'exploring', 'examining', 'to']),
        ('a project', ['that', 'which', 'to', 'aiming', 'designed']),
        ('a service', ['that', 'which', 'providing', 'offering']),
        ('an app', ['that', 'which', 'for', 'helping']),
        ('a website', ['that', 'which', 'for', 'providing']),
        ('a brand', ['that', 'which', 'known', 'specialising']),
        ('a product', ['that', 'which', 'designed', 'used']),
        ('a magazine', ['that', 'which', 'published', 'covering']),
        ('a newspaper', ['that', 'which', 'published', 'covering']),
        ('a journal', ['that', 'which', 'published', 'dedicated']),
        ('the book', ['that', 'which', 'examining', 'exploring']),
        ('the charity', ['that', 'which', 'supporting', 'providing']),
        ('the organization', ['that', 'which', 'providing', 'supporting']),
        ('the organisation', ['that', 'which', 'providing', 'supporting']),
        ('the company', ['that', 'which', 'specialising', 'based']),
        ('the foundation', ['that', 'which', 'supporting', 'dedicated']),
        ('the campaign', ['that', 'which', 'to', 'for', 'aiming']),
        ('the report', ['that', 'which', 'published', 'examining']),
    ]

    for descriptor, entity_continuations in NON_PERSON_DESCRIPTORS:
        if role_lower.startswith(descriptor + ' '):
            # Check what comes after the descriptor
            rest = role_lower[len(descriptor):].strip()
            # If it continues with entity patterns (that/which/by/etc), reject
            for continuation in entity_continuations:
                if rest.startswith(continuation):
                    return False

    # Sprint 7.16 defensive check: Reject obvious non-role descriptors
    # These words indicate the text is describing a place/thing, not a person's role
    # This handles edge cases like "Poole Harbour, a beautiful coastal location"
    # (though "Poole Harbour" would already be filtered by is_obvious_non_person)
    non_role_indicators = ['beautiful', 'coastal', 'location', 'place', 'area',
                           'building', 'venue', 'site', 'stopping', 'which meets']
    if any(indicator in role_lower for indicator in non_role_indicators):
        return False

    # Pattern 1: Starts with article (a/an/the) - role introduction pattern
    # "a Poole-based nutritionist", "an educator", "the marketing manager"
    if re.match(r'^(?:a|an|the)\s+\w', role_lower):
        return True

    # Pattern 2: "also known as" - alias/nickname introduction
    # "also known as The Food Educator"
    if 'also known as' in role_lower:
        return True

    # Pattern 3: Fallback - check for role indicator words (for other patterns)
    # "marketing manager at BU" (no article, but has "manager")
    for indicator in ROLE_INDICATORS:
        if indicator in role_lower:
            return True

    return False


def is_credit_text(text):
    """
    Identify if text contains image credit information.

    Args:
        text: Text to check

    Returns:
        bool: True if this is credit text
    """
    if not text:
        return False

    text_lower = text.lower()

    credit_keywords = [
        'photo by', 'photo taken by', 'image by', 'photograph by',
        'credit:', 'credits:', 'source:', '©', 'copyright',
        'courtesy of', 'picture by'
    ]

    return any(keyword in text_lower for keyword in credit_keywords)


# =============================================================================
# SPRINT 7.8: SOURCE EXTRACTION FUNCTIONS
# =============================================================================

def find_attribution_near(quote_elem):
    """
    Find attribution text near a structural quote element.

    Args:
        quote_elem: BeautifulSoup element (blockquote, etc.)

    Returns:
        str or None: Attribution text if found
    """
    if not quote_elem:
        return None

    # Check for figcaption or caption sibling
    next_sibling = quote_elem.find_next_sibling()
    if next_sibling and next_sibling.name in ['figcaption', 'cite', 'p']:
        text = next_sibling.get_text(strip=True)
        # Check if it looks like an attribution (short, has a name pattern)
        if len(text) < 100 and re.search(r'[A-Z][a-z]+', text):
            return text

    # Check parent for figcaption
    parent = quote_elem.parent
    if parent and parent.name == 'figure':
        caption = parent.find('figcaption')
        if caption:
            return caption.get_text(strip=True)

    return None


def extract_name_from_attribution(text):
    """
    Extract a person's name from attribution text.

    Args:
        text: Attribution text (e.g., "- John Smith" or "John Smith, CEO")

    Returns:
        str or None: Extracted name
    """
    if not text:
        return None

    # Remove leading dashes, em-dashes, etc.
    text = re.sub(r'^[-–—\s]+', '', text)

    # Pattern: Capture full name (2-4 words, capitalized)
    name_pattern = r'^([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){1,3})'
    match = re.search(name_pattern, text)

    if match:
        name = match.group(1).strip()
        # Clean and validate
        name = clean_source_name(name)
        if not is_false_positive(name):
            return name

    return None


def extract_structural_sources(soup):
    """
    Extract sources from structural quote elements (blockquotes, pull quotes).

    Sprint 7.8.1: Enhanced to handle inline attributions within blockquotes.

    Args:
        soup: BeautifulSoup object of article content

    Returns:
        list: List of source dicts with name, attribution, quote_snippet
    """
    sources = []

    if not soup:
        return sources

    # Find all blockquote elements
    blockquotes = soup.find_all('blockquote')

    for bq in blockquotes:
        quote_text = bq.get_text(strip=True)

        # Skip very short quotes
        if len(quote_text) < 10:
            continue

        # Skip if it's just an attribution line
        if len(quote_text.split()) < 5:
            continue

        # SPRINT 7.8.1: First check for CHILD attribution elements within the blockquote
        # Shorthand uses <footer><cite> for pull quote attributions
        cite_elem = bq.find('cite')
        footer_elem = bq.find('footer')

        attribution_name = None
        if cite_elem:
            attribution_name = cite_elem.get_text(strip=True)
        elif footer_elem:
            attribution_name = footer_elem.get_text(strip=True)

        if attribution_name:
            # Validate the name
            if not is_false_positive(attribution_name) and len(quote_text) >= 10:
                sources.append({
                    'name': attribution_name,
                    'full_attribution': f'blockquote cite: {attribution_name}',
                    'quote_snippet': quote_text[:50],
                    'position': 'blockquote-inline'
                })
                continue  # Found attribution, don't look elsewhere

        # If no inline attribution found, look for attribution near the blockquote
        attribution_text = find_attribution_near(bq)

        if attribution_text:
            name = extract_name_from_attribution(attribution_text)
            if name:
                sources.append({
                    'name': name,
                    'full_attribution': attribution_text[:50],
                    'quote_snippet': quote_text[:50],
                    'position': 'structural_blockquote'
                })

    return sources


def extract_sources(body_text, soup=None):
    """
    Unified source extraction combining structural and text-based patterns.

    This function extracts quoted sources from article content using:
    1. Structural patterns (blockquotes, pull quotes)
    2. Text-based patterns (inline quotes with attribution)

    Args:
        body_text: Clean body text (peripherals already removed)
        soup: Optional BeautifulSoup object for structural extraction

    Returns:
        list: Deduplicated list of source dicts with gender detection
    """
    sources = []

    # Step 1: Extract from structural elements if soup provided
    if soup:
        structural_sources = extract_structural_sources(soup)
        sources.extend(structural_sources)

    # Step 2: Extract from text patterns (using existing extract_quoted_sources logic)
    # This includes: quotes with attribution, role descriptions, lastname+verbs, blockquote patterns
    text_sources = extract_quoted_sources(body_text)
    sources.extend(text_sources)

    # Step 3: Deduplicate
    unique_sources = deduplicate_sources(sources)

    # Step 4: Add gender detection with context analysis
    # Sprint 8.2: Use context-aware gender detection for structural sources
    for source in unique_sources:
        if 'gender' not in source:
            gender_info = detect_gender_with_context(source['name'], body_text)
            source['gender'] = gender_info['gender']
            source['gender_confidence'] = gender_info['confidence']
            source['gender_method'] = gender_info['method']

    return unique_sources


def classify_image(img, article_body):
    """
    Classify an image as 'stock', 'original', or 'uncredited'.

    Sprint 6.7.2 improvements:
    - Detects uncredited images (no credit pattern found)
    - Better stock detection using generic description phrases

    Sprint 7.10 - Uncle Bob three-layer detection:
    Layer 1: Filename patterns (pexels-, unsplash-, etc.) - catches stock even if credit is garbage
    Layer 2: Sibling caption detection - extract_credit_from_context checks .image-caption spans
    Layer 3: Credit text keywords (Pexels, Unsplash, Getty, etc.) - classifies as stock

    Args:
        img: BeautifulSoup img tag
        article_body: Article body element for finding captions

    Returns:
        tuple: (classification, credit_text)
    """
    # Get all possible credit/caption sources
    credit_sources = []

    # Check img attributes
    alt_text = img.get('alt', '')
    credit_sources.append(alt_text)
    credit_sources.append(img.get('title', ''))
    credit_sources.append(img.get('data-caption', ''))

    # Check nearby figcaption
    parent = img.find_parent('figure')
    if parent:
        figcaption = parent.find('figcaption')
        if figcaption:
            credit_sources.append(figcaption.get_text(strip=True))

    # Check for caption div
    img_container = img.find_parent(['div', 'figure'])
    if img_container:
        caption_divs = img_container.find_all(['div', 'p'], class_=lambda x: x and ('caption' in str(x).lower() or 'credit' in str(x).lower()))
        for div in caption_divs:
            credit_sources.append(div.get_text(strip=True))

    # Combine all credit text
    credit_text = ' '.join(filter(None, credit_sources))
    credit_lower = credit_text.lower()

    # Check for stock photo indicators first
    # 1. Credit text contains stock source
    for keyword in STOCK_PHOTO_INDICATORS['credit_keywords']:
        if keyword in credit_lower:
            return ('stock', credit_text)

    # 2. Filename patterns
    src = img.get('src', '')
    src_lower = src.lower()
    for pattern in STOCK_PHOTO_INDICATORS['filename_patterns']:
        if pattern in src_lower:
            return ('stock', credit_text)

    # 3. Alt text contains stock keywords
    for keyword in STOCK_PHOTO_INDICATORS['alt_keywords']:
        if keyword in credit_lower:
            return ('stock', credit_text)

    # 4. Generic stock phrases in alt text (Sprint 6.7.2)
    alt_lower = alt_text.lower()
    for phrase in GENERIC_STOCK_PHRASES:
        if phrase in alt_lower:
            return ('stock', credit_text or 'No credit')

    # Check for proper credit attribution
    credit_patterns = ['photo:', 'photo by', 'credit:', 'by ', 'photograph:', 'image:', 'picture:']
    has_credit = any(p in credit_lower for p in credit_patterns)

    if has_credit:
        return ('original', credit_text)

    # No credit found - mark as uncredited
    return ('uncredited', credit_text if credit_text else 'No credit')


def extract_images(article_body):
    """
    Extract and classify all images from article body.

    Sprint 6.7.2: Now tracks three classifications: original, stock, uncredited

    Returns:
        dict: {
            'total': int,
            'original': int,
            'stock': int,
            'uncredited': int,
            'details': [{'src': str, 'classification': str, 'credit': str}, ...]
        }
    """
    if not article_body:
        return {
            'total': 0,
            'original': 0,
            'stock': 0,
            'uncredited': 0,
            'details': []
        }

    images = article_body.find_all('img')

    original_count = 0
    stock_count = 0
    uncredited_count = 0
    details = []

    for img in images:
        src = img.get('src', '')

        # Skip tiny images (likely icons, not content images)
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                if int(width) < 100 or int(height) < 100:
                    continue
            except:
                pass

        classification, credit = classify_image(img, article_body)

        if classification == 'original':
            original_count += 1
        elif classification == 'stock':
            stock_count += 1
        else:  # uncredited
            uncredited_count += 1

        details.append({
            'src': src,
            'classification': classification,
            'credit': credit if credit else 'No credit found'
        })

    return {
        'total': len(details),
        'original': original_count,
        'stock': stock_count,
        'uncredited': uncredited_count,
        'details': details
    }


# Sprint 8.2: Common ambiguous/unisex names that benefit from context analysis
AMBIGUOUS_NAMES = [
    'alex', 'jordan', 'taylor', 'morgan', 'casey', 'riley', 'jamie',
    'sam', 'chris', 'pat', 'robin', 'terry', 'lee', 'kim', 'abi', 'abby',
    'ashley', 'avery', 'bailey', 'cameron', 'charlie', 'drew', 'finley',
    'frankie', 'hayden', 'jesse', 'justice', 'kendall', 'logan', 'mackenzie',
    'parker', 'peyton', 'quinn', 'reese', 'sage', 'shawn', 'skyler', 'sydney'
]


def find_pronouns_near_name(text, name, window=200):
    """
    Sprint 8.2: Find gendered pronouns within window chars of name.

    Args:
        text: Full article text
        name: Person's name to search near
        window: Character window around name to search

    Returns:
        dict: {'female': count, 'male': count}
    """
    female_pronouns = ['she', 'her', 'herself', 'woman', 'female']
    male_pronouns = ['he', 'him', 'himself', 'man', 'male']

    pronoun_counts = {'female': 0, 'male': 0}

    # Find all occurrences of the name
    name_positions = []
    for match in re.finditer(re.escape(name), text, re.IGNORECASE):
        name_positions.append(match.start())

    if not name_positions:
        return pronoun_counts

    # For each name occurrence, search in surrounding window
    for pos in name_positions:
        start = max(0, pos - window)
        end = min(len(text), pos + len(name) + window)
        context = text[start:end].lower()

        # Count pronouns in this window
        for pronoun in female_pronouns:
            # Use word boundary to avoid matching substrings
            if re.search(r'\b' + pronoun + r'\b', context):
                pronoun_counts['female'] += 1

        for pronoun in male_pronouns:
            if re.search(r'\b' + pronoun + r'\b', context):
                pronoun_counts['male'] += 1

    return pronoun_counts


def detect_gender_with_context(full_name, surrounding_text):
    """
    Sprint 8.2: Detect gender using three-tier approach:
    1. First name lookup (gender-guesser)
    2. Pronoun context search if ambiguous
    3. Statistical fallback

    Args:
        full_name: Person's full name
        surrounding_text: Article text for context analysis

    Returns:
        dict: {
            'gender': 'male'|'female'|'unknown',
            'confidence': 'high'|'medium'|'low',
            'method': 'name_lookup'|'pronoun_context'|'statistical'
        }
    """
    d = gender.Detector()

    # Skip titles to get first name
    titles = ['councillor', 'cllr', 'dr', 'detective', 'chief', 'inspector',
              'sergeant', 'professor', 'mr', 'mrs', 'ms', 'miss', 'sir', 'dame']

    words = full_name.split()
    first_name = None
    for word in words:
        if word.lower() not in titles:
            first_name = word
            break

    if not first_name:
        return {'gender': 'unknown', 'confidence': 'low', 'method': 'none'}

    # Step 1: Check gender-guesser
    result = d.get_gender(first_name)

    # Sprint 8.2: Check if name is in ambiguous list - override gender-guesser
    # Some names like "Jordan" return 'male' but are culturally ambiguous
    is_ambiguous = first_name.lower() in AMBIGUOUS_NAMES

    # High confidence: Clear male/female (not mostly_*) AND not in ambiguous list
    if result == 'male' and not is_ambiguous:
        return {'gender': 'male', 'confidence': 'high', 'method': 'name_lookup'}
    elif result == 'female' and not is_ambiguous:
        return {'gender': 'female', 'confidence': 'high', 'method': 'name_lookup'}

    # Step 2: For ambiguous/mostly_* names, check pronoun context
    if result in ['mostly_male', 'mostly_female', 'andy', 'unknown'] or is_ambiguous:
        pronouns = find_pronouns_near_name(surrounding_text, full_name, window=200)

        # Found female pronouns only
        if pronouns['female'] > 0 and pronouns['male'] == 0:
            return {'gender': 'female', 'confidence': 'medium', 'method': 'pronoun_context'}

        # Found male pronouns only
        if pronouns['male'] > 0 and pronouns['female'] == 0:
            return {'gender': 'male', 'confidence': 'medium', 'method': 'pronoun_context'}

        # Mixed or no pronouns - fall through to Step 3

    # Step 3: Use mostly_* result as low confidence fallback
    if result == 'mostly_male':
        return {'gender': 'male', 'confidence': 'low', 'method': 'statistical'}
    elif result == 'mostly_female':
        return {'gender': 'female', 'confidence': 'low', 'method': 'statistical'}

    # Unknown
    return {'gender': 'unknown', 'confidence': 'low', 'method': 'none'}


def get_gender(full_name):
    """
    Extract first name and guess gender.
    Returns: 'male', 'female', or 'unknown'

    NOTE: This is the legacy function. New code should use detect_gender_with_context().
    """
    d = gender.Detector()

    # Skip titles
    titles = ['councillor', 'cllr', 'dr', 'detective', 'chief', 'inspector',
              'sergeant', 'professor', 'mr', 'mrs', 'ms', 'miss', 'sir', 'dame']

    words = full_name.split()

    # Find first word that's not a title
    first_name = None
    for word in words:
        if word.lower() not in titles:
            first_name = word
            break

    if not first_name:
        return 'unknown'

    result = d.get_gender(first_name)

    # Map gender-guesser results
    if result in ['male', 'mostly_male']:
        return 'male'
    elif result in ['female', 'mostly_female']:
        return 'female'
    else:
        return 'unknown'


def deduplicate_sources(sources):
    """
    Deduplicate sources by name.
    Prefer longer/more complete names. Merge names where one is a subset of another.
    """
    unique = []

    for source in sources:
        name = source['name']
        name_lower = name.lower().strip()

        # Check if this name is a duplicate or substring of an existing name
        merged = False
        for i, existing in enumerate(unique):
            existing_lower = existing['name'].lower().strip()

            # Exact match (case-insensitive)
            if existing_lower == name_lower:
                merged = True
                break
            # If new name contains existing (e.g., "Becca Parker" contains "Becca")
            elif existing_lower in name_lower and existing_lower != name_lower:
                # Replace with longer name
                unique[i] = source
                merged = True
                break
            # If existing contains new name (e.g., existing "Becca Parker", new "Becca")
            elif name_lower in existing_lower and existing_lower != name_lower:
                # Keep existing (longer) name
                merged = True
                break
            # Check surname match for different first names
            elif len(name.split()) > 1 and len(existing['name'].split()) > 1:
                surname = name.split()[-1].lower()
                existing_surname = existing['name'].split()[-1].lower()
                if surname == existing_surname:
                    # Same surname, prefer the one we have (keep first occurrence)
                    merged = True
                    break

        if not merged:
            unique.append(source)

    return unique


def resolve_full_name(partial_name, text):
    """
    Sprint 7.9.1: Resolve partial name (surname only) to full name.
    Searches backwards in text for "[FirstName] [Surname]" pattern.

    Args:
        partial_name: Surname only (e.g., "Brown")
        text: Full article text

    Returns:
        Full name if found (e.g., "Rebecca Brown"), otherwise original partial_name
    """
    # If already a full name (has space), return as-is
    if ' ' in partial_name.strip():
        return partial_name

    # Pattern: [FirstName] [Surname] where Surname matches partial_name
    # Look for capitalized first name followed by the partial name
    pattern = r'\b([A-Z][a-z]+)\s+' + re.escape(partial_name) + r'\b'

    matches = list(re.finditer(pattern, text))
    if matches:
        # Return the first occurrence (earliest in text)
        first_match = matches[0]
        full_name = first_match.group(0).strip()
        return full_name

    # No full name found, return original
    return partial_name


def extract_quoted_sources(text):
    """
    Returns list of sources with evidence and gender.
    Sprint 8.1: Now uses quote normalization to handle all quote types.
    """
    sources = []

    # Sprint 8.1: Normalize quotes first - this handles ALL quote types
    # No need to hardcode quote variants in regex
    text = normalize_quotes(text)

    # Step 1: Find all quotes with their positions
    # Sprint 8.1: Simplified pattern - only straight quotes after normalization
    quote_pattern = r'"([^\n"]+?)"'

    for match in re.finditer(quote_pattern, text):
        quote_text = match.group(1)
        quote_start = match.start()
        quote_end = match.end()

        # Skip very short quotes (likely not actual quotes)
        if len(quote_text) < 10:
            continue

        # Skip quotes that are just attribution (e.g., " Wilder said. ")
        attribution_words = ['said', 'says', 'explained', 'explains', 'added', 'adds',
                           'told', 'tells', 'noted', 'argued', 'claimed', 'commented',
                           'stated', 'remarked', 'announced', 'confirmed', 'revealed']
        quote_lower = quote_text.lower().strip()
        # If the quote is mostly just "Name said." or similar, skip it
        word_count_quote = len(quote_text.split())
        if word_count_quote < 5 and any(attr in quote_lower for attr in attribution_words):
            continue

        # Step 2: Get context (100 chars before and after)
        context_before = text[max(0, quote_start-100):quote_start]
        context_after = text[quote_end:min(len(text), quote_end+100)]

        # Step 3: Look for attribution AFTER quote
        # Pattern: [quote], said/says/etc [Capitalised Name]
        # Pattern: [quote]. [Capitalised Name] said/added/etc
        # Improved name pattern to capture full names (allows multiple words, hyphens, etc.)
        name_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3})'

        after_match = re.search(
            r'^[,.\s]*(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)\s+' + name_pattern,
            context_after
        )

        if not after_match:
            # Try reversed pattern: , [Name] said
            after_match = re.search(
                r'^[,.\s]*' + name_pattern + r'\s+(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)',
                context_after
            )

        # Step 4: Look for attribution BEFORE quote
        # Pattern: [Capitalised Name] said/says/etc: [quote]
        # Also handles: "quote," Name said. "quote2"
        # Also handles: Name, title/role, said: "quote"
        # Sprint 7.9.3: Made punctuation optional to handle "Name said that..." patterns
        before_match = re.search(
            name_pattern + r'(?:,\s+[^,]+?,)?\s+(?:said|says|explained|explains|added|adds|told|tells|noted|argued|claimed|commented|stated|remarked|announced|confirmed|revealed)[,:.]?\s*$',
            context_before
        )

        # Also check for "According to [Name]," pattern
        according_match = re.search(
            r'[Aa]ccording to\s+' + name_pattern + r'[,]?\s*$',
            context_before
        )

        # Sprint 8.1: Enhanced dash attribution pattern
        # Handles en-dash (–), em-dash (—), and hyphen (-) attribution
        # Pattern: "quote text. – Name, role/description"
        dash_match = None
        if not after_match and not before_match and not according_match:
            # Sprint 8.1: Support all dash types, not just en/em dash
            dash_pattern = r'^[,.\s]*[–—\-]\s*' + name_pattern + r'(?:,\s+[^,]+)?'
            dash_match = re.search(dash_pattern, context_after)

        # Step 5: Extract name and store evidence
        if after_match:
            name = after_match.group(1).strip()
            # Sprint 7.9.1: Resolve partial names to full names
            name = resolve_full_name(name, text)
            # Sprint 7.9.1: Filter out false positives (pronouns, etc.)
            if not is_false_positive(name):
                sources.append({
                    'name': name,
                    'full_attribution': context_after[:50].strip(),
                    'quote_snippet': quote_text[:50],
                    'position': 'after'
                })
        elif before_match:
            name = before_match.group(1).strip()
            # Sprint 7.9.1: Resolve partial names to full names
            name = resolve_full_name(name, text)
            # Sprint 7.9.1: Filter out false positives (pronouns, etc.)
            if not is_false_positive(name):
                sources.append({
                    'name': name,
                    'full_attribution': context_before[-50:].strip(),
                    'quote_snippet': quote_text[:50],
                    'position': 'before'
                })
        elif according_match:
            name = according_match.group(1).strip()
            # Sprint 7.9.1: Resolve partial names to full names
            name = resolve_full_name(name, text)
            # Sprint 7.9.1: Filter out false positives (pronouns, etc.)
            if not is_false_positive(name):
                sources.append({
                    'name': name,
                    'full_attribution': context_before[-50:].strip(),
                    'quote_snippet': quote_text[:50],
                    'position': 'before'
                })
        elif dash_match:
            # Sprint 7.9.3: Handle en-dash attribution
            name = dash_match.group(1).strip()
            name = resolve_full_name(name, text)
            if not is_false_positive(name):
                sources.append({
                    'name': name,
                    'full_attribution': context_after[:50].strip(),
                    'quote_snippet': quote_text[:50],
                    'position': 'dash_attribution'
                })

    # Step 5b: Look for full name with role/description (Shorthand pattern)
    # Pattern: "Sophia Lloyd, a Poole-based nutritionist who..."
    # Sprint 7.9.3: Updated to accept optional "a", "the", "an" before role description
    # Made the ending clause optional to handle "Name, manager of Company" patterns
    # Sprint 7.12: Enhanced to capture and validate role description text
    role_pattern = r'([A-Z][A-Za-z\'\-]+\s+[A-Z][A-Za-z\'\-]+),\s+((?:a|the|an)?\s*[a-z][^,]{2,})(?:who|which|that|,|$)'
    for match in re.finditer(role_pattern, text):
        name = match.group(1).strip()
        role_text = match.group(2).strip()

        # Sprint 7.12: Validate role description contains actual job titles
        # This prevents false positives like "Poole Harbour, a beautiful coastal location"
        if len(name) >= 5 and not is_false_positive(name) and is_valid_role_description(role_text):
            sources.append({
                'name': name,
                'full_attribution': match.group(0)[:50],
                'quote_snippet': '',
                'position': 'role_description'
            })

    # Step 5c: Look for last name + action verbs (journalism style)
    # Pattern: "Lloyd advises...", "Brown believes...", "Smith emphasises..."
    # This catches follow-up references after full name introduction
    lastname_verbs = ['advises', 'believes', 'emphasises', 'suggests', 'recommends',
                      'argues', 'maintains', 'insists', 'stresses', 'points out',
                      'notes', 'observes', 'warns', 'highlights', 'explains']

    # First extract all full names to build last name database
    full_names_found = set()
    for source in sources:
        if 'name' in source and ' ' in source['name']:
            full_names_found.add(source['name'])

    # Now look for last name references
    for verb in lastname_verbs:
        # Pattern: Lastname verb
        pattern = r'\b([A-Z][A-Za-z\'\-]+)\s+' + verb
        for match in re.finditer(pattern, text):
            lastname = match.group(1)
            # Check if this lastname matches any full name we found
            matching_full_name = None
            for full_name in full_names_found:
                if full_name.endswith(' ' + lastname):
                    matching_full_name = full_name
                    break

            if matching_full_name:
                # Add as the full name (will be deduplicated later)
                sources.append({
                    'name': matching_full_name,
                    'full_attribution': f'{lastname} {verb}',
                    'quote_snippet': '',
                    'position': f'lastname_{verb}'
                })

    # Step 5d: Look for standalone dash attribution
    # Sprint 8.1: Pattern to find "– Dave Richmond, Bournemouth property owner"
    # This catches blockquote attributions where quote and attribution are in same element
    # Format: [any text] [en-dash/em-dash/hyphen] [Name, role/description]
    # Note: Attribution can be mid-line or start of line, not just ^
    # Sprint 7.14: Tightened to require multi-word name OR comma after name
    # This prevents single words like "Qualifying" or "Race" from matching

    # Pattern 1: Multi-word name (2+ words) - with optional role after comma
    multiword_name_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)+)'
    dash_multiword_pattern = r'[–—]\s+' + multiword_name_pattern + r'(?:,\s+[^,\n]+)?'

    # Pattern 2: Single or multi-word name followed by comma and role (required)
    name_with_comma_pattern = r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),\s+[^,\n]+'

    # Try pattern 1 first (multi-word names)
    dash_matches = list(re.finditer(dash_multiword_pattern, text))
    for match in dash_matches:
        name = match.group(1).strip()
        if not is_false_positive(name):
            sources.append({
                'name': name,
                'full_attribution': match.group(0)[:50].strip(),
                'quote_snippet': '',
                'position': 'standalone_dash'
            })

    # Try pattern 2 (name with comma and role)
    dash_comma_pattern = r'[–—]\s+' + name_with_comma_pattern
    dash_comma_matches = list(re.finditer(dash_comma_pattern, text))
    for match in dash_comma_matches:
        # Extract just the name part (before comma)
        full_match = match.group(0)
        # Find the name before the comma
        name_match = re.search(r'[–—]\s+([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3}),', full_match)
        if name_match:
            name = name_match.group(1).strip()
            if not is_false_positive(name):
                sources.append({
                    'name': name,
                    'full_attribution': match.group(0)[:50].strip(),
                    'quote_snippet': '',
                    'position': 'standalone_dash'
                })

    # Step 5e: Look for blockquote patterns (Shorthand pull quotes)
    # Sprint 8.1: Updated to use straight quotes after normalization
    # Pattern 1: Blockquote followed by attribution name
    # Format: > "Quote text"
    #         > Name
    blockquote_pattern = r'>\s*"([^\n"]+?)"\s*>\s*([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3})'
    for match in re.finditer(blockquote_pattern, text):
        quote_text = match.group(1).strip()
        name = match.group(2).strip()
        if len(quote_text) >= 10:  # Skip short quotes
            sources.append({
                'name': name,
                'full_attribution': f'blockquote > {name}',
                'quote_snippet': quote_text[:50],
                'position': 'blockquote'
            })

    # Pattern 2: Blockquote with name on same line (inline attribution)
    # Format: "Quote" - Name  OR  "Quote" Name
    # Sprint 8.1: Updated to use straight quotes after normalization
    blockquote_inline = r'"([^\n"]+?)"\s*[-–—]?\s*([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,3})(?=\s*$|[\n\r])'
    for match in re.finditer(blockquote_inline, text, re.MULTILINE):
        quote_text = match.group(1).strip()
        name = match.group(2).strip()
        # Filter out common false positives
        if len(quote_text) >= 10 and name not in ['The', 'This', 'That', 'They', 'There']:
            sources.append({
                'name': name,
                'full_attribution': f'inline attribution - {name}',
                'quote_snippet': quote_text[:50],
                'position': 'blockquote-inline'
            })

    # Step 6: Deduplicate by normalized name
    unique_sources = deduplicate_sources(sources)

    # Step 7: Add gender detection with context analysis
    # Sprint 8.2: Use context-aware gender detection
    for source in unique_sources:
        gender_info = detect_gender_with_context(source['name'], text)
        source['gender'] = gender_info['gender']
        source['gender_confidence'] = gender_info['confidence']
        source['gender_method'] = gender_info['method']

    # Step 8: Sprint 7.14 - Filter obvious non-persons before returning
    # Previously, scrape.py sources bypassed validation and went straight to "confirmed"
    # Now apply the same validation used by verify.py
    try:
        # Import here to avoid circular dependency
        import sys
        import os
        # Add scraper directory to path
        scraper_dir = os.path.dirname(os.path.abspath(__file__))
        if scraper_dir not in sys.path:
            sys.path.insert(0, scraper_dir)

        from reconcile import is_obvious_non_person

        filtered_sources = []
        for source in unique_sources:
            name = source.get('name', '')
            if not is_obvious_non_person(name):
                filtered_sources.append(source)

        return filtered_sources
    except ImportError:
        # If reconcile.py not available, return unfiltered (backward compatibility)
        return unique_sources


def is_valid_newsday(date_str):
    """
    Check if article date falls within valid newsday ranges (Mon-Fri only).
    """
    if not date_str:
        return False

    try:
        article_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        for start_str, end_str in VALID_NEWSDAY_RANGES:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

            if start_date <= article_date <= end_date:
                return True

        return False
    except:
        return False


def is_placeholder_image(src):
    """Skip placeholder/base64 tiny images"""
    if not src:
        return True
    if 'data:image/gif;base64' in src:
        return True
    if 'data:image/svg+xml;base64' in src:
        return True
    if len(src) < 20:  # Too short to be real
        return True
    if 'placeholder' in src.lower():
        return True
    return False


def extract_image_credit_from_caption(caption_text):
    """Extract photographer name from caption"""
    if not caption_text:
        return None

    patterns = [
        r'Photo(?:\s+taken)?\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'Credits?:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'Image(?:\s+by)?:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'©\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, caption_text)
        if match:
            return match.group(1)

    return None


def extract_credit_from_context(elem):
    """
    Look for credit text near the image.
    Sprint 7.10: Added sibling .image-caption detection (Uncle Bob Layer 2).
    """
    if not elem:
        return ''

    # Check figcaption
    parent = elem.parent
    if parent and parent.name == 'figure':
        caption = parent.find('figcaption')
        if caption:
            return caption.get_text(strip=True)

    # Sprint 7.10: Check for sibling image-caption span (featured image pattern)
    if parent:
        for sibling in parent.next_siblings:
            if hasattr(sibling, 'get') and sibling.name in ['span', 'div']:
                sibling_classes = sibling.get('class', [])
                if 'image-caption' in sibling_classes:
                    return sibling.get_text(strip=True)

    # Check parent/siblings for caption text
    if parent:
        text = parent.get_text()
        # Look for "Photo by", "Photo taken by", "Credits", etc.
        credit_match = re.search(
            r'(?:Photo(?:\s+taken)?\s+by|Credits?:?|Image:?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            text
        )
        if credit_match:
            return credit_match.group(0)

    return ''


def count_shorthand_images(soup):
    """
    Count images in Shorthand pages comprehensively.
    Returns list of image dicts with src, credit, and classification.
    """
    images = []
    seen_srcs = set()  # Avoid duplicates

    # 1. Standard <img> tags
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src and src not in seen_srcs and not is_placeholder_image(src):
            seen_srcs.add(src)
            credit = extract_credit_from_context(img)
            images.append({
                'src': src,
                'credit': credit,
                'method': 'img_tag'
            })

    # 2. <figure> elements (may have <figcaption>)
    for fig in soup.find_all('figure'):
        img = fig.find('img')
        if img:
            src = img.get('src', '')
            if src and src not in seen_srcs and not is_placeholder_image(src):
                seen_srcs.add(src)
                caption = fig.find('figcaption')
                credit = caption.get_text(strip=True) if caption else ''
                images.append({
                    'src': src,
                    'credit': credit,
                    'method': 'figure'
                })

    # 3. Background images in style attributes
    for elem in soup.find_all(style=re.compile(r'background-image|background:\s*url')):
        style = elem.get('style', '')
        url_match = re.search(r'url\(["\']?([^"\')\s]+)["\']?\)', style)
        if url_match:
            src = url_match.group(1)
            if src not in seen_srcs and not is_placeholder_image(src):
                seen_srcs.add(src)
                images.append({
                    'src': src,
                    'credit': 'Background image',
                    'method': 'css_background'
                })

    # 4. Data attributes (Shorthand uses these)
    for elem in soup.find_all(attrs={'data-src': True}):
        src = elem.get('data-src')
        if src and src not in seen_srcs and not is_placeholder_image(src):
            seen_srcs.add(src)
            credit = extract_credit_from_context(elem)
            images.append({
                'src': src,
                'credit': credit,
                'method': 'data_src'
            })

    # Also check data-lazy-src
    for elem in soup.find_all(attrs={'data-lazy-src': True}):
        src = elem.get('data-lazy-src')
        if src and src not in seen_srcs and not is_placeholder_image(src):
            seen_srcs.add(src)
            credit = extract_credit_from_context(elem)
            images.append({
                'src': src,
                'credit': credit,
                'method': 'data_lazy_src'
            })

    return images


# =============================================================================
# SPRINT 7.8: CLEAN CONTENT EXTRACTION FUNCTIONS
# =============================================================================

def extract_wordpress_images(soup):
    """
    Extract and classify images from WordPress article body.

    Args:
        soup: BeautifulSoup object of article content

    Returns:
        dict: Image statistics and details
    """
    if not soup:
        return {
            'total': 0,
            'original': 0,
            'stock': 0,
            'uncredited': 0,
            'details': []
        }

    # Use existing extract_images function
    return extract_images(soup)


def extract_shorthand_images_clean(soup):
    """
    Extract and classify images from Shorthand content.

    Args:
        soup: BeautifulSoup object of Shorthand page

    Returns:
        dict: Image statistics and details
    """
    if not soup:
        return {
            'total': 0,
            'original': 0,
            'stock': 0,
            'uncredited': 0,
            'details': []
        }

    # Get raw image list from count_shorthand_images
    shorthand_images = count_shorthand_images(soup)

    original_count = 0
    stock_count = 0
    uncredited_count = 0
    details = []

    for img in shorthand_images:
        # Classify each Shorthand image
        credit = extract_image_credit_from_caption(img.get('credit', ''))
        classification = 'original' if credit else 'uncredited'

        if classification == 'original':
            original_count += 1
        elif classification == 'stock':
            stock_count += 1
        else:
            uncredited_count += 1

        details.append({
            'src': img['src'],
            'credit': credit if credit else 'No credit found',
            'classification': classification
        })

    return {
        'total': len(details),
        'original': original_count,
        'stock': stock_count,
        'uncredited': uncredited_count,
        'details': details
    }


def extract_wordpress_content(soup):
    """
    Extract clean body content from WordPress article.

    Removes peripheral content (navigation, captions, author boxes, etc.)
    and returns only the article body text.

    Args:
        soup: BeautifulSoup object of full article page

    Returns:
        dict: {
            'body_text': str,
            'word_count': int,
            'sources': list,
            'images': dict
        }
    """
    if not soup:
        return {
            'body_text': '',
            'word_count': 0,
            'sources': [],
            'images': {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []}
        }

    # Find article body container
    article_body = soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in str(x).lower() or 'entry' in str(x).lower()))

    if not article_body:
        return {
            'body_text': '',
            'word_count': 0,
            'sources': [],
            'images': {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []}
        }

    # Remove peripheral elements
    peripherals_to_remove = [
        'script', 'style', 'nav', 'footer', 'aside', 'header',
        # Author boxes
        {'name': 'div', 'class': lambda x: x and 'author' in str(x).lower()},
        # Related posts
        {'name': 'div', 'class': lambda x: x and 'related' in str(x).lower()},
        # Navigation
        {'name': 'div', 'class': lambda x: x and 'navigation' in str(x).lower()},
        # Comments
        {'name': 'div', 'id': lambda x: x and 'comment' in str(x).lower()},
        # Social sharing
        {'name': 'div', 'class': lambda x: x and 'share' in str(x).lower()},
        # Sidebars
        {'name': 'div', 'class': lambda x: x and 'sidebar' in str(x).lower()},
        # Captions (will extract separately)
        {'name': 'figcaption'},
    ]

    # Create a copy to work with
    article_copy = BeautifulSoup(str(article_body), 'lxml')

    # Remove peripherals
    for item in peripherals_to_remove:
        if isinstance(item, str):
            for tag in article_copy.find_all(item):
                tag.decompose()
        elif isinstance(item, dict):
            for tag in article_copy.find_all(**item):
                tag.decompose()

    # Extract clean body text from only content elements
    content_elements = article_copy.find_all(['p', 'h2', 'h3', 'h4', 'blockquote'])

    text_parts = []
    for elem in content_elements:
        text = elem.get_text(strip=True)

        # Skip caption text
        if is_caption_text(text):
            continue

        # Skip very short fragments
        if len(text.split()) < 3:
            continue

        text_parts.append(text)

    # Join for body text
    # Sprint 8.1: Use newlines to preserve line structure for pattern matching
    body_text = '\n'.join(text_parts)

    # Count words
    word_count = count_words(body_text)

    # Extract sources using unified function
    sources = extract_sources(body_text, article_body)

    # Extract images
    images = extract_wordpress_images(article_body)

    return {
        'body_text': body_text,
        'word_count': word_count,
        'sources': sources,
        'images': images
    }


def extract_shorthand_content_new(shorthand_url):
    """
    Extract clean body content from Shorthand article.

    Removes peripheral content (navigation, captions, credits, etc.)
    and returns only the article body text.

    Sprint 7.8: Refactored with clean architecture.

    Args:
        shorthand_url: URL of Shorthand page

    Returns:
        dict: {
            'body_text': str,
            'word_count': int,
            'author': str or None,
            'sources': list,
            'images': dict
        }
    """
    try:
        print(f"    Fetching Shorthand: {shorthand_url}")
        response = requests.get(shorthand_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract author from Shorthand byline
        author = None
        byline_patterns = [
            r'By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Words\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Written\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]

        # Look for byline in elements with relevant classes
        byline_elements = soup.find_all(['p', 'span', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['byline', 'author', 'credit', 'writer']))

        for elem in byline_elements:
            text = elem.get_text(strip=True)
            for pattern in byline_patterns:
                match = re.search(pattern, text)
                if match:
                    author = match.group(1).strip()
                    break
            if author:
                break

        # If not found in specific elements, check all text
        if not author:
            all_text = soup.get_text()
            for pattern in byline_patterns:
                match = re.search(pattern, all_text[:2000])
                if match:
                    author = match.group(1).strip()
                    break

        # Remove peripheral elements
        # SPRINT 7.8.1: Don't remove footer elements inside blockquotes (they contain cite attributions)
        peripherals_to_remove = ['nav', 'header']
        for tag_name in peripherals_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove footer elements that are NOT inside blockquotes
        for footer in soup.find_all('footer'):
            # Check if this footer is a child of a blockquote
            if not footer.find_parent('blockquote'):
                footer.decompose()

        # Remove social and credits sections
        for div in soup.find_all('div', class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['social', 'credit', 'share', 'navigation'])):
            div.decompose()

        # Extract text from content elements only
        content_tags = soup.find_all(['p', 'blockquote', 'h1', 'h2', 'h3'])

        text_parts = []
        for tag in content_tags:
            text = tag.get_text(strip=True)

            # Skip caption text
            if is_caption_text(text):
                continue

            # Skip UI elements
            text_lower = text.lower()
            skip_phrases = ['built with', 'click to', 'scroll to', 'shorthand']
            if any(phrase in text_lower for phrase in skip_phrases):
                continue

            # Skip very short fragments
            if len(text.split()) < 3:
                continue

            text_parts.append(text)

        # Join for body text
        body_text = ' '.join(text_parts)

        # Count words
        word_count = count_words(body_text)

        # Extract sources using unified function
        # For quote extraction, join paragraphs with newline to prevent cross-paragraph quotes
        text_for_quotes = '\n'.join(text_parts)
        sources = extract_sources(text_for_quotes, soup)

        # Extract images
        images = extract_shorthand_images_clean(soup)

        print(f"    Shorthand word count: {word_count}")
        if author:
            print(f"    Shorthand author: {author}")
        if images['total'] > 0:
            print(f"    Shorthand images found: {images['total']}")

        return {
            'body_text': body_text,
            'word_count': word_count,
            'author': author,
            'sources': sources,
            'images': images
        }

    except requests.RequestException as e:
        print(f"    Error fetching Shorthand page: {e}")
        return {
            'body_text': '',
            'word_count': 0,
            'author': None,
            'sources': [],
            'images': {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []}
        }
    except Exception as e:
        print(f"    Error parsing Shorthand content: {e}")
        return {
            'body_text': '',
            'word_count': 0,
            'author': None,
            'sources': [],
            'images': {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []}
        }


# =============================================================================
# OLD SHORTHAND FUNCTION (DEPRECATED - Sprint 7.8)
# Kept for backward compatibility during transition
# =============================================================================

def extract_shorthand_content(shorthand_url):
    """
    DEPRECATED: Use extract_shorthand_content_new() instead.

    Fetch and extract text content and author from a Shorthand embed page.
    Returns tuple: (cleaned_text, word_count, author) or (None, None, None) if extraction fails.
    Sprint 7.3: Now extracts byline from Shorthand pages.
    Sprint 7.6: Enhanced image counting for Shorthand pages.
    """
    try:
        print(f"    Fetching Shorthand: {shorthand_url}")
        response = requests.get(shorthand_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract author from Shorthand byline (Sprint 7.3)
        author = None
        byline_patterns = [
            r'By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "By Vishal Seenath"
            r'Words\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "Words by..."
            r'Written\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "Written by..."
        ]

        # Look for byline in elements with relevant classes
        byline_elements = soup.find_all(['p', 'span', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['byline', 'author', 'credit', 'writer']))

        for elem in byline_elements:
            text = elem.get_text(strip=True)
            for pattern in byline_patterns:
                match = re.search(pattern, text)
                if match:
                    author = match.group(1).strip()
                    break
            if author:
                break

        # If not found in specific elements, check all text
        if not author:
            all_text = soup.get_text()
            for pattern in byline_patterns:
                match = re.search(pattern, all_text[:2000])  # Check first 2000 chars
                if match:
                    author = match.group(1).strip()
                    break

        # Extract text from paragraphs, blockquotes, and headings
        content_tags = soup.find_all(['p', 'blockquote', 'h1', 'h2', 'h3'])

        text_parts = []
        for tag in content_tags:
            # Skip navigation, footer, and metadata
            parent_classes = []
            for parent in tag.parents:
                if parent.get('class'):
                    parent_classes.extend(parent.get('class'))

            # Skip if in nav/footer/header
            skip_classes = ['nav', 'navigation', 'footer', 'header', 'menu', 'metadata',
                          'caption', 'credit', 'credits']
            if any(skip_class in ' '.join(parent_classes).lower() for skip_class in skip_classes):
                continue

            text = tag.get_text(strip=True)

            # Skip if text contains photo credits or UI elements
            if text:
                text_lower = text.lower()
                skip_phrases = ['photo by', 'image by', 'unsplash', 'shorthand',
                              'built with', 'click to', 'scroll to']
                if any(phrase in text_lower for phrase in skip_phrases):
                    continue

                # Skip very short fragments (likely UI elements)
                word_count_fragment = len(text.split())
                if word_count_fragment < 5:
                    continue

                text_parts.append(text)

        # Join all text for word count, but preserve paragraph structure for quote extraction
        full_text = ' '.join(text_parts)
        words = full_text.split()
        word_count = len(words) if words else None

        # For quote extraction, join paragraphs with newline to prevent cross-paragraph quotes
        text_for_quotes = '\n'.join(text_parts)

        # Count images in Shorthand page (Sprint 7.6)
        shorthand_images = count_shorthand_images(soup)
        image_count = len(shorthand_images)

        print(f"    Shorthand word count: {word_count}")
        if author:
            print(f"    Shorthand author: {author}")
        if image_count > 0:
            print(f"    Shorthand images found: {image_count}")
        return (text_for_quotes, word_count, author, shorthand_images)

    except requests.RequestException as e:
        print(f"    Error fetching Shorthand page: {e}")
        return (None, None, None, [])
    except Exception as e:
        print(f"    Error parsing Shorthand content: {e}")
        return (None, None, None, [])


def scrape_page_for_articles(url):
    """
    Scrape a page and return article URLs.
    """
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        article_urls = []

        # Find article containers
        article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in str(x).lower() or 'article' in str(x).lower() or 'card' in str(x).lower()))

        for container in article_containers:
            # Look for headline link
            headline_elem = container.find(['h1', 'h2', 'h3', 'h4'])

            if headline_elem:
                link = headline_elem.find('a')
                if not link:
                    parent = headline_elem.find_parent('a')
                    if parent:
                        link = parent

                if link and link.get('href'):
                    full_url = urljoin(BASE_URL, link.get('href'))
                    # Only include article URLs
                    if '/20' in full_url and 'buzz.bournemouth.ac.uk' in full_url:
                        article_urls.append(full_url)

        print(f"  Found {len(article_urls)} articles")
        return article_urls

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []


def extract_article_metadata(url):
    """
    Fetch an article and extract metadata.
    Returns dict with article info or None.
    """
    try:
        time.sleep(0.5)  # Rate limiting

        print(f"  Extracting: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract headline
        headline_elem = soup.find('h1', class_=lambda x: x and 'title' in str(x).lower())
        if not headline_elem:
            headline_elem = soup.find('h1')
        headline = headline_elem.get_text(strip=True) if headline_elem else "Unknown"

        # Extract author from byline
        author = "Unknown"

        # First try to find author link in byline
        byline_container = soup.find('div', class_=lambda x: x and 'author' in str(x).lower())
        if byline_container:
            author_link = byline_container.find('a', href=re.compile(r'/author/'))
            if author_link:
                author_text = author_link.get_text(strip=True)
                # Remove "View all posts by" prefix if present
                author = re.sub(r'^View all posts by\s+', '', author_text, flags=re.IGNORECASE)

        # Try meta tag for JSON-LD schema
        if author == "Unknown":
            # Look for JSON-LD schema with author info
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        if isinstance(data['author'], dict) and 'name' in data['author']:
                            author = data['author']['name']
                            break
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and '@type' in item and item['@type'] == 'Person':
                                if 'name' in item:
                                    author = item['name']
                                    break
                except:
                    continue

        # Try searching for "by [Name]" pattern in visible text
        if author == "Unknown":
            byline_elem = soup.find(string=re.compile(r'\bby\s+[A-Z]', re.IGNORECASE))
            if byline_elem:
                # Make sure it's not in a script tag
                if byline_elem.find_parent('script') is None:
                    byline_text = byline_elem.strip()
                    match = re.search(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', byline_text)
                    if match:
                        author = match.group(1).strip()

        # Check if generic author
        generic_authors = ['editor green', 'editor', 'buzz', 'staff']
        if author.lower() in generic_authors:
            author = "Unknown"

        # Extract date and time from byline or meta
        article_date = None
        article_time = None

        # Try JSON-LD schema first (most reliable)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                date_published = None

                # Handle @graph structure (WordPress schema.org)
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if isinstance(item, dict) and 'datePublished' in item:
                            date_published = item['datePublished']
                            break
                elif isinstance(data, dict):
                    date_published = data.get('datePublished')
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'datePublished' in item:
                            date_published = item['datePublished']
                            break

                if date_published:
                    # Parse ISO 8601 format: "2026-01-16T14:30:00+00:00"
                    if 'T' in date_published:
                        date_part, time_part = date_published.split('T')
                        article_date = date_part  # "2026-01-16"
                        # Extract HH:MM from time_part (e.g., "14:30:00+00:00" -> "14:30")
                        article_time = time_part[:5]
                        break
                    else:
                        article_date = date_published
            except:
                continue

        # Fallback: Try to find date in <time> tag
        if not article_date:
            date_elem = soup.find('time')
            if date_elem:
                datetime_str = date_elem.get('datetime')
                if datetime_str:
                    try:
                        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        article_date = dt.strftime('%Y-%m-%d')
                        article_time = dt.strftime('%H:%M')
                    except:
                        pass

        # Fallback: search for date in text
        if not article_date:
            date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')
            date_match = date_pattern.search(soup.get_text())
            if date_match:
                date_str = date_match.group(0)
                # Parse date
                formats = ["%B %d, %Y", "%b %d, %Y"]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str.strip(), fmt)
                        article_date = dt.strftime('%Y-%m-%d')
                        break
                    except:
                        continue

        # Extract category from "Category:" line
        category = "Unknown"
        category_elem = soup.find(string=re.compile(r'Category:', re.IGNORECASE))
        if category_elem:
            # Find the next link after "Category:"
            parent = category_elem.find_parent()
            if parent:
                cat_link = parent.find_next('a')
                if cat_link:
                    category = cat_link.get_text(strip=True)

        # Fallback: look for category in URL
        if category == "Unknown":
            if '/category/' in url:
                cat_match = re.search(r'/category/([^/]+)/', url)
                if cat_match:
                    category = cat_match.group(1).replace('-', ' ').title()

        # ==========================================================
        # SPRINT 7.8: CLEAN ARCHITECTURE CONTENT EXTRACTION
        # ==========================================================

        # Detect Shorthand embed first
        content_type = "standard"
        word_count = None
        shorthand_url = None
        source_evidence = []
        images = {'total': 0, 'original': 0, 'stock': 0, 'uncredited': 0, 'details': []}

        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
        if iframe:
            content_type = "shorthand"
            # Extract Shorthand URL and fetch content
            shorthand_url = iframe.get('src')
            if shorthand_url:
                # Ensure it's a full URL
                if not shorthand_url.startswith('http'):
                    shorthand_url = 'https:' + shorthand_url if shorthand_url.startswith('//') else shorthand_url

                # Use new clean extraction function (Sprint 7.8)
                shorthand_data = extract_shorthand_content_new(shorthand_url)

                word_count = shorthand_data['word_count']
                source_evidence = shorthand_data['sources']
                images = shorthand_data['images']

                # Override author with Shorthand byline if found
                if shorthand_data['author']:
                    author = shorthand_data['author']
            else:
                print(f"    Warning: Shorthand iframe found but no src URL")
                word_count = None
        else:
            # Use new clean extraction function for WordPress (Sprint 7.8)
            wordpress_data = extract_wordpress_content(soup)

            word_count = wordpress_data['word_count']
            source_evidence = wordpress_data['sources']
            images = wordpress_data['images']

        # Map category to primary category
        category_primary = CATEGORY_MAP.get(category, "News")  # Default to "News"

        # Count sources by gender
        sources_male = sum(1 for s in source_evidence if s['gender'] == 'male')
        sources_female = sum(1 for s in source_evidence if s['gender'] == 'female')
        sources_unknown = sum(1 for s in source_evidence if s['gender'] == 'unknown')

        # Generate unique ID from URL
        article_id = hashlib.md5(url.encode()).hexdigest()[:12]

        # Calculate confidence scores
        author_confidence = "high" if author != "Unknown" and author.lower() not in ['editor', 'staff', 'buzz'] else "low"

        word_count_confidence = "high" if content_type == "standard" else "medium"

        # Quoted sources confidence
        if len(source_evidence) > 0:
            quoted_sources_confidence = "high"
        elif word_count and word_count < 300:
            quoted_sources_confidence = "medium"
        else:
            quoted_sources_confidence = "low"

        # Build warnings array
        warnings = []
        if author == "Unknown":
            warnings.append("Unknown author")
        if content_type == "shorthand":
            warnings.append("Shorthand word count may have ~20% inflation")
        if len(source_evidence) == 0 and word_count and word_count > 500:
            warnings.append("No quoted sources in article >500 words")

        return {
            'id': article_id,
            'headline': headline,
            'url': url,
            'author': author,
            'author_confidence': author_confidence,
            'date': article_date,
            'time': article_time,
            'category': category,
            'category_primary': category_primary,
            'word_count': word_count,
            'word_count_confidence': word_count_confidence,
            'content_type': content_type,
            'shorthand_url': shorthand_url,
            'quoted_sources': len(source_evidence),
            'quoted_sources_confidence': quoted_sources_confidence,
            'sources_male': sources_male,
            'sources_female': sources_female,
            'sources_unknown': sources_unknown,
            'source_evidence': source_evidence,
            'images': images,
            'warnings': warnings
        }

    except requests.RequestException as e:
        print(f"  Error extracting {url}: {e}")
        return None


def main():
    print("=" * 80)
    print("BUzz Metrics Scraper - Sprint 2")
    print("=" * 80)
    print()

    # Collect all article URLs from pages
    all_urls = set()

    for page_url in PAGES:
        urls = scrape_page_for_articles(page_url)
        all_urls.update(urls)

    print(f"\n{'-' * 80}")
    print(f"Total unique article URLs found: {len(all_urls)}")
    print(f"{'-' * 80}\n")

    # Extract metadata for each article
    articles = []
    for url in sorted(all_urls):
        metadata = extract_article_metadata(url)
        if metadata:
            # Filter by valid newsday dates
            if is_valid_newsday(metadata['date']):
                articles.append(metadata)

    print(f"\n{'-' * 80}")
    print(f"Successfully extracted: {len(articles)} articles (from valid newsdays)")
    print(f"{'-' * 80}\n")

    # Sort articles by date
    articles.sort(key=lambda x: (x['date'] if x['date'] else '', x['headline']))

    # Generate statistics
    by_day = defaultdict(int)
    by_category = defaultdict(int)
    by_category_primary = defaultdict(int)
    by_author = defaultdict(int)
    word_counts = []
    shorthand_count = 0
    shorthand_with_count = 0
    shorthand_without_count = 0
    standard_count = 0

    # Source statistics
    total_sources = 0
    total_male = 0
    total_female = 0
    total_unknown = 0
    source_distribution = defaultdict(int)
    articles_with_imbalance = []

    for article in articles:
        if article['date']:
            by_day[article['date']] += 1
        by_category[article['category']] += 1
        by_category_primary[article['category_primary']] += 1
        by_author[article['author']] += 1

        if article['content_type'] == 'shorthand':
            shorthand_count += 1
            if article['word_count']:
                shorthand_with_count += 1
                word_counts.append(article['word_count'])
            else:
                shorthand_without_count += 1
        else:
            standard_count += 1
            if article['word_count']:
                word_counts.append(article['word_count'])

        # Source statistics
        num_sources = article['quoted_sources']
        total_sources += num_sources
        total_male += article['sources_male']
        total_female += article['sources_female']
        total_unknown += article['sources_unknown']

        # Distribution: 0, 1, 2, 3+
        if num_sources >= 3:
            source_distribution['3+'] += 1
        else:
            source_distribution[num_sources] += 1

        # Gender imbalance: 3+ male, 0 female
        if article['sources_male'] >= 3 and article['sources_female'] == 0:
            articles_with_imbalance.append({
                'headline': article['headline'],
                'url': article['url'],
                'male': article['sources_male'],
                'female': article['sources_female']
            })

    # Save to JSON
    output = {
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_articles': len(articles),
        'articles': articles
    }

    output_path = '../data/metrics_raw.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 80)
    print("BUzz Scraper Summary - Week 1 (Jan 12-16, 2026)")
    print("=" * 80)
    print(f"\nTotal Articles: {len(articles)}")

    print("\nBy Day:")
    day_names = {
        '2026-01-12': 'Sun 12 Jan',
        '2026-01-13': 'Mon 13 Jan',
        '2026-01-14': 'Tue 14 Jan',
        '2026-01-15': 'Wed 15 Jan',
        '2026-01-16': 'Thu 16 Jan',
    }
    for date in sorted(by_day.keys()):
        day_name = day_names.get(date, date)
        print(f"  {day_name}: {by_day[date]}")

    print("\nBy Category (Primary):")
    for cat in sorted(by_category_primary.keys(), key=lambda x: by_category_primary[x], reverse=True):
        print(f"  {cat}: {by_category_primary[cat]}")

    print("\nBy Original Category:")
    for category in sorted(by_category.keys(), key=lambda x: by_category[x], reverse=True):
        print(f"  {category}: {by_category[category]}")

    print("\nTop Authors:")
    for author in sorted(by_author.keys(), key=lambda x: by_author[x], reverse=True)[:10]:
        print(f"  {author}: {by_author[author]}")

    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        print(f"\nAvg Word Count: {avg_words:.0f} (excluding Shorthand)")

    print(f"\nContent Types:")
    print(f"  Standard articles: {standard_count}")
    print(f"  Shorthand embeds: {shorthand_count}")
    print(f"    - With word count: {shorthand_with_count}")
    print(f"    - Without word count: {shorthand_without_count}")

    # Print source statistics
    print(f"\n{'=' * 80}")
    print("QUOTED SOURCE ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Sources: {total_sources}")
    print(f"Average per Article: {total_sources / len(articles):.1f}")

    print(f"\nSource Distribution:")
    # Sort keys, handling '3+' specially
    sorted_keys = sorted([k for k in source_distribution.keys() if k != '3+'])
    if '3+' in source_distribution:
        sorted_keys.append('3+')
    for count in sorted_keys:
        print(f"  {count} sources: {source_distribution[count]} articles")

    print(f"\nGender Breakdown:")
    print(f"  Male: {total_male} ({100*total_male/max(total_sources,1):.1f}%)")
    print(f"  Female: {total_female} ({100*total_female/max(total_sources,1):.1f}%)")
    print(f"  Unknown: {total_unknown} ({100*total_unknown/max(total_sources,1):.1f}%)")

    # Articles with gender imbalance
    if articles_with_imbalance:
        print(f"\nArticles with Gender Imbalance (3+ male, 0 female): {len(articles_with_imbalance)}")
        for article in articles_with_imbalance:
            print(f"  - {article['headline']}")
            print(f"    Male: {article['male']}, Female: {article['female']}")

    # Sample articles with full source evidence
    articles_with_sources = [a for a in articles if a['quoted_sources'] > 0]
    if articles_with_sources:
        print(f"\nSample Articles with Sources (first 5):")
        for i, article in enumerate(articles_with_sources[:5], 1):
            print(f"\n{i}. {article['headline']}")
            print(f"   URL: {article['url']}")
            print(f"   Sources: {article['quoted_sources']} (M:{article['sources_male']}, F:{article['sources_female']}, U:{article['sources_unknown']})")
            if article['source_evidence']:
                print(f"   Evidence:")
                for j, source in enumerate(article['source_evidence'][:3], 1):
                    print(f"     {j}. {source['name']} ({source['gender']})")
                    print(f"        Quote: \"{source['quote_snippet']}...\"")
                    print(f"        Attribution: {source['full_attribution']}")

    # Articles with 0 sources
    articles_no_sources = [a for a in articles if a['quoted_sources'] == 0]
    if articles_no_sources:
        print(f"\nArticles with 0 Sources ({len(articles_no_sources)}):")
        for article in articles_no_sources[:5]:
            print(f"  - {article['headline']}")
            print(f"    Category: {article['category_primary']}")

    print(f"\nData saved to {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

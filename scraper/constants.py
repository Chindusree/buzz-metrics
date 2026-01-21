"""
Sprint 7.35: Single source of truth for filtering rules.

All filtering constants live here. Import from this file only.
DO NOT duplicate these values elsewhere.
"""

# Positions that indicate a direct quote attribution
# These are the ONLY positions that count as confirmed sources
DIRECT_QUOTE_POSITIONS = {
    'after',              # "Quote," Name said
    'before',             # Name said, "Quote"
    'blockquote-inline',  # <blockquote> with attribution
    'lastname_verb',      # Smith said: "Quote"
    'standalone_dash',    # "Quote" — Name
}

# Known false positive names (organizations, places, brands)
FALSE_POSITIVE_NAMES = {
    'AFC Bournemouth',
    'Tottenham Hotspur',
    'Dorset Police',
    'Poole Harbour',
    'COVID',
    'Lambrini',
    'Dorset Mind',
    'Economic Forum',
}

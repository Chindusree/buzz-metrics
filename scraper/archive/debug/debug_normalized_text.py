#!/usr/bin/env python3
"""
Debug: Show text AFTER normalization (what Groq actually receives)
"""

import requests
from bs4 import BeautifulSoup
from scrape import extract_wordpress_content, normalize_quotes

url = "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/"

print("=" * 80)
print("TEXT AFTER NORMALIZATION (What Groq receives)")
print("=" * 80)

response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')

wordpress_data = extract_wordpress_content(soup)
body_text = wordpress_data['body_text']

# Normalize quotes (same as what Groq function does)
normalized_text = normalize_quotes(body_text)

print(f"\nNormalized text length: {len(normalized_text)} characters")

# Check for quote marks
straight_count = normalized_text.count('"')
print(f'Straight quotes ("): {straight_count} occurrences')

# Show all quoted text
import re
quotes = re.findall(r'"([^"]{10,})"', normalized_text)
if quotes:
    print(f"\nFound {len(quotes)} quotes:")
    for i, quote in enumerate(quotes, 1):
        print(f"\n  Quote {i}: {quote[:150]}...")

        # Find who said it
        quote_idx = normalized_text.find(quote)
        before_quote = normalized_text[max(0, quote_idx-150):quote_idx]
        after_quote = normalized_text[quote_idx+len(quote):quote_idx+len(quote)+100]

        # Look for names before quote
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:said|told|explained|stated|added)'
        before_matches = re.findall(name_pattern, before_quote)
        after_matches = re.findall(name_pattern, after_quote)

        if before_matches:
            print(f"  Attribution (before): {before_matches[-1]}")
        if after_matches:
            print(f"  Attribution (after): {after_matches[0]}")

        # Show context
        print(f"  Before quote: ...{before_quote[-80:]}")
        print(f"  After quote: {after_quote[:80]}...")
else:
    print("\nNo quotes found")

# Check for Grant Hancox quote
print("\n" + "=" * 80)
print("GRANT HANCOX QUOTE CHECK:")
print("=" * 80)

if 'Grant Hancox' in normalized_text:
    idx = normalized_text.find('Grant Hancox')
    context = normalized_text[idx:idx+500]
    print(context)
else:
    print("Grant Hancox not found")

# Check for Roan Fox
print("\n" + "=" * 80)
print("ROAN FOX CHECK:")
print("=" * 80)

if 'Roan Fox' in normalized_text:
    idx = normalized_text.find('Roan Fox')
    context = normalized_text[max(0, idx-100):idx+200]
    print(context)
else:
    print("Roan Fox not found")

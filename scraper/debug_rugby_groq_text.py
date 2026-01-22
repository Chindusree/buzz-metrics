#!/usr/bin/env python3
"""
Debug: Show exact text being sent to Groq for Rugby article
"""

import requests
from bs4 import BeautifulSoup
from scrape import extract_wordpress_content

url = "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/"

print("=" * 80)
print("DEBUGGING RUGBY ARTICLE - TEXT SENT TO GROQ")
print("=" * 80)

# Fetch the page
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')

# Use the same extraction method as scraper
wordpress_data = extract_wordpress_content(soup)

body_text = wordpress_data['body_text']

print(f"\nExtracted body text length: {len(body_text)} characters")
print(f"\n{'=' * 80}")
print("FULL TEXT BEING SENT TO GROQ:")
print('=' * 80)
print(body_text)
print('=' * 80)

# Check for specific names
print("\n" + "=" * 80)
print("NAME DETECTION:")
print("=" * 80)

names_to_check = ["Grant Hancox", "Roan Fox", "For me, it's to play"]

for name in names_to_check:
    if name in body_text:
        print(f"\n✓ FOUND: '{name}'")
        # Show context
        idx = body_text.find(name)
        context_start = max(0, idx - 100)
        context_end = min(len(body_text), idx + len(name) + 100)
        print(f"  Context: ...{body_text[context_start:context_end]}...")
    else:
        print(f"\n✗ NOT FOUND: '{name}'")

# Check for quote marks
print("\n" + "=" * 80)
print("QUOTE MARKS:")
print("=" * 80)
straight_count = body_text.count('"')
curly_count = body_text.count('"') + body_text.count('"')
print(f'Straight quotes ("): {straight_count} occurrences')
print(f'Curly quotes (""): {curly_count} occurrences')

# Show all quoted text
import re
quotes = re.findall(r'"([^"]{20,})"', body_text)
if quotes:
    print(f"\nFound {len(quotes)} quotes:")
    for i, quote in enumerate(quotes, 1):
        print(f"\n  Quote {i}: {quote[:100]}...")
else:
    print("\nNo quotes found with straight quotes")

# Check for "said" patterns
print("\n" + "=" * 80)
print("'SAID' PATTERNS:")
print("=" * 80)
said_pattern = re.findall(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) said[:\s]+"([^"]{20,})"', body_text)
if said_pattern:
    print(f"Found {len(said_pattern)} 'X said' patterns:")
    for name, quote in said_pattern:
        print(f"\n  {name} said: {quote[:80]}...")
else:
    print("No 'X said' patterns found")

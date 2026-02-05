#!/usr/bin/env python3
"""
Debug the Rugby Club article to see what Groq is detecting
"""

import requests
from bs4 import BeautifulSoup

url = "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-rugby-club-head-to-old-tiffinians/"

response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')

# Find article body
article = soup.find('article')
if article:
    text = article.get_text(strip=True)

    # Search for quotes
    import re

    print("Searching for quoted text in article...")
    print("=" * 80)

    # Look for patterns like "Name said" or quotes
    quote_patterns = [
        r'"([^"]{20,200})"[,.]?\s*(?:said|told|explained|added|stated)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|told|explained|added|stated)[:\s]+["\']([^"\']{20,200})',
    ]

    for pattern in quote_patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"\nPattern: {pattern}")
            for match in matches:
                print(f"  Match: {match}")

    # Search for specific names
    print("\n" + "=" * 80)
    print("Searching for specific names...")
    print("=" * 80)

    names_to_find = ["Grant Hancox", "Roan Fox", "Hancox", "Fox"]

    for name in names_to_find:
        if name.lower() in text.lower():
            # Find context around the name
            idx = text.lower().find(name.lower())
            context_start = max(0, idx - 100)
            context_end = min(len(text), idx + len(name) + 100)
            context = text[context_start:context_end]
            print(f"\nFound '{name}':")
            print(f"  Context: ...{context}...")
        else:
            print(f"\n'{name}' NOT FOUND in article")

    # Show first 1000 chars of article
    print("\n" + "=" * 80)
    print("First 1000 characters of article:")
    print("=" * 80)
    print(text[:1000])

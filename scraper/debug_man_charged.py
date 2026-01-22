#!/usr/bin/env python3
"""
Debug the Man charged article
"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/"

response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')

article = soup.find('article')
if article:
    text = article.get_text(strip=True)

    print("=" * 80)
    print("Searching for DCI Neil Meade quotes...")
    print("=" * 80)

    # Look for "Neil Meade" or "DCI Neil Meade" with quotes
    if "neil meade" in text.lower():
        idx = text.lower().find("neil meade")
        context_start = max(0, idx - 300)
        context_end = min(len(text), idx + 300)
        context = text[context_start:context_end]
        print(f"\nFound 'Neil Meade':")
        print(f"Context (600 chars):")
        print(context)
        print()

    # Look for quotes
    print("\n" + "=" * 80)
    print("All quotes in article:")
    print("=" * 80)

    # Find text in quotes (both straight and curly)
    quote_pattern = r'[""]([^""]{30,200})[""]'
    matches = re.findall(quote_pattern, text)

    if matches:
        for i, match in enumerate(matches, 1):
            print(f"\nQuote {i}: {match}")
            # Find who said it (look after quote)
            idx = text.find(match)
            after_quote = text[idx + len(match):idx + len(match) + 100]
            print(f"After quote: {after_quote[:80]}...")
    else:
        print("No quotes found")

    # Show first 1500 chars
    print("\n" + "=" * 80)
    print("First 1500 characters:")
    print("=" * 80)
    print(text[:1500])

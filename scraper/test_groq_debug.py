#!/usr/bin/env python3
"""
Debug Groq integration by showing what text is being analyzed
"""

import requests
from bs4 import BeautifulSoup

# Test with a known article that has quotes
test_url = "https://buzz.bournemouth.ac.uk/2026/01/dawson-shines-on-odi-return/"

print("Fetching article...")
response = requests.get(test_url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')

# Find article body
article_body = soup.find('article')
if article_body:
    # Get text
    text = article_body.get_text(strip=True)
    print(f"\nArticle text length: {len(text)} chars")
    print("\nFirst 500 chars:")
    print("-" * 80)
    print(text[:500])
    print("-" * 80)

    # Check for quotes
    has_straight_quotes = '"' in text
    has_curly_quotes = '"' in text or '"' in text

    print(f"\nHas straight quotes (\")? {has_straight_quotes}")
    print(f"Has curly quotes ("")? {has_curly_quotes}")

    if has_straight_quotes or has_curly_quotes:
        # Find quoted text
        print("\nSearching for quoted text...")
        import re
        # Find text in quotes
        quote_patterns = [
            r'"([^"]{20,})"',  # straight quotes
            r'"([^"]{20,})"',  # curly quotes
        ]

        for pattern in quote_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"\nFound {len(matches)} quotes with pattern {pattern}:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"  {i}. {match[:80]}...")
else:
    print("No article body found!")

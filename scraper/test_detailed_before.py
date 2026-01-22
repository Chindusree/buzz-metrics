#!/usr/bin/env python3
"""
Detailed test - check if "Three Poole" or similar issues exist
"""

from scrape import extract_article_metadata
import requests
from bs4 import BeautifulSoup

print("=" * 80)
print("DETAILED BEFORE TEST")
print("=" * 80)

# Test 1: Rapist sentenced
print("\n1. RAPIST SENTENCED ARTICLE")
print("-" * 80)
url = "https://buzz.bournemouth.ac.uk/2026/01/rapist-sentenced-following-assault-in-bournemouth-home/"
metadata = extract_article_metadata(url)

if metadata and metadata['source_evidence']:
    print(f"Found {len(metadata['source_evidence'])} sources:")
    for i, source in enumerate(metadata['source_evidence'], 1):
        print(f"\n  {i}. Name: '{source['name']}'")
        print(f"     Gender: {source['gender']}")
        print(f"     Type: {source.get('type', 'N/A')}")

        # Check if it's "The victim" - should be normalized
        if source['name'].lower() in ['the victim', 'victim']:
            print(f"     ⚠️ ISSUE: Should be 'Anonymous victim' or 'Unnamed victim'")

# Test 2: Poole sailors
print("\n\n2. POOLE SAILORS ARTICLE")
print("-" * 80)
url = "https://buzz.bournemouth.ac.uk/2026/01/poole-sailors-win-first-sailgp-race/"
metadata = extract_article_metadata(url)

if metadata and metadata['source_evidence']:
    print(f"Found {len(metadata['source_evidence'])} sources:")
    for i, source in enumerate(metadata['source_evidence'], 1):
        print(f"\n  {i}. Name: '{source['name']}'")
        print(f"     Gender: {source['gender']}")
        print(f"     Type: {source.get('type', 'N/A')}")

        # Check for group phrases
        if 'three' in source['name'].lower() or 'poole' in source['name'].lower():
            if not source['name'].replace(' ', '').replace('-', '').isalpha():
                print(f"     ⚠️ POTENTIAL ISSUE: Contains number/group descriptor")

# Also fetch the article and check for "Three Poole" phrase
print("\n\n3. CHECKING ARTICLE TEXT FOR 'THREE POOLE'")
print("-" * 80)
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'lxml')
article = soup.find('article')
if article:
    text = article.get_text()
    if 'Three Poole' in text or 'three Poole' in text:
        idx = text.lower().find('three poole')
        context = text[idx:idx+200]
        print(f"Found 'three Poole' in text:")
        print(f"  Context: {context}")
    else:
        print("'Three Poole' phrase NOT found in article")

    # Check what sailors/sources are mentioned
    import re
    sailor_mentions = re.findall(r'(Dylan Fletcher|Hannah Mills|Tom Slingsby)', text)
    print(f"\nSailor names mentioned in article: {set(sailor_mentions)}")

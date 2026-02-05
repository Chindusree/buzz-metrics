#!/usr/bin/env python3
"""
Debug: Why was Anne Marie Moriarty missed in BPC strikes article?
"""

import requests
from bs4 import BeautifulSoup
from scrape import extract_shorthand_content_new, normalize_quotes, analyze_article_with_groq

shorthand_url = "https://buzznews.shorthandstories.com/bournemouth-and-poole-college-strikes-feature/index.html"

print("=" * 80)
print("DEBUGGING ANNE MARIE MORIARTY DETECTION")
print("=" * 80)
print(f"\nShorthand URL: {shorthand_url}\n")

# Extract content using the same method as scraper
print("STEP 1: Extracting Shorthand content...")
print("-" * 80)
shorthand_data = extract_shorthand_content_new(shorthand_url)

body_text = shorthand_data['body_text']
print(f"Extracted text length: {len(body_text)} characters")
print(f"Word count: {shorthand_data['word_count']}")

# Normalize quotes
normalized_text = normalize_quotes(body_text)
print(f"Normalized text length: {len(normalized_text)} characters")

# Check for Anne Marie Moriarty
print("\n" + "=" * 80)
print("STEP 2: Checking for Anne Marie Moriarty in extracted text")
print("-" * 80)

search_terms = [
    "Anne Marie Moriarty",
    "Anne-Marie Moriarty",
    "Moriarty",
    "Anne Marie",
    "Anne-Marie"
]

found_any = False
for term in search_terms:
    if term in body_text or term in normalized_text:
        print(f"\n✓ FOUND: '{term}'")
        found_any = True

        # Show context
        idx = normalized_text.find(term)
        if idx == -1:
            idx = body_text.find(term)
        context_start = max(0, idx - 200)
        context_end = min(len(normalized_text), idx + len(term) + 200)
        context = normalized_text[context_start:context_end] if term in normalized_text else body_text[context_start:context_end]

        print(f"Context (400 chars):")
        print(f"...{context}...")
        break

if not found_any:
    print("\n✗ Anne Marie Moriarty NOT FOUND in extracted text")
    print("\nThis means the text extraction is incomplete!")

# Check for her quotes
print("\n" + "=" * 80)
print("STEP 3: Checking for Anne Marie Moriarty's quotes")
print("-" * 80)

quotes_to_find = [
    "overworked",
    "national pay bargaining",
    "If we stand together we are stronger",
    "no other option",
    "We needed to be heard and we have been"
]

for quote in quotes_to_find:
    if quote.lower() in normalized_text.lower():
        print(f"\n✓ Found quote: '{quote}'")

        # Find context around quote
        idx = normalized_text.lower().find(quote.lower())
        context_start = max(0, idx - 150)
        context_end = min(len(normalized_text), idx + len(quote) + 150)
        context = normalized_text[context_start:context_end]

        print(f"  Context: ...{context}...")
    else:
        print(f"\n✗ Missing quote: '{quote}'")

# Check text truncation
print("\n" + "=" * 80)
print("STEP 4: Checking if text sent to Groq is truncated")
print("-" * 80)

# Groq receives first 8000 chars (see scrape.py line 111)
groq_text = normalized_text[:8000]
print(f"Text length sent to Groq: {len(groq_text)} chars (limit: 8000)")
print(f"Full text length: {len(normalized_text)} chars")

if len(normalized_text) > 8000:
    print(f"\n⚠️  WARNING: Text is TRUNCATED!")
    print(f"   Missing {len(normalized_text) - 8000} characters")

    # Check if Anne Marie is in the truncated part
    if "Anne Marie Moriarty" in normalized_text[8000:] or "Moriarty" in normalized_text[8000:]:
        print(f"\n✗ PROBLEM FOUND: Anne Marie Moriarty appears AFTER character 8000!")
        print(f"   She's in the truncated part that Groq never sees")

        # Find her position
        idx = normalized_text.find("Moriarty")
        if idx > 8000:
            print(f"   Position: character {idx} (truncation at 8000)")
else:
    print("\n✓ Text is NOT truncated - Groq receives all content")

# Show what Groq actually sees
print("\n" + "=" * 80)
print("STEP 5: Text that Groq receives (first/last 500 chars)")
print("-" * 80)
print("\nFirst 500 chars:")
print(groq_text[:500])
print("\n...")
print("\nLast 500 chars sent to Groq:")
print(groq_text[-500:])

# Check if Anne Marie is in what Groq sees
print("\n" + "=" * 80)
print("STEP 6: Is Anne Marie in the text Groq receives?")
print("-" * 80)

if "Moriarty" in groq_text:
    print("✓ YES - Anne Marie Moriarty is in the text sent to Groq")
    print("\nIf Groq missed her, it's a prompt issue, not a truncation issue")
else:
    print("✗ NO - Anne Marie Moriarty is NOT in the text sent to Groq")
    print("\nThis is a TRUNCATION problem - need to increase character limit")

    # Find where she appears
    full_idx = normalized_text.find("Moriarty")
    if full_idx != -1:
        print(f"\nShe appears at character position: {full_idx}")
        print(f"Groq only receives up to character: 8000")
        print(f"Characters past truncation point: {full_idx - 8000}")

# Actually call Groq to see what it detects
print("\n" + "=" * 80)
print("STEP 7: What sources does Groq actually detect?")
print("-" * 80)

groq_sources = analyze_article_with_groq(body_text)

if groq_sources:
    print(f"\nGroq detected {len(groq_sources)} sources:")
    for i, source in enumerate(groq_sources, 1):
        print(f"  {i}. {source['name']} ({source['gender']})")

    # Check if Anne Marie is in there
    anne_marie_found = any('moriarty' in s['name'].lower() for s in groq_sources)
    if anne_marie_found:
        print("\n✓ Anne Marie Moriarty WAS detected by Groq")
    else:
        print("\n✗ Anne Marie Moriarty was NOT detected by Groq")
        print("\nPossible reasons:")
        print("  1. Her quotes appear after character 8000 (truncation)")
        print("  2. Her name format doesn't match what Groq extracted")
        print("  3. Groq prompt needs improvement")
else:
    print("\nGroq returned no sources (or failed)")

print("\n" + "=" * 80)
print("DEBUGGING COMPLETE")
print("=" * 80)

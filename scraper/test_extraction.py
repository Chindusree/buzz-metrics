#!/usr/bin/env python3
"""
SAFE Testing Script for Source Extraction Development

This script allows testing extraction logic changes WITHOUT touching production data.

Usage:
    python3 test_extraction.py <article_url>

Example:
    python3 test_extraction.py https://buzz.bournemouth.ac.uk/2026/01/article-name/

Features:
    - Fetches a single article
    - Tests extraction functions
    - Prints results to console
    - NEVER writes to data/*.json files
    - Safe for development testing

CRITICAL: Use this instead of scrape.py when testing extraction changes!
"""

import sys
import requests
from bs4 import BeautifulSoup

# Import extraction functions from scrape.py
from scrape import (
    extract_article_metadata,
    extract_sources,
    extract_quoted_sources,
    normalize_quotes
)


def test_single_article(url):
    """
    Test source extraction on a single article.

    Args:
        url: Article URL to test
    """
    print("=" * 80)
    print("SAFE EXTRACTION TEST - NO DATA FILES MODIFIED")
    print("=" * 80)
    print(f"\nTesting URL: {url}\n")

    # Extract full article metadata
    article = extract_article_metadata(url)

    if not article:
        print("❌ Failed to extract article")
        return

    print("✓ Article extracted successfully\n")
    print("-" * 80)
    print("ARTICLE METADATA")
    print("-" * 80)
    print(f"Headline: {article['headline']}")
    print(f"Author: {article['author']}")
    print(f"Date: {article['date']}")
    print(f"Category: {article['category_primary']}")
    print(f"Word count: {article['word_count']}")
    print(f"Content type: {article['content_type']}")

    # Source analysis
    sources = article.get('source_evidence', [])
    print(f"\n{'-' * 80}")
    print("SOURCE EXTRACTION RESULTS")
    print("-" * 80)
    print(f"Total sources found: {len(sources)}\n")

    if sources:
        # Group by position type
        by_position = {}
        for source in sources:
            pos = source.get('position', 'unknown')
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(source)

        # Print by position type
        for position, sources_list in sorted(by_position.items()):
            print(f"\n{position.upper()} ({len(sources_list)}):")
            for i, source in enumerate(sources_list, 1):
                print(f"  {i}. {source['name']}")
                print(f"     Gender: {source.get('gender', 'unknown')}")
                print(f"     Attribution: {source.get('full_attribution', '')[:80]}")
                if source.get('quote_snippet'):
                    print(f"     Quote: \"{source['quote_snippet'][:60]}...\"")

        # Gender breakdown
        gender_counts = {'male': 0, 'female': 0, 'unknown': 0}
        for source in sources:
            gender = source.get('gender', 'unknown')
            if gender in gender_counts:
                gender_counts[gender] += 1

        print(f"\n{'-' * 80}")
        print("GENDER BREAKDOWN")
        print("-" * 80)
        for gender, count in gender_counts.items():
            pct = (count / len(sources) * 100) if sources else 0
            print(f"{gender.capitalize()}: {count} ({pct:.1f}%)")
    else:
        print("⚠️  No sources found in article")

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE - NO FILES MODIFIED")
    print("=" * 80)


def test_text_extraction(text):
    """
    Test source extraction on raw text.
    Useful for testing specific patterns.

    Args:
        text: Text to test extraction on
    """
    print("=" * 80)
    print("TEXT PATTERN TEST")
    print("=" * 80)
    print(f"\nInput text ({len(text)} chars):")
    print(text[:200] + "..." if len(text) > 200 else text)
    print()

    # Normalize quotes
    normalized = normalize_quotes(text)

    # Extract sources
    sources = extract_quoted_sources(normalized)

    print(f"Sources found: {len(sources)}\n")
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   Position: {source.get('position', 'unknown')}")
        print(f"   Attribution: {source.get('full_attribution', '')[:80]}")
        print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 test_extraction.py <article_url>")
        print()
        print("Example:")
        print("  python3 test_extraction.py https://buzz.bournemouth.ac.uk/2026/01/article/")
        print()
        print("For text testing:")
        print('  python3 test_extraction.py --text "Name, who did thing, said something"')
        sys.exit(1)

    arg = sys.argv[1]

    if arg == '--text':
        if len(sys.argv) < 3:
            print("Error: --text requires a text argument")
            sys.exit(1)
        test_text_extraction(sys.argv[2])
    else:
        test_single_article(arg)


if __name__ == '__main__':
    main()

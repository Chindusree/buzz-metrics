#!/usr/bin/env python3
"""
Analyze SEI results - create stakeholder tables and spot checks
"""
import json
import requests
from bs4 import BeautifulSoup

def fetch_article_text(url):
    """Fetch first 300 words of article body"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try Shorthand first
        shorthand = soup.find('div', class_='markup')
        if shorthand:
            text = shorthand.get_text(separator=' ', strip=True)
            words = text.split()[:300]
            return ' '.join(words)

        # Standard WordPress
        content = soup.find('div', class_='entry-content')
        if content:
            text = content.get_text(separator=' ', strip=True)
            words = text.split()[:300]
            return ' '.join(words)

        return "Could not extract article text"
    except Exception as e:
        return f"Error fetching: {e}"

def main():
    # Load data
    with open('data/metrics_sei.json', 'r') as f:
        data = json.load(f)

    articles = data['articles']

    # Get analyzed articles with scores
    analyzed = [a for a in articles if a.get('sei_score') is not None]
    analyzed.sort(key=lambda x: x['sei_score'], reverse=True)

    # TASK 1: Top 5 Stakeholder Tables
    print("=" * 100)
    print("TASK 1: STAKEHOLDER MAPPING FOR TOP 5 SCORERS")
    print("=" * 100)

    top_5 = analyzed[:5]

    for i, article in enumerate(top_5, 1):
        print(f"\n{'='*100}")
        print(f"#{i} | {article['headline']}")
        print(f"URL: {article['url']}")
        print(f"SEI Score: {article['sei_score']}")
        print(f"{'='*100}")

        groq = article.get('groq_response', {})
        sources = groq.get('quoted_sources', [])
        stakeholders = groq.get('stakeholder_mapping', {}).get('stakeholders', [])

        # Sources table
        print("\nSOURCES FOUND:")
        print(f"{'Name':<30} | {'Gender':<8} | {'Category':<15}")
        print("-" * 60)
        for source in sources:
            name = source.get('name', 'Unknown')
            gender = source.get('gender', 'Unknown')
            role = source.get('role', 'Unknown')
            print(f"{name:<30} | {gender:<8} | {role:<15}")

        # Ghost stakeholders
        print("\nGHOST STAKEHOLDERS:")
        ghost_count = 0
        for stakeholder in stakeholders:
            if not stakeholder.get('was_quoted', False):
                ghost_count += 1
                group = stakeholder.get('group', 'Unknown')
                examples = stakeholder.get('examples', [])
                examples_str = ', '.join(examples) if examples else '(none listed)'
                print(f"  • {group}: {examples_str}")

        if ghost_count == 0:
            print("  (None - all stakeholders were quoted)")

    # TASK 2: Low Scorer Spot Checks
    print("\n\n")
    print("=" * 100)
    print("TASK 2: LOW SCORER BREAKDOWN + SPOT CHECKS")
    print("=" * 100)

    # Get 0-20 band
    low_scorers = [a for a in analyzed if a['sei_score'] <= 20]

    # Count by source count
    zero_sources = []
    one_source = []
    two_plus_sources = []

    for article in low_scorers:
        groq = article.get('groq_response', {})
        sources = groq.get('quoted_sources', [])
        source_count = len(sources)

        if source_count == 0:
            zero_sources.append(article)
        elif source_count == 1:
            one_source.append(article)
        else:
            two_plus_sources.append(article)

    print(f"\nLOW SCORERS (0-20) BREAKDOWN:")
    print(f"  • 0 sources: {len(zero_sources)} articles")
    print(f"  • 1 source:  {len(one_source)} articles")
    print(f"  • 2+ sources: {len(two_plus_sources)} articles")
    print(f"  • TOTAL: {len(low_scorers)} articles")

    # Select spot check samples
    print("\n\nSPOT CHECK SAMPLES:")
    print("=" * 100)

    spot_checks = []

    # Pick 2 from zero sources
    if len(zero_sources) >= 2:
        spot_checks.extend(zero_sources[:2])

    # Pick 2 from one source
    if len(one_source) >= 2:
        spot_checks.extend(one_source[:2])

    # Pick 1 from two+ sources
    if len(two_plus_sources) >= 1:
        spot_checks.append(two_plus_sources[0])

    for i, article in enumerate(spot_checks, 1):
        print(f"\n{'='*100}")
        print(f"SPOT CHECK #{i}")
        print(f"{'='*100}")

        print(f"\nHeadline: {article['headline']}")
        print(f"URL: {article['url']}")
        print(f"SEI Score: {article['sei_score']}")

        groq = article.get('groq_response', {})
        sources = groq.get('quoted_sources', [])

        print(f"\nQuoted Sources ({len(sources)}):")
        if len(sources) == 0:
            print("  (None)")
        else:
            for source in sources:
                name = source.get('name', 'Unknown')
                gender = source.get('gender', 'Unknown')
                role = source.get('role', 'Unknown')
                print(f"  • {name} ({gender}, {role})")

        components = article.get('sei_components', {})
        print(f"\nSEI Components:")
        print(f"  • Inclusion: {components.get('inclusion', 0):.1f}")
        print(f"  • Structural Agency: {components.get('structural_agency', 0):.1f}")
        print(f"  • Impact Equity: {components.get('impact_equity', 0):.1f}")
        print(f"  • Ghost Ratio: {components.get('ghost_ratio', 0):.2f}")

        print(f"\nFirst 300 words of article body:")
        print("-" * 100)
        article_text = fetch_article_text(article['url'])
        print(article_text)
        print("-" * 100)

if __name__ == "__main__":
    main()

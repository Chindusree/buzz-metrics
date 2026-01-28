#!/usr/bin/env python3
"""
Rescore the two Shorthand articles with full content
"""
import json
import os
import sys
sys.path.insert(0, '/Users/creedharan/buzz-metrics/scraper')

from sei_production import analyze_with_groq, calculate_sei_score

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Load investigation results
with open('scraper/shorthand_investigation.json', 'r') as f:
    investigation = json.load(f)

# Load current SEI data
with open('data/metrics_sei.json', 'r') as f:
    sei_data = json.load(f)

print("="*100)
print("RESCORING SHORTHAND ARTICLES WITH FULL CONTENT")
print("="*100)

for article_data in investigation:
    if not article_data.get('is_shorthand'):
        continue

    url = article_data['url']
    full_text = article_data.get('full_text')
    word_count = article_data.get('word_count')

    if not full_text:
        print(f"\nSkipping {article_data['article_name']} - no content extracted")
        continue

    print(f"\n{'='*100}")
    print(f"Rescoring: {article_data['article_name']}")
    print(f"URL: {url}")
    print(f"Word count: {word_count}")
    print("="*100)

    # Find original article in sei_data
    original_article = None
    article_index = None
    for i, article in enumerate(sei_data['articles']):
        if article['url'] == url:
            original_article = article
            article_index = i
            break

    if not original_article:
        print(f"ERROR: Could not find article in metrics_sei.json")
        continue

    print(f"\nORIGINAL SCORING:")
    print(f"  SEI Score: {original_article.get('sei_score')}")
    print(f"  Sources: {len(original_article.get('groq_response', {}).get('quoted_sources', []))}")

    # Analyze with Groq using full content
    print(f"\nAnalyzing with Groq (full Shorthand content)...")

    try:
        groq_response = analyze_with_groq(
            article_text=full_text,
            content_type='shorthand',
            word_count=word_count,
            category='Unknown'
        )

        # Check if exempt
        if groq_response.get('sei_exempt'):
            print(f"\n✓ Article is EXEMPT: {groq_response['sei_exempt']}")
            print(f"  Reason: {groq_response.get('reasoning', 'N/A')}")

            # Update article
            sei_data['articles'][article_index]['sei_exempt'] = groq_response['sei_exempt']
            sei_data['articles'][article_index]['sei_score'] = None
            sei_data['articles'][article_index]['sei_components'] = None
            sei_data['articles'][article_index]['groq_response'] = groq_response

            # Update metadata counts
            sei_data['metadata']['analyzed'] -= 1
            sei_data['metadata']['exempt'] += 1

        else:
            # Calculate SEI score
            sei_inputs = groq_response.get('sei_inputs', {})
            sei_result = calculate_sei_score(groq_response)
            sei_score = sei_result['score']
            sei_components = sei_result['components']

            print(f"\nNEW SCORING:")
            print(f"  SEI Score: {sei_score}")
            print(f"  Sources: {sei_inputs.get('total_sources', 0)}")
            print(f"    - Non-male: {sei_inputs.get('non_male_sources', 0)}")
            print(f"    - Male: {sei_inputs.get('male_sources', 0)}")
            print(f"  Components:")
            print(f"    - Inclusion: {sei_components['inclusion']:.1f}")
            print(f"    - Structural Agency: {sei_components['structural_agency']:.1f}")
            print(f"    - Impact Equity: {sei_components['impact_equity']:.1f}")
            print(f"    - Ghost Ratio: {sei_components['ghost_ratio']:.2f}")

            # Show sources
            print(f"\n  Quoted Sources:")
            for source in groq_response.get('quoted_sources', []):
                print(f"    - {source.get('name')} ({source.get('gender')}, {source.get('role')})")

            # Update article
            sei_data['articles'][article_index]['groq_response'] = groq_response
            sei_data['articles'][article_index]['sei_score'] = sei_score
            sei_data['articles'][article_index]['sei_components'] = sei_components
            sei_data['articles'][article_index]['metadata'] = {
                'content_type': 'shorthand',
                'word_count': word_count,
                'category': 'Unknown'
            }

            # Compare
            old_score = original_article.get('sei_score')
            if old_score != sei_score:
                diff = sei_score - old_score if old_score else sei_score
                print(f"\n  Score change: {old_score} → {sei_score} (Δ {diff:+.1f})")

    except Exception as e:
        print(f"\nERROR during Groq analysis: {e}")
        import traceback
        traceback.print_exc()

# Save updated data
print(f"\n{'='*100}")
print("SAVING UPDATED DATA")
print(f"{'='*100}")

with open('data/metrics_sei.json', 'w') as f:
    json.dump(sei_data, f, indent=2)

print(f"\n✓ Updated metrics_sei.json")
print(f"\nMetadata:")
print(f"  Total: {sei_data['metadata']['total_articles']}")
print(f"  Analyzed: {sei_data['metadata']['analyzed']}")
print(f"  Exempt: {sei_data['metadata']['exempt']}")
print(f"  Errors: {sei_data['metadata']['errors']}")

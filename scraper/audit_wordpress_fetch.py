#!/usr/bin/env python3
"""
Audit WordPress article fetching during SEI run
Verify all non-Shorthand articles had proper content
"""
import json
import requests
from bs4 import BeautifulSoup
import re

print("="*100)
print("WORDPRESS ARTICLE FETCH AUDIT")
print("="*100)

# Load data
with open('data/metrics_verified.json', 'r') as f:
    verified = json.load(f)

with open('data/metrics_sei.json', 'r') as f:
    sei = json.load(f)

# Load Shorthand list
with open('scraper/full_shorthand_scan.json', 'r') as f:
    shorthand_scan = json.load(f)

shorthand_urls = set([s['url'] for s in shorthand_scan['all_shorthand']])

print(f"\nTotal articles: {len(verified['articles'])}")
print(f"Shorthand articles: {len(shorthand_urls)}")
print(f"WordPress articles: {len(verified['articles']) - len(shorthand_urls)}")

# Get all WordPress articles
wordpress_articles = []

for article in verified['articles']:
    if article['url'] not in shorthand_urls:
        wordpress_articles.append(article)

print(f"\n{'='*100}")
print("ANALYSIS 1: Check SEI scores for WordPress articles")
print(f"{'='*100}")

# Find corresponding SEI data
wp_with_scores = []
wp_without_scores = []
wp_errors = []
wp_exempt = []

for wp_article in wordpress_articles:
    url = wp_article['url']

    # Find in SEI data
    sei_article = None
    for s in sei['articles']:
        if s['url'] == url:
            sei_article = s
            break

    if not sei_article:
        wp_without_scores.append({
            'headline': wp_article['headline'],
            'url': url,
            'reason': 'not_found_in_sei'
        })
        continue

    # Check status
    if sei_article.get('sei_exempt'):
        wp_exempt.append({
            'headline': wp_article['headline'],
            'url': url,
            'exempt_reason': sei_article['sei_exempt']
        })
    elif sei_article.get('sei_error'):
        wp_errors.append({
            'headline': wp_article['headline'],
            'url': url,
            'error': sei_article['sei_error']
        })
    elif sei_article.get('sei_score') is not None:
        # Check if Groq analysis looks reasonable
        groq = sei_article.get('groq_response', {})
        sources = groq.get('quoted_sources', [])

        wp_with_scores.append({
            'headline': wp_article['headline'],
            'url': url,
            'sei_score': sei_article['sei_score'],
            'source_count': len(sources),
            'has_groq_response': bool(groq)
        })
    else:
        wp_without_scores.append({
            'headline': wp_article['headline'],
            'url': url,
            'reason': 'no_score_or_error'
        })

print(f"\nWordPress articles breakdown:")
print(f"  ✓ Scored: {len(wp_with_scores)}")
print(f"  ⊘ Exempt: {len(wp_exempt)}")
print(f"  ✗ Errors: {len(wp_errors)}")
print(f"  ? Missing: {len(wp_without_scores)}")

if wp_errors:
    print(f"\n\nArticles with ERRORS during SEI run:")
    for i, article in enumerate(wp_errors[:10], 1):
        print(f"{i}. {article['headline'][:70]}")
        print(f"   Error: {article['error']}")

if wp_without_scores:
    print(f"\n\nArticles WITHOUT scores (unexpected):")
    for i, article in enumerate(wp_without_scores[:5], 1):
        print(f"{i}. {article['headline'][:70]}")
        print(f"   Reason: {article['reason']}")

print(f"\n{'='*100}")
print("ANALYSIS 2: Test current fetch_article_content() on sample WordPress articles")
print(f"{'='*100}")

# Test function from sei_production.py
def fetch_article_content(url):
    """Exact copy from sei_production.py"""
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for Shorthand
        iframe = soup.find('iframe', src=lambda x: x and 'shorthandstories.com' in x)
        is_shorthand = False

        if iframe:
            is_shorthand = True
            shorthand_url = iframe['src']
            response = requests.get(shorthand_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

        # Extract body
        if is_shorthand:
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            body = soup.get_text(separator='\n', strip=True)
        else:
            content = soup.find('div', class_='entry-content')
            if content:
                for tag in content.find_all(['script', 'style']):
                    tag.decompose()
                body = content.get_text(separator='\n', strip=True)
            else:
                body = ""

        return body, is_shorthand

    except Exception as e:
        return None, False

print(f"\nTesting 10 random WordPress articles...")

import random
sample = random.sample(wp_with_scores, min(10, len(wp_with_scores)))

fetch_success = []
fetch_failures = []

for article in sample:
    url = article['url']
    headline = article['headline']

    print(f"\nTesting: {headline[:60]}")

    body, is_shorthand = fetch_article_content(url)

    if body:
        word_count = len(body.split())
        print(f"  ✓ Fetched: {word_count} words")

        # Sanity check - should have reasonable content
        if word_count < 50:
            print(f"  ⚠️  WARNING: Very short content (< 50 words)")
            fetch_failures.append({
                'url': url,
                'headline': headline,
                'word_count': word_count,
                'reason': 'too_short'
            })
        else:
            fetch_success.append({
                'url': url,
                'headline': headline,
                'word_count': word_count
            })
    else:
        print(f"  ✗ FAILED to fetch")
        fetch_failures.append({
            'url': url,
            'headline': headline,
            'word_count': 0,
            'reason': 'fetch_returned_none'
        })

print(f"\n{'='*100}")
print("ANALYSIS 3: Check content length indicators in Groq responses")
print(f"{'='*100}")

print(f"\nChecking if Groq analyzed substantial content...")

# Check stakeholder counts as proxy for content quality
low_content_indicators = []
good_content_indicators = []

for article in wp_with_scores[:50]:  # Check first 50
    url = article['url']

    # Find full SEI article
    sei_article = None
    for s in sei['articles']:
        if s['url'] == url:
            sei_article = s
            break

    if not sei_article:
        continue

    groq = sei_article.get('groq_response', {})

    # Check indicators
    stakeholder_mapping = groq.get('stakeholder_mapping', {})
    stakeholders = stakeholder_mapping.get('stakeholders', [])
    core_event = stakeholder_mapping.get('core_event', '')

    sources = groq.get('quoted_sources', [])

    # If Groq identified stakeholders and core event, it had content
    if stakeholders and core_event:
        good_content_indicators.append(url)
    else:
        low_content_indicators.append({
            'url': url,
            'headline': article['headline'],
            'sources': len(sources),
            'stakeholders': len(stakeholders),
            'has_core_event': bool(core_event)
        })

print(f"\nSample of 50 WordPress articles:")
print(f"  ✓ Good content indicators: {len(good_content_indicators)}")
print(f"  ⚠️  Low content indicators: {len(low_content_indicators)}")

if low_content_indicators:
    print(f"\n\nArticles with weak content indicators:")
    for i, article in enumerate(low_content_indicators[:5], 1):
        print(f"{i}. {article['headline'][:70]}")
        print(f"   Sources: {article['sources']}, Stakeholders: {article['stakeholders']}, Core event: {article['has_core_event']}")

print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

total_wp = len(wordpress_articles)
scored = len(wp_with_scores)
exempt = len(wp_exempt)
errors = len(wp_errors)

print(f"\nWordPress articles: {total_wp}")
print(f"  Successfully scored: {scored} ({scored/total_wp*100:.1f}%)")
print(f"  Exempt: {exempt} ({exempt/total_wp*100:.1f}%)")
print(f"  Errors: {errors} ({errors/total_wp*100:.1f}%)")

print(f"\nFetch test results:")
print(f"  Success: {len(fetch_success)}/{len(sample)}")
print(f"  Failures: {len(fetch_failures)}/{len(sample)}")

print(f"\nContent quality indicators (sample of 50):")
print(f"  Good: {len(good_content_indicators)} ({len(good_content_indicators)/50*100:.0f}%)")
print(f"  Weak: {len(low_content_indicators)} ({len(low_content_indicators)/50*100:.0f}%)")

# Save results
results = {
    'total_wordpress': total_wp,
    'scored': len(wp_with_scores),
    'exempt': len(wp_exempt),
    'errors': len(wp_errors),
    'missing': len(wp_without_scores),
    'error_articles': wp_errors,
    'missing_articles': wp_without_scores,
    'fetch_test': {
        'success': len(fetch_success),
        'failures': len(fetch_failures),
        'failure_details': fetch_failures
    },
    'content_quality': {
        'good_indicators': len(good_content_indicators),
        'weak_indicators': len(low_content_indicators),
        'weak_details': low_content_indicators
    }
}

with open('scraper/wordpress_fetch_audit.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Full audit saved to: scraper/wordpress_fetch_audit.json")

# VERDICT
print(f"\n{'='*100}")
print("VERDICT")
print(f"{'='*100}")

if errors <= 2 and len(fetch_failures) == 0 and len(low_content_indicators) <= 5:
    print("\n✅ PASS: WordPress articles were fetched properly during SEI run")
    print("   - High success rate for scoring")
    print("   - Current fetch function works correctly")
    print("   - Good content quality indicators in Groq responses")
elif errors > 5 or len(fetch_failures) > 2:
    print("\n⚠️  CONCERN: Some WordPress articles may have fetch issues")
    print(f"   - {errors} errors during original run")
    print(f"   - {len(fetch_failures)} failures in current test")
    print("   - Recommend investigating specific failures")
else:
    print("\n✓ ACCEPTABLE: WordPress fetch mostly successful with minor issues")
    print("   - Minor issues detected but overall quality is good")

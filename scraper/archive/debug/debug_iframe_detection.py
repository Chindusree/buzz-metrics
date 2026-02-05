#!/usr/bin/env python3
"""
Debug why sei_production.py's fetch_article_content() failed for 26/28 Shorthand articles
"""
import requests
from bs4 import BeautifulSoup
import json
import re

# Load the 28 Shorthand URLs
with open('scraper/full_shorthand_scan.json', 'r') as f:
    scan_results = json.load(f)

shorthand_articles = scan_results['all_shorthand']

print("="*100)
print("DEBUGGING IFRAME DETECTION FAILURE")
print("="*100)

# Test the EXACT code from sei_production.py lines 234-264
def fetch_article_content_original(url):
    """Exact copy of sei_production.py's fetch_article_content()"""
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
        print(f"  Error: {e}")
        return None, False


print(f"\nTesting iframe detection on all {len(shorthand_articles)} Shorthand articles...")
print("\nThis will take ~2 minutes...\n")

success = []
failures = []

for i, article in enumerate(shorthand_articles, 1):
    url = article['url']
    headline = article['headline']

    print(f"[{i}/{len(shorthand_articles)}] {headline[:60]}")

    # Test the function
    body, is_shorthand = fetch_article_content_original(url)

    if body and is_shorthand:
        word_count = len(body.split())
        print(f"  ✓ SUCCESS: Detected Shorthand, {word_count} words")
        success.append({
            'url': url,
            'headline': headline,
            'word_count': word_count
        })
    elif is_shorthand and not body:
        print(f"  ⚠️  DETECTED Shorthand but body is EMPTY")
        failures.append({
            'url': url,
            'headline': headline,
            'reason': 'shorthand_detected_but_empty_body'
        })
    else:
        print(f"  ✗ FAILED: Did not detect Shorthand iframe")

        # Let's debug WHY it failed
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check different iframe detection methods
            iframe_basic = soup.find('iframe')
            iframe_shorthand = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
            iframe_lambda = soup.find('iframe', src=lambda x: x and 'shorthandstories.com' in x)

            print(f"     Debug:")
            print(f"       - Any iframe: {iframe_basic is not None}")
            if iframe_basic:
                print(f"       - iframe src: {iframe_basic.get('src', 'NO SRC')[:80]}")
            print(f"       - Regex match: {iframe_shorthand is not None}")
            print(f"       - Lambda match: {iframe_lambda is not None}")

            # Check for data-src or other attributes
            if iframe_basic and not iframe_basic.get('src'):
                print(f"       - iframe has data-src: {iframe_basic.get('data-src', 'NO')[:80]}")

        except Exception as e:
            print(f"     Debug error: {e}")

        failures.append({
            'url': url,
            'headline': headline,
            'reason': 'iframe_not_detected'
        })

print("\n" + "="*100)
print("RESULTS")
print("="*100)

print(f"\nSuccess: {len(success)}")
print(f"Failures: {len(failures)}")
print(f"Success rate: {len(success)/len(shorthand_articles)*100:.1f}%")

if failures:
    print(f"\n\nFAILURE ANALYSIS:")
    print("-"*100)

    iframe_not_detected = [f for f in failures if f['reason'] == 'iframe_not_detected']
    empty_body = [f for f in failures if f['reason'] == 'shorthand_detected_but_empty_body']

    print(f"\nIframe not detected: {len(iframe_not_detected)}")
    print(f"Shorthand detected but empty body: {len(empty_body)}")

    if iframe_not_detected:
        print(f"\n\nArticles where iframe was NOT detected:")
        for i, f in enumerate(iframe_not_detected[:5], 1):
            print(f"{i}. {f['headline'][:70]}")
            print(f"   {f['url']}")

    if empty_body:
        print(f"\n\nArticles where Shorthand was detected but body was empty:")
        for i, f in enumerate(empty_body, 1):
            print(f"{i}. {f['headline'][:70]}")
            print(f"   {f['url']}")

# Save results
debug_results = {
    'total_tested': len(shorthand_articles),
    'success_count': len(success),
    'failure_count': len(failures),
    'success': success,
    'failures': failures
}

with open('scraper/iframe_debug_results.json', 'w') as f:
    json.dump(debug_results, f, indent=2)

print(f"\n\n✓ Full results saved to: scraper/iframe_debug_results.json")

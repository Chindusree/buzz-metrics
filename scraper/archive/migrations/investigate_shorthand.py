#!/usr/bin/env python3
"""
Investigate Lymington sailor and Lions captain articles for Shorthand embeds
"""
import requests
from bs4 import BeautifulSoup
import json
import re

def check_shorthand(url):
    """Check if article is Shorthand embed and extract details"""
    print(f"\n{'='*100}")
    print(f"Checking: {url}")
    print(f"{'='*100}")

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for Shorthand iframe
        iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))

        if iframe:
            shorthand_url = iframe['src']
            print(f"✓ IS SHORTHAND EMBED")
            print(f"Shorthand URL: {shorthand_url}")

            # Fetch Shorthand content
            try:
                sh_response = requests.get(shorthand_url, timeout=10)
                sh_soup = BeautifulSoup(sh_response.text, 'html.parser')

                # Extract text from Shorthand
                text_blocks = []

                # Try multiple Shorthand selectors
                for selector in [
                    ('div', {'id': 'app'}),
                    ('div', {'class': 'markup'}),
                    ('article', {}),
                ]:
                    container = sh_soup.find(selector[0], selector[1])
                    if container:
                        for elem in container.find_all(['p', 'h1', 'h2', 'h3', 'blockquote', 'li']):
                            text = elem.get_text(strip=True)
                            if text and len(text) > 10:
                                text_blocks.append(text)
                        if text_blocks:
                            break

                if text_blocks:
                    full_text = ' '.join(text_blocks)
                    word_count = len(full_text.split())
                    print(f"Word count: {word_count}")
                    print(f"\nFirst 300 words:")
                    print('-' * 100)
                    words = full_text.split()[:300]
                    print(' '.join(words))
                    print('-' * 100)

                    # Look for quotes (basic detection)
                    quote_pattern = re.compile(r'["""]([^"""]+)["""]|said:|:')
                    quotes_found = quote_pattern.findall(full_text[:2000])
                    print(f"\nQuote indicators found: {len(quotes_found)}")

                    return {
                        'is_shorthand': True,
                        'shorthand_url': shorthand_url,
                        'word_count': word_count,
                        'full_text': full_text,
                        'preview': ' '.join(words[:300])
                    }
                else:
                    print("✗ Could not extract Shorthand content")
                    return {'is_shorthand': True, 'shorthand_url': shorthand_url, 'error': 'extraction_failed'}

            except Exception as e:
                print(f"✗ Error fetching Shorthand content: {e}")
                return {'is_shorthand': True, 'shorthand_url': shorthand_url, 'error': str(e)}
        else:
            print("✗ NOT a Shorthand embed")

            # Try standard WordPress extraction
            content = soup.find('div', class_='entry-content')
            if content:
                # Remove scripts/styles
                for elem in content.find_all(['script', 'style', 'iframe']):
                    elem.decompose()

                text = content.get_text(separator=' ', strip=True)
                word_count = len(text.split())
                print(f"Standard WordPress article")
                print(f"Word count: {word_count}")
                print(f"\nFirst 300 words:")
                print('-' * 100)
                words = text.split()[:300]
                print(' '.join(words))
                print('-' * 100)

                return {
                    'is_shorthand': False,
                    'word_count': word_count,
                    'full_text': text,
                    'preview': ' '.join(words[:300])
                }
            else:
                print("✗ Could not extract any content")
                return {'is_shorthand': False, 'error': 'no_content'}

    except Exception as e:
        print(f"✗ Error: {e}")
        return {'error': str(e)}

def get_current_score(url):
    """Get current SEI score from metrics_sei.json"""
    with open('data/metrics_sei.json', 'r') as f:
        data = json.load(f)

    for article in data['articles']:
        if article['url'] == url:
            return {
                'sei_score': article.get('sei_score'),
                'sei_exempt': article.get('sei_exempt'),
                'quoted_sources': article.get('groq_response', {}).get('quoted_sources', [])
            }
    return None

# Check both articles
articles = [
    {
        'name': 'Lymington sailor',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/lymingtons-sailor-extends-record-championship-reign-in-shenzhen/'
    },
    {
        'name': 'Lions captain',
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/grant-hancox-acl-feature-2/'
    }
]

results = []

for article in articles:
    print(f"\n\n{'#'*100}")
    print(f"# {article['name'].upper()}")
    print(f"{'#'*100}")

    # Get current scoring
    current = get_current_score(article['url'])
    if current:
        print(f"\nCURRENT SEI DATA:")
        print(f"  Score: {current['sei_score']}")
        print(f"  Exempt: {current['sei_exempt']}")
        print(f"  Sources: {len(current['quoted_sources'])}")
        for source in current['quoted_sources']:
            print(f"    - {source.get('name')} ({source.get('gender')}, {source.get('role')})")

    # Check for Shorthand
    result = check_shorthand(article['url'])
    result['article_name'] = article['name']
    result['url'] = article['url']
    result['current_score'] = current
    results.append(result)

# Summary
print(f"\n\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

for result in results:
    print(f"\n{result['article_name']}:")
    print(f"  URL: {result['url']}")
    print(f"  Is Shorthand: {result.get('is_shorthand', False)}")
    if result.get('shorthand_url'):
        print(f"  Shorthand URL: {result['shorthand_url']}")
    if result.get('word_count'):
        print(f"  Word count: {result['word_count']}")
    if result['current_score']:
        print(f"  Current SEI score: {result['current_score']['sei_score']}")
    if result.get('error'):
        print(f"  ERROR: {result['error']}")

# Save results
with open('scraper/shorthand_investigation.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n\nFull results saved to: scraper/shorthand_investigation.json")

#!/usr/bin/env python3
"""
SSI 2.1 Validation Test
Tests the revised SSI prompt against 6 real BUzz articles
"""

import json
import os
import time
from bs4 import BeautifulSoup
import requests
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

# Load SSI 2.1 prompt
with open('ssi_prompt_v2.1.md', 'r') as f:
    SSI_PROMPT = f.read()

# Test cases with expected outcomes
TEST_ARTICLES = [
    {
        'num': 1,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/breaking-news-bundee-aki-dropped-from-ireland-six-nations-squad/',
        'expected': {
            'ssi_exempt': False,
            'ssi_gate': '40-CAP',
            'sd': 0.0,
            'oi': 0.0,
            'reason': 'Wire rewrite of IRFU statement, no sources'
        }
    },
    {
        'num': 2,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/bournemouth-vs-liverpool-preview-and-predictions/',
        'expected': {
            'ssi_exempt': True,
            'ssi_exempt_reason': 'MATCH_PREVIEW',
            'reason': "Should detect 'vs' + Sport category"
        }
    },
    {
        'num': 3,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/breaking-romain-faivre-joins-auxerre-on-loan/',
        'expected': {
            'ssi_exempt': True,
            'ssi_exempt_reason': 'BREAKING',
            'reason': 'Headline starts with BREAKING:'
        }
    },
    {
        'num': 4,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/rain-hinders-raducanus-austrailian-open-preperation/',
        'expected': {
            'ssi_exempt': False,
            'ssi_gate': '40-CAP',
            'sd': 0.0,
            'oi': 0.0,
            'cd_timeline': True,
            'reason': 'Broadcast rewrite, 0 sources, should find timeline (2021 US Open)'
        }
    },
    {
        'num': 5,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/college-staff-to-strike-this-week/',
        'expected': {
            'ssi_exempt': False,
            'ssi_gate': None,
            'sd_min': 0.33,
            'oi_min': 0.5,
            'reason': 'Local story, should find sources with GOOD_FAITH OI'
        }
    },
    {
        'num': 6,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/breaking-news-dorset-fire-stations-announce-stations-at-risk-of-closure/',
        'expected': {
            'ssi_exempt': True,
            'ssi_exempt_reason': 'BREAKING',
            'reason': 'BREAKING in headline - tests exemption priority'
        }
    },
    {
        'num': 7,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/the-rise-of-walking-football-in-bournemouth/',
        'expected': {
            'ssi_exempt': False,
            'ssi_gate': None,
            'sd_min': 0.33,
            'oi_min': 0.7,
            'reason': 'Local feature, sources should be GOOD_FAITH or ORIGINAL'
        }
    },
    {
        'num': 8,
        'url': 'https://buzz.bournemouth.ac.uk/2026/01/breaking-oliver-glasner-confirms-marc-guehi-departure/',
        'expected': {
            'ssi_exempt': True,
            'ssi_exempt_reason': 'BREAKING',
            'reason': 'BREAKING headline - but if not exempt, would test presser quotes'
        }
    }
]


def fetch_article(url):
    """Fetch article text from BUzz URL"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Extract headline
        headline_tag = soup.find('h1', class_='entry-title')
        headline = headline_tag.get_text(strip=True) if headline_tag else ''

        # Extract category
        category_tag = soup.find('span', class_='cat-links')
        category = category_tag.get_text(strip=True) if category_tag else ''

        # Extract article text
        content = soup.find('div', class_='entry-content')
        if not content:
            return None, 'No article content found'

        # Get all paragraphs
        paragraphs = content.find_all('p')
        article_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # Calculate word count
        word_count = len(article_text.split())

        return {
            'headline': headline,
            'category': category,
            'word_count': word_count,
            'article_text': article_text
        }, None

    except Exception as e:
        return None, f'Fetch error: {str(e)}'


def call_groq_ssi(headline, word_count, category, article_text):
    """Call Groq with SSI 2.1 prompt"""
    try:
        user_msg = f"""Headline: {headline}
Word Count: {word_count}
Category: {category}

Article Text:
{article_text}"""

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': SSI_PROMPT},
                {'role': 'user', 'content': user_msg}
            ],
            temperature=0.1,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1])

        result = json.loads(result_text)
        return result, None

    except json.JSONDecodeError as e:
        return None, f'JSON parse error: {str(e)}'
    except Exception as e:
        return None, f'Groq error: {str(e)}'


def validate_result(result, expected):
    """Validate Groq result against expected outcome"""
    issues = []

    # Check exemption
    if expected.get('ssi_exempt'):
        if not result.get('ssi_exempt'):
            issues.append(f"Expected exempt=true, got {result.get('ssi_exempt')}")
        elif result.get('ssi_exempt_reason') != expected.get('ssi_exempt_reason'):
            issues.append(f"Expected exempt reason '{expected.get('ssi_exempt_reason')}', got '{result.get('ssi_exempt_reason')}'")
    else:
        if result.get('ssi_exempt'):
            issues.append(f"Expected exempt=false, got exempt=true ({result.get('ssi_exempt_reason')})")

    # Check gate
    if 'ssi_gate' in expected:
        if result.get('ssi_gate') != expected['ssi_gate']:
            issues.append(f"Expected gate '{expected['ssi_gate']}', got '{result.get('ssi_gate')}'")

    # Check score
    if 'ssi_score' in expected:
        actual_score = result.get('ssi_score')
        if actual_score != expected['ssi_score']:
            issues.append(f"Expected score {expected['ssi_score']}, got {actual_score}")

    # Check score range
    if 'ssi_score_range' in expected:
        actual_score = result.get('ssi_score')
        min_score, max_score = expected['ssi_score_range']
        if not (min_score <= actual_score <= max_score):
            issues.append(f"Expected score in range {min_score}-{max_score}, got {actual_score}")

    # Check component values (SD, OI)
    components = result.get('ssi_components', {})

    if 'sd' in expected:
        actual_sd = components.get('sd', 0)
        if actual_sd != expected['sd']:
            issues.append(f"Expected SD={expected['sd']}, got {actual_sd}")

    if 'oi' in expected:
        actual_oi = components.get('oi', 0)
        if actual_oi != expected['oi']:
            issues.append(f"Expected OI={expected['oi']}, got {actual_oi}")

    # Check minimum thresholds
    if 'sd_min' in expected and not result.get('ssi_exempt'):
        actual_sd = components.get('sd', 0)
        if actual_sd < expected['sd_min']:
            issues.append(f"SD_MIN: got {actual_sd}, expected >= {expected['sd_min']}")

    if 'oi_min' in expected and not result.get('ssi_exempt'):
        actual_oi = components.get('oi', 0)
        if actual_oi < expected['oi_min']:
            issues.append(f"OI_MIN: got {actual_oi}, expected >= {expected['oi_min']}")

    # Check context flags
    if 'cd_timeline' in expected and not result.get('ssi_exempt'):
        actual_timeline = result.get('ssi_context_flags', {}).get('has_timeline', False)
        if actual_timeline != expected['cd_timeline']:
            issues.append(f"Expected has_timeline={expected['cd_timeline']}, got {actual_timeline}")

    return issues


def main():
    print('=' * 95)
    print('SSI 2.1 VALIDATION TEST')
    print('=' * 95)
    print()

    results = []
    passed = 0
    failed = 0

    for test in TEST_ARTICLES:
        num = test['num']
        url = test['url']
        expected = test['expected']

        print(f"[TEST {num}] {url}")
        print(f"  Expected: {expected['reason']}")

        # Fetch article
        article, error = fetch_article(url)
        if error:
            print(f"  ✗ {error}")
            results.append({
                'test': num,
                'url': url,
                'status': 'FETCH_ERROR',
                'error': error
            })
            failed += 1
            print()
            continue

        print(f"  ✓ Fetched: {article['headline'][:60]}...")
        print(f"    {article['word_count']} words, category: {article['category']}")

        # Call Groq
        time.sleep(1.5)  # Rate limiting
        result, error = call_groq_ssi(
            article['headline'],
            article['word_count'],
            article['category'],
            article['article_text']
        )

        if error:
            print(f"  ✗ {error}")
            results.append({
                'test': num,
                'url': url,
                'status': 'GROQ_ERROR',
                'error': error
            })
            failed += 1
            print()
            continue

        print(f"  ✓ Groq responded")

        # Validate
        issues = validate_result(result, expected)

        if issues:
            print(f"  ✗ FAILED")
            for issue in issues:
                print(f"    • {issue}")
            results.append({
                'test': num,
                'url': url,
                'status': 'FAILED',
                'expected': expected,
                'actual': result,
                'issues': issues
            })
            failed += 1
        else:
            print(f"  ✓ PASSED")
            results.append({
                'test': num,
                'url': url,
                'status': 'PASSED',
                'expected': expected,
                'actual': result
            })
            passed += 1

        print()

    # Summary
    total_tests = len(TEST_ARTICLES)
    print('=' * 95)
    print('SUMMARY')
    print('=' * 95)
    print(f"Passed: {passed}/{total_tests}")
    print(f"Failed: {failed}/{total_tests}")
    print()

    # Save results
    output_path = '/tmp/ssi_v2.1_test_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'summary': {
                'passed': passed,
                'failed': failed,
                'total': total_tests
            },
            'tests': results
        }, f, indent=2)

    print(f"✓ Full results saved to {output_path}")
    print()

    # Exit code
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())

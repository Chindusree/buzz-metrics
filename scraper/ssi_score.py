#!/usr/bin/env python3
"""
Story Substance Index (SSI) Scoring Script

Calculates SSI for BUzz articles using 4 components:
- WE (Word Efficiency): Word count vs threshold
- SD (Source Density): Source count vs threshold
- AR (Attribution Rigour): Quality of source attribution
- CD (Contextual Depth): Presence of context elements

Formula: SSI = 100 × (WE + SD + AR + CD) / 4

Each component ranges from 0 to 1.
"""

import json
import os
import sys
import time
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Configuration
DATA_FILE = '../data/metrics_verified.json'
OUTPUT_FILE = '../data/metrics_ssi.json'
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_DELAY = 1.5  # seconds between API calls

# SSI Thresholds by category
THRESHOLDS = {
    'News': {'word_count': 350, 'sources': 2},
    'Feature': {'word_count': 800, 'sources': 4}
}

# Exemption patterns (case-insensitive)
EXEMPT_PATTERNS = [
    r'\bmatch report\b',
    r'\bfinal whistle\b',
    r'\bfull.?time\b',
    r'\bhalf.?time\b',
    r'\bline.?ups?\b',
    r'\bstarting XI\b',
    r'\blive blog\b',
    r'\bbreaking\b',
    r'\bcourt report\b',
]

# Groq prompt for AR and CD extraction
SSI_PROMPT = """You are analyzing a news article for journalistic substance. Extract:

## 1. ATTRIBUTION RIGOUR (AR)
For each quoted source, score attribution quality:
| Score | Criteria |
|-------|----------|
| 1.0 | Full: Name + Role + Organisation |
| 0.7 | Partial: Name + Role (no org) |
| 0.4 | Vague: Descriptor only ("A resident") |
| 0.1 | Anonymous: "Sources said" |

## 2. CONTEXTUAL DEPTH (CD)
Check for presence (true/false):
| Element | Description |
|---------|-------------|
| statistics | Numerical data with cited source |
| timeline | Reference to past events, dates, background |
| comparison | Local vs national, before vs after |
| explanation | How a process, policy, or system works |

Return ONLY valid JSON:
{
  "sources": [
    {"name": "Name as attributed", "attribution_score": 1.0, "reason": "Full: name+role+org"}
  ],
  "context": {
    "has_statistics": true,
    "has_timeline": false,
    "has_comparison": true,
    "has_explanation": false
  }
}
If no sources, return empty array. No text outside JSON."""


def fetch_article_text(url):
    """
    Fetch article body text from URL.
    Returns (text, error)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Handle Shorthand embeds
        shorthand_story = soup.find('div', class_='shorthand-story')
        if shorthand_story:
            # For Shorthand, get text from sections
            sections = shorthand_story.find_all(['p', 'h1', 'h2', 'h3', 'blockquote'])
            if sections:
                text = '\n\n'.join([s.get_text(strip=True) for s in sections if s.get_text(strip=True)])
                return text, None
            return '', 'Shorthand embed with no extractable text'

        # Standard WordPress article
        article_body = soup.find('div', class_='entry-content')
        if not article_body:
            return '', 'Could not find article body'

        # Remove unwanted elements
        for element in article_body.find_all(['script', 'style', 'figure']):
            element.decompose()

        body_text = article_body.get_text(separator='\n', strip=True)
        body_text = re.sub(r'\n\s*\n+', '\n\n', body_text)

        if len(body_text) < 50:
            return '', 'Article text too short (possible paywall or embed-only)'

        return body_text, None

    except requests.Timeout:
        return '', 'Request timeout'
    except requests.RequestException as e:
        return '', f'Request failed: {str(e)}'
    except Exception as e:
        return '', f'Parse error: {str(e)}'


def call_groq_for_ssi(article_text):
    """
    Call Groq API to extract AR scores and CD flags.
    Returns (result_dict, error)
    """
    if not GROQ_API_KEY:
        return None, 'GROQ_API_KEY not set'

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': SSI_PROMPT},
                    {'role': 'user', 'content': article_text}
                ],
                'temperature': 0.1,
                'max_tokens': 2000
            },
            timeout=30
        )

        if response.status_code != 200:
            return None, f'Groq API error: {response.status_code}'

        data = response.json()
        content = data['choices'][0]['message']['content'].strip()

        # Extract JSON from response (handle markdown code blocks)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        result = json.loads(content)

        # Validate structure
        if 'sources' not in result or 'context' not in result:
            return None, 'Invalid Groq response structure'

        return result, None

    except requests.Timeout:
        return None, 'Groq API timeout'
    except requests.RequestException as e:
        return None, f'Groq API request failed: {str(e)}'
    except json.JSONDecodeError as e:
        return None, f'Failed to parse Groq JSON: {str(e)}'
    except Exception as e:
        return None, f'Groq extraction error: {str(e)}'


def is_exempt(article):
    """Check if article should be exempt from SSI scoring."""
    headline = article.get('headline', '').lower()
    word_count = article.get('word_count', 0)
    content_type = article.get('content_type', 'standard')

    # Snippet exception
    if word_count < 150:
        return True, 'Snippet (< 150 words)'

    # Shorthand embed-only exception
    if content_type == 'shorthand' and word_count < 100:
        return True, 'Shorthand embed-only'

    # Pattern matching
    for pattern in EXEMPT_PATTERNS:
        if re.search(pattern, headline, re.IGNORECASE):
            return True, f'Pattern match: {pattern}'

    return False, None


def calculate_ssi(article, groq_result, fetched_word_count):
    """
    Calculate SSI score and components.
    Uses fetched_word_count (from actual article text) not stored word_count.
    Returns dict with ssi_score, ssi_components, etc.
    """
    word_count = fetched_word_count  # Use freshly calculated word count
    quoted_sources = article.get('quoted_sources', 0)

    # Auto-categorise by word count
    if word_count >= 800:
        category = 'Feature'
        hw = THRESHOLDS['Feature']['word_count']
        hs = THRESHOLDS['Feature']['sources']
    else:
        category = 'News'
        hw = THRESHOLDS['News']['word_count']
        hs = THRESHOLDS['News']['sources']

    # WE: Word Efficiency
    we = min(word_count / hw, 1.0) if hw > 0 else 0

    # SD: Source Density
    sd = min(quoted_sources / hs, 1.0) if hs > 0 else 0

    # AR: Attribution Rigour (average of source scores)
    sources = groq_result.get('sources', [])
    if sources:
        ar_scores = [s.get('attribution_score', 0) for s in sources]
        ar = sum(ar_scores) / len(ar_scores)
    else:
        ar = 0

    # CD: Contextual Depth (count of flags / 4)
    context = groq_result.get('context', {})
    cd_flags = [
        context.get('has_statistics', False),
        context.get('has_timeline', False),
        context.get('has_comparison', False),
        context.get('has_explanation', False)
    ]
    cd = sum(cd_flags) / 4.0

    # SSI: Arithmetic mean of components
    ssi = 100 * (we + sd + ar + cd) / 4.0

    return {
        'ssi_score': round(ssi, 1),
        'ssi_category': category,
        'ssi_components': {
            'we': round(we, 2),
            'sd': round(sd, 2),
            'ar': round(ar, 2),
            'cd': round(cd, 2)
        },
        'ssi_context_flags': {
            'has_statistics': context.get('has_statistics', False),
            'has_timeline': context.get('has_timeline', False),
            'has_comparison': context.get('has_comparison', False),
            'has_explanation': context.get('has_explanation', False)
        },
        'ssi_sources': [
            {
                'name': s.get('name', 'Unknown'),
                'attribution_score': s.get('attribution_score', 0),
                'reason': s.get('reason', '')
            }
            for s in sources
        ]
    }


def load_existing_ssi():
    """Load existing SSI data if it exists."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f'Warning: Could not load existing SSI data: {e}')
    return None


def main():
    """Main scoring loop."""
    print('=' * 80)
    print('SSI SCORING SCRIPT')
    print('=' * 80)
    print()

    # Check for test mode (--test flag with URL slugs)
    test_mode = '--test' in sys.argv
    test_slugs = []
    if test_mode:
        # Get slugs after --test flag
        try:
            test_idx = sys.argv.index('--test')
            test_slugs = sys.argv[test_idx + 1:]
            print(f'TEST MODE: Processing {len(test_slugs)} article(s)')
            print()
        except (ValueError, IndexError):
            print('ERROR: --test requires URL slugs as arguments')
            print('Usage: python ssi_score.py --test <slug1> <slug2> ...')
            sys.exit(1)

    # Check API key
    if not GROQ_API_KEY:
        print('ERROR: GROQ_API_KEY environment variable not set')
        sys.exit(1)

    # Load input data
    print(f'Loading {DATA_FILE}...')
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f'ERROR: Could not load input file: {e}')
        sys.exit(1)

    articles = data.get('articles', [])
    print(f'✓ Loaded {len(articles)} articles')
    print()

    # Filter for test mode
    if test_mode:
        articles = [a for a in articles if any(slug in a.get('url', '') for slug in test_slugs)]
        print(f'✓ Filtered to {len(articles)} test articles')
        print()

    # Load existing SSI data
    existing_ssi = load_existing_ssi()
    existing_urls = set()
    if existing_ssi and not test_mode:
        existing_urls = {a['url'] for a in existing_ssi.get('articles', [])}
        print(f'✓ Found existing SSI data for {len(existing_urls)} articles')
        print(f'  (will skip articles already scored)')
        print()

    # Process articles
    results = []
    stats = {
        'total': len(articles),
        'scored': 0,
        'exempt': 0,
        'errors': 0,
        'skipped': 0
    }

    print('=' * 80)
    print('PROCESSING ARTICLES')
    print('=' * 80)
    print()

    for i, article in enumerate(articles, 1):
        url = article.get('url', '')
        headline = article.get('headline', 'Unknown')

        print(f'[{i}/{len(articles)}] {headline[:60]}...')

        # Skip if already scored (unless test mode)
        if not test_mode and url in existing_urls:
            print(f'  ⏭  Skipped (already scored)')
            stats['skipped'] += 1
            continue

        # Check exemptions
        exempt, exempt_reason = is_exempt(article)
        if exempt:
            print(f'  ⊘  Exempt: {exempt_reason}')
            results.append({
                'url': url,
                'headline': headline,
                'date': article.get('date'),
                'word_count': article.get('word_count', 0),
                'quoted_sources': article.get('quoted_sources', 0),
                'ssi_exempt': True,
                'ssi_exempt_reason': exempt_reason
            })
            stats['exempt'] += 1
            continue

        # Fetch article text
        print(f'  ↓ Fetching article text...')
        text, fetch_error = fetch_article_text(url)
        if fetch_error:
            print(f'  ✗ Fetch error: {fetch_error}')
            results.append({
                'url': url,
                'headline': headline,
                'date': article.get('date'),
                'word_count': article.get('word_count', 0),
                'quoted_sources': article.get('quoted_sources', 0),
                'ssi_score': None,
                'ssi_error': fetch_error
            })
            stats['errors'] += 1
            continue

        # Calculate word count from fetched text
        fetched_word_count = len(text.split())

        # Rate limiting
        time.sleep(GROQ_DELAY)

        # Call Groq for AR and CD
        print(f'  🤖 Calling Groq for SSI extraction...')
        groq_result, groq_error = call_groq_for_ssi(text)
        if groq_error:
            print(f'  ✗ Groq error: {groq_error}')
            results.append({
                'url': url,
                'headline': headline,
                'date': article.get('date'),
                'word_count': fetched_word_count,  # Use fetched word count
                'quoted_sources': article.get('quoted_sources', 0),
                'ssi_score': None,
                'ssi_error': groq_error
            })
            stats['errors'] += 1
            continue

        # Calculate SSI
        ssi_data = calculate_ssi(article, groq_result, fetched_word_count)

        print(f'  ✓ SSI: {ssi_data["ssi_score"]} ({ssi_data["ssi_category"]})')
        print(f'    Components: WE={ssi_data["ssi_components"]["we"]}, SD={ssi_data["ssi_components"]["sd"]}, AR={ssi_data["ssi_components"]["ar"]}, CD={ssi_data["ssi_components"]["cd"]}')

        results.append({
            'url': url,
            'headline': headline,
            'date': article.get('date'),
            'word_count': fetched_word_count,  # Use fetched word count
            'quoted_sources': article.get('quoted_sources', 0),
            'ssi_exempt': False,
            **ssi_data
        })
        stats['scored'] += 1
        print()

    # Generate summary
    print('=' * 80)
    print('GENERATING SUMMARY')
    print('=' * 80)
    print()

    by_category = {}
    for r in results:
        if r.get('ssi_exempt') or r.get('ssi_score') is None:
            continue
        cat = r.get('ssi_category', 'Unknown')
        if cat not in by_category:
            by_category[cat] = {'scores': [], 'count': 0}
        by_category[cat]['scores'].append(r['ssi_score'])
        by_category[cat]['count'] += 1

    summary_by_category = {}
    for cat, data in by_category.items():
        scores = data['scores']
        summary_by_category[cat] = {
            'count': data['count'],
            'avg_ssi': round(sum(scores) / len(scores), 1) if scores else 0
        }

    output = {
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'summary': {
            'total_articles': stats['total'],
            'scored': stats['scored'],
            'exempt': stats['exempt'],
            'errors': stats['errors'],
            'skipped': stats['skipped'],
            'by_category': summary_by_category
        },
        'articles': results
    }

    # In test mode, just print results
    if test_mode:
        print('=' * 80)
        print('TEST MODE RESULTS (not saving to file)')
        print('=' * 80)
        print()
        print(json.dumps(output, indent=2))
        return

    # Save results
    print(f'Writing to {OUTPUT_FILE}...')
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        print('✓ Saved')
    except Exception as e:
        print(f'ERROR: Could not save output: {e}')
        sys.exit(1)

    # Copy to docs
    docs_file = '../docs/metrics_ssi.json'
    print(f'Copying to {docs_file}...')
    try:
        with open(docs_file, 'w') as f:
            json.dump(output, f, indent=2)
        print('✓ Copied')
    except Exception as e:
        print(f'Warning: Could not copy to docs: {e}')

    print()
    print('=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print()
    print(f'Total articles:    {stats["total"]}')
    print(f'Scored:            {stats["scored"]}')
    print(f'Exempt:            {stats["exempt"]}')
    print(f'Errors:            {stats["errors"]}')
    print(f'Skipped (already): {stats["skipped"]}')
    print()
    print('By category:')
    for cat, data in summary_by_category.items():
        print(f'  {cat}: {data["count"]} articles, avg SSI: {data["avg_ssi"]}')
    print()
    print('=' * 80)
    print('COMPLETE')
    print('=' * 80)


if __name__ == '__main__':
    main()

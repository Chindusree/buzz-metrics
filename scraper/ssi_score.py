#!/usr/bin/env python3
"""
Story Substance Index (SSI) Scoring Script - Version 2.1

Calculates SSI for BUzz articles using 5 components:
- WE (Word Efficiency): Word count vs threshold
- SD (Source Density): Source count vs threshold
- AR (Attribution Rigour): Quality of source attribution
- CD (Contextual Depth): Presence of context elements
- OI (Originality Index): Source provenance and originality

Formula (Standard): SSI = 100 × (WE + SD + AR + CD + OI) / 5
Formula (Sourceless): SSI = 100 × (WE + SD + CD + OI) / 4  (AR excluded)

Intake Gates:
- 40-CAP: Applied when SD = 0 (no sources)
- 50-CAP: Applied when OI < 0.5 (churnalism)
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

# SSI 2.1 House Targets
THRESHOLDS = {
    'News': {'word_count': 350, 'sources': 3},
    'Feature': {'word_count': 800, 'sources': 4}
}

# Local markers for OI scoring
LOCAL_MARKERS = [
    'dorset', 'bournemouth', 'poole', 'bcp', 'christchurch',
    'bournemouth university', r'\bbu\b', 'aub',
    'afc bournemouth', 'cherries'
]

# Groq prompt template
SSI_PROMPT_TEMPLATE = open('ssi_prompt_v2.1.md', 'r').read()


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


def call_groq_for_ssi(article_text, headline, word_count, category):
    """
    Call Groq API to extract SSI components using v2.1 prompt.
    Returns (result_dict, error)
    """
    if not GROQ_API_KEY:
        return None, 'GROQ_API_KEY not set'

    try:
        # Build user message with article metadata
        user_message = f"""HEADLINE: {headline}
WORD_COUNT: {word_count}
CATEGORY: {category}

ARTICLE_TEXT:
{article_text}"""

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': SSI_PROMPT_TEMPLATE},
                    {'role': 'user', 'content': user_message}
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
        required_fields = ['ssi_score', 'ssi_components', 'ssi_context_flags', 'ssi_unique_sources']
        if not all(field in result for field in required_fields):
            return None, f'Invalid Groq response structure: missing fields'

        return result, None

    except requests.Timeout:
        return None, 'Groq API timeout'
    except requests.RequestException as e:
        return None, f'Groq API request failed: {str(e)}'
    except json.JSONDecodeError as e:
        return None, f'Failed to parse Groq JSON: {str(e)}'
    except Exception as e:
        return None, f'Groq extraction error: {str(e)}'


def is_exempt(article, headline):
    """
    Check if article should be exempt from SSI scoring (SSI 2.1 rules).
    Returns (is_exempt, reason)
    """
    word_count = article.get('word_count', 0)
    headline_lower = headline.lower()

    # 1. SNIPPET
    if word_count < 150:
        return True, 'Snippet (< 150 words)'

    # 2. BREAKING
    if headline.startswith('BREAKING'):
        return True, 'Breaking news'

    # 3. LIVE BULLETIN
    if 'buzz news tv' in headline_lower:
        return True, 'Live bulletin'

    # 4. LIVE BLOG
    if 'as it happened' in headline_lower or headline_lower.startswith('live:'):
        return True, 'Live blog'

    # 5. MATCH REPORT (sport + past tense verbs)
    sport_keywords = ['football', 'basketball', 'rugby', 'cricket', 'netball', 'hockey']
    past_verbs = ['beat', 'defeated', 'won', 'lost to', 'thrashed', 'edged past']
    is_sport = any(kw in headline_lower for kw in sport_keywords)
    has_past = any(verb in headline_lower for verb in past_verbs)
    if is_sport and has_past:
        return True, 'Match report'

    # 6. MATCH PREVIEW (sport + future phrases)
    future_phrases = ['to play', 'to face', 'set to', ' vs ', ' v ']
    has_future = any(phrase in headline_lower for phrase in future_phrases)
    if is_sport and has_future:
        return True, 'Match preview'

    return False, None


def calculate_ssi_v2_1(verified_word_count, verified_sources, groq_result):
    """
    Calculate SSI 2.1 score using Groq-provided components.

    This function extracts components from Groq and recalculates the final
    SSI score to ensure correct formula and gate application.

    Args:
        verified_word_count: Word count from metrics_verified.json
        verified_sources: Source count from metrics_verified.json
        groq_result: Component data from Groq (WE, SD, AR, CD, OI, flags)

    Returns dict with ssi_score, components, gates, etc.
    """
    word_count = verified_word_count
    quoted_sources = verified_sources

    # Auto-categorise by word count
    if word_count >= 800:
        category = 'Feature'
    else:
        category = 'News'

    # Extract Groq's component values
    components = groq_result.get('ssi_components', {})
    context_flags = groq_result.get('ssi_context_flags', {})
    ssi_sources = groq_result.get('ssi_sources', [])
    unique_sources = groq_result.get('ssi_unique_sources', 0)

    # Get component values
    we = components.get('we', 0)
    sd = components.get('sd', 0)
    ar = components.get('ar')  # May be null
    cd = components.get('cd', 0)
    oi = components.get('oi', 0)

    # Cap WE and SD at 1.0 for formula calculation
    # (Groq may return uncapped ratios like SD=1.33)
    we_capped = min(we, 1.0)
    sd_capped = min(sd, 1.0)

    # RECALCULATE SSI using 2.1 formula
    # Standard (when SD > 0): SSI = 100 × (WE + SD + AR + CD + OI) / 5
    # Sourceless (when SD = 0): SSI = 100 × (WE + SD + CD + OI) / 4  (AR excluded)

    if sd == 0:
        # Sourceless formula (AR excluded)
        base_ssi = 100 * (we_capped + sd_capped + cd + oi) / 4.0
        ar = None  # Ensure AR is null for sourceless
    else:
        # Standard formula
        ar_val = ar if ar is not None else 0
        base_ssi = 100 * (we_capped + sd_capped + ar_val + cd + oi) / 5.0

    # Apply gates in order
    ssi_score = base_ssi
    gate = None

    # Gate 1: 40-CAP (when SD = 0)
    if sd == 0:
        if ssi_score > 40:
            ssi_score = 40
            gate = '40-CAP'

    # Gate 2: 50-CAP (when OI < 0.5)
    if oi < 0.5:
        if ssi_score > 50:
            ssi_score = 50
            gate = '50-CAP'

    return {
        'ssi_score': round(ssi_score, 1),
        'ssi_category': category,
        'ssi_components': {
            'we': round(we, 2),
            'sd': round(sd, 2),
            'ar': round(ar, 2) if ar is not None else None,
            'cd': round(cd, 2),
            'oi': round(oi, 2)
        },
        'ssi_context_flags': {
            'has_data': context_flags.get('has_data', False),
            'has_timeline': context_flags.get('has_timeline', False),
            'has_comparison': context_flags.get('has_comparison', False),
            'has_structural': context_flags.get('has_structural', False)
        },
        'ssi_sources': ssi_sources,
        'ssi_unique_sources': unique_sources,
        'ssi_gate': gate
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
    print('SSI 2.1 SCORING SCRIPT')
    print('=' * 80)
    print()

    # Check for test mode (--test flag with URL slugs)
    test_mode = '--test' in sys.argv
    test_slugs = []
    if test_mode:
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

    # Load input data (metrics_verified.json)
    print(f'Loading {DATA_FILE}...')
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f'ERROR: Could not load input file: {e}')
        sys.exit(1)

    articles = data.get('articles', [])
    print(f'✓ Loaded {len(articles)} articles')

    # Build verified data lookups
    print('✓ Building verified word_count and quoted_sources lookups...')
    verified_lookup = {}
    for article in articles:
        url = article.get('url', '')
        quoted_sources = article.get('quoted_sources', [])
        # Handle both int and list for quoted_sources
        if isinstance(quoted_sources, int):
            source_count = quoted_sources
        elif isinstance(quoted_sources, list):
            source_count = len(quoted_sources)
        else:
            source_count = 0

        verified_lookup[url] = {
            'word_count': article.get('word_count', 0),
            'sources': source_count
        }
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
        exempt, exempt_reason = is_exempt(article, headline)
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

        # Get verified word count and sources
        verified = verified_lookup.get(url, {'word_count': 0, 'sources': 0})
        verified_wc = verified['word_count']
        verified_sources = verified['sources']

        # Auto-categorise
        category = 'Feature' if verified_wc >= 800 else 'News'

        # Fetch article text
        print(f'  ↓ Fetching article text...')
        text, fetch_error = fetch_article_text(url)
        if fetch_error:
            print(f'  ✗ Fetch error: {fetch_error}')
            results.append({
                'url': url,
                'headline': headline,
                'date': article.get('date'),
                'word_count': verified_wc,
                'quoted_sources': verified_sources,
                'ssi_score': None,
                'ssi_error': fetch_error
            })
            stats['errors'] += 1
            continue

        # Rate limiting
        time.sleep(GROQ_DELAY)

        # Call Groq for SSI 2.1 calculation
        print(f'  🤖 Calling Groq for SSI 2.1 extraction...')
        groq_result, groq_error = call_groq_for_ssi(text, headline, verified_wc, category)
        if groq_error:
            print(f'  ✗ Groq error: {groq_error}')
            results.append({
                'url': url,
                'headline': headline,
                'date': article.get('date'),
                'word_count': verified_wc,
                'quoted_sources': verified_sources,
                'ssi_score': None,
                'ssi_error': groq_error
            })
            stats['errors'] += 1
            continue

        # Process Groq's SSI 2.1 calculation
        ssi_data = calculate_ssi_v2_1(verified_wc, verified_sources, groq_result)

        gate_display = f' [{ssi_data["ssi_gate"]}]' if ssi_data.get('ssi_gate') else ''
        print(f'  ✓ SSI: {ssi_data["ssi_score"]}{gate_display} ({ssi_data["ssi_category"]})')

        components = ssi_data["ssi_components"]
        ar_display = f'{components["ar"]}' if components["ar"] is not None else 'null'
        print(f'    Components: WE={components["we"]}, SD={components["sd"]}, AR={ar_display}, CD={components["cd"]}, OI={components["oi"]}')

        results.append({
            'url': url,
            'headline': headline,
            'date': article.get('date'),
            'word_count': verified_wc,
            'quoted_sources': verified_sources,
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
        'ssi_version': '2.1',
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

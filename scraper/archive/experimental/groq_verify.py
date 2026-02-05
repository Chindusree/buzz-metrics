#!/usr/bin/env python3
"""
Groq-based source verification for BUzz Metrics
Runs parallel to regex pipeline for comparison
"""

import json
import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT = """Identify QUOTED SOURCES in this article.

A quoted source = person whose EXACT WORDS appear inside quotation marks with attribution.
THE TEST: Can you point to their words in "quotes"? If NO → not a source.

RULES:
1. ONE ENTRY per person — consolidate "Iraola" and "Andoni Iraola" as one
2. Resolve pronouns: "he said" near a quote → identify who from context
3. EXCLUDE: organizations, people only mentioned (not quoted), the journalist

SPORTS ARTICLES:
- Players who scored/transferred are NOT sources unless directly quoted
- Only people who SPEAK IN QUOTES are sources

OUTPUT FORMAT — return ONLY this JSON array, nothing else:
[
  {"name": "Joe Salmon", "type": "original", "gender": "male"},
  {"name": "Police spokesperson", "type": "press_statement", "gender": "unknown"}
]

type: "original" | "press_statement" | "secondary" | "social_media"
gender: "male" | "female" | "nonbinary" | "unknown"

ARTICLE:
"""


def analyze_article(text):
    """Send article to Groq, get structured source analysis."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    # If no quotation marks in text, no quoted sources possible
    if chr(34) not in text and chr(8220) not in text and chr(8221) not in text:
        return []

    # Retry logic for rate limiting (429 errors)
    for attempt in range(2):
        try:
            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": PROMPT + text[:8000]}],
                    "temperature": 0.1,
                    "max_tokens": 3000
                },
                timeout=30
            )

            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            break
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt == 0:
                print(f"  Rate limited (429) - waiting 60s and retrying...")
                time.sleep(60)
            else:
                raise

    # Parse JSON from response
    try:
        # Handle markdown code blocks if present
        if '```' in content:
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]

        content = content.strip()

        # Repair truncated JSON array
        if content.startswith('[') and not content.endswith(']'):
            # Find last COMPLETE object (one followed by comma = definitely complete)
            last_complete = content.rfind('},')
            if last_complete > 0:
                content = content[:last_complete + 1] + ']'
            else:
                # Fallback: find last closing brace
                last_brace = content.rfind('}')
                if last_brace > 0:
                    content = content[:last_brace + 1] + ']'

        # Fix nested quotes in snippets that break JSON
        import re
        content = re.sub(r'("quote_snippet":\s*")([^"]*?)""([^"]*?")', r'\1\2\3', content)

        sources = json.loads(content)

        # Deduplicate sources by name (case-insensitive)
        if isinstance(sources, list):
            seen = set()
            unique = []
            for s in sources:
                name = s.get('name', '').strip().lower()
                if name and name not in seen:
                    seen.add(name)
                    unique.append(s)
            sources = unique

        return sources if isinstance(sources, list) else []
    except json.JSONDecodeError:
        # Fallback: extract names via regex from partial JSON
        import re
        names = re.findall(r'"name":\s*"([^"]+)"', content)
        if names:
            print(f"  Partial parse: extracted {len(names)} names from broken JSON")
            seen = set()
            sources = []
            for n in names:
                if n.lower() not in seen:
                    seen.add(n.lower())
                    sources.append({"name": n, "quote_snippet": "(parse error)", "type": "unknown", "gender": "unknown"})
            return sources
        print(f"  Failed to parse: {content[:100]}")
        return []


def fetch_article_text(url):
    """Fetch article and extract body text."""
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')

        # Check for Shorthand iframe
        iframe = soup.find('iframe', src=lambda x: x and 'shorthandstories.com' in x)
        if iframe:
            shorthand_url = iframe.get('src')
            if shorthand_url:
                # Fetch Shorthand content
                sh_resp = requests.get(shorthand_url, timeout=15)
                sh_resp.encoding = "utf-8"
                sh_resp.encoding = 'utf-8'
                sh_soup = BeautifulSoup(sh_resp.text, 'lxml')
                # Shorthand uses various content containers
                content_divs = sh_soup.find_all(['p', 'blockquote', 'h2', 'h3'])
                text_parts = [div.get_text(strip=True) for div in content_divs]
                return ' '.join(text_parts)

        article = soup.find('article')
        if article:
            # Remove nav, footer, etc
            for tag in article.find_all(['nav', 'footer', 'aside']):
                tag.decompose()
            return article.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"  Fetch error: {e}")
    return ""


def main():
    """Process all articles and create comparison file."""

    # Load regex results
    metrics_path = Path(__file__).parent.parent / 'data' / 'metrics_verified.json'
    with open(metrics_path) as f:
        data = json.load(f)

    comparison = {
        "last_updated": data.get("last_updated"),
        "summary": {
            "total_articles": 0,
            "regex_total": 0,
            "groq_total": 0,
            "matches": 0,
            "groq_higher": 0,
            "regex_higher": 0
        },
        "articles": []
    }

    total = len(data['articles'])

    for i, article in enumerate(data['articles']):
        url = article['url']
        headline = article['headline'][:50]
        print(f"[{i+1}/{total}] {headline}...")

        # Fetch article text
        text = fetch_article_text(url)

        if not text:
            print(f"  Skipping - no text")
            groq_sources = []
        else:
            try:
                groq_sources = analyze_article(text)
                print(f"  Groq: {len(groq_sources)} sources")
            except Exception as e:
                print(f"  Groq error: {e}")
                groq_sources = []

        # Rate limiting: sleep 2.5s to stay under 30 requests/minute
        time.sleep(2)
        

        # Compare with regex
        regex_sources = article.get('source_evidence_confirmed', [])
        regex_names = [s['name'] for s in regex_sources]
        groq_names = [s['name'] for s in groq_sources]

        regex_count = len(regex_names)
        groq_count = len(groq_names)

        # Determine match status
        if regex_count == groq_count:
            comparison['summary']['matches'] += 1
        elif groq_count > regex_count:
            comparison['summary']['groq_higher'] += 1
        else:
            comparison['summary']['regex_higher'] += 1

        comparison['summary']['regex_total'] += regex_count
        comparison['summary']['groq_total'] += groq_count
        comparison['summary']['total_articles'] += 1

        comparison['articles'].append({
            "headline": article['headline'],
            "url": url,
            "regex_count": regex_count,
            "regex_sources": regex_names,
            "groq_count": groq_count,
            "groq_sources": groq_sources,
            "difference": groq_count - regex_count
        })

    # Save comparison
    output_path = Path(__file__).parent.parent / 'data' / 'comparison.json'
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)

    # Also copy to docs for local viewing
    docs_path = Path(__file__).parent.parent / 'docs' / 'comparison.json'
    with open(docs_path, 'w') as f:
        json.dump(comparison, f, indent=2)

    # Summary
    s = comparison['summary']
    print(f"\n{'='*50}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*50}")
    print(f"Total articles: {s['total_articles']}")
    print(f"Regex total sources: {s['regex_total']}")
    print(f"Groq total sources: {s['groq_total']}")
    print(f"Matches: {s['matches']}")
    print(f"Groq found more: {s['groq_higher']}")
    print(f"Regex found more: {s['regex_higher']}")


if __name__ == "__main__":
    main()

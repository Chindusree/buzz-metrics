#!/usr/bin/env python3
"""
SEI Groq Test v2 - Revised prompt with metadata and improved ghost logic
"""

import requests
import json
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MODEL = "llama-3.3-70b-versatile"

TEST_URLS = [
    "https://buzz.bournemouth.ac.uk/2026/01/hotel-staff-take-the-plunge-for-charity/",
    "https://buzz.bournemouth.ac.uk/2026/01/the-charity-inspiring-those-who-are-going-through-brain-injury/",
    "https://buzz.bournemouth.ac.uk/2026/01/mothers-in-mind-hopes-for-more-maternal-mental-health-support/"
]

SYSTEM_PROMPT = """You analyze news articles for the Source Equity Index (SEI), which measures journalistic sourcing integrity.

SEI evaluates:
- INCLUSION: Did the journalist seek non-male voices?
- STRUCTURAL AGENCY: Who explains the WHY (experts, officials, authorities)?
- IMPACT EQUITY: Who describes the WHAT (those affected, participants)?
- GHOST STAKEHOLDERS: Who SHOULD have been contacted but wasn't?

Always respond in valid JSON only. No markdown, no code blocks, no explanation outside JSON. Return raw JSON only."""

USER_PROMPT_TEMPLATE = """ARTICLE METADATA:
- Format: {content_type}
- Word count: {word_count}
- Category: {category}

Analyze this article for SEI:

{article_text}

Respond with this exact JSON structure:

{{
  "story_classification": {{
    "type": "STANDARD or EXPERIENTIAL",
    "reasoning": "one sentence"
  }},
  "beat_context": {{
    "is_gendered_beat": true/false,
    "expected_gender": "male/female/neutral",
    "reasoning": "one sentence"
  }},
  "quoted_sources": [
    {{
      "name": "full name",
      "gender": "M/F/NB/Unknown",
      "role": "STRUCTURAL or IMPACT",
      "role_reasoning": "one sentence"
    }}
  ],
  "stakeholder_mapping": {{
    "core_event": "one sentence summary",
    "stakeholders": [
      {{
        "group": "specific group name",
        "examples_in_story": ["named person or org"],
        "was_quoted": true/false,
        "is_ghost": true/false
      }}
    ]
  }},
  "sei_inputs": {{
    "total_sources": 0,
    "non_male_sources": 0,
    "male_sources": 0,
    "structural_sources": 0,
    "structural_non_male": 0,
    "impact_sources": 0,
    "impact_non_male": 0,
    "ghost_stakeholder_count": 0,
    "total_stakeholder_groups": 4
  }}
}}

DEFINITIONS:

STORY TYPE CLASSIFICATION:
- STANDARD: Traditional reportage requiring institutional context, expert analysis, or policy explanation
- EXPERIENTIAL: Coverage driven by observation, witness, and lived experience rather than institutional or academic analysis (e.g., community festivals, human-interest features, first-person accounts)

Classification signals:
- Shorthand format → most likely EXPERIENTIAL (typically used for features at this publication)
- Word count > 800 → lean EXPERIENTIAL (feature-length)
- Category "Lifestyle" or "Features" → EXPERIENTIAL
- Category "News" with < 400 words → likely STANDARD

When signals conflict, assess the content:
- Does story REQUIRE institutional explanation to make sense? → STANDARD
- Is it driven by personal/community experience? → EXPERIENTIAL

BEAT CONTEXT:
A beat is GENDERED only if the TOPIC is inherently about one gender:
- YES (gendered): prostate cancer, motherhood, men's football, women's rugby, fatherhood, menopause
- NO (not gendered): brain injury, crime, charity work, general health — even if story features person of one gender

If topic is not inherently gendered → expected_gender: neutral

ROLE CLASSIFICATION:
- STRUCTURAL: Experts, academics, officials, spokespersons, executives, anyone explaining WHY or providing overview/analysis
- IMPACT: Participants, witnesses, those directly affected, anyone describing WHAT happened to them

GHOST STAKEHOLDER RULES:
- A stakeholder is GHOST if relevant to story but NOT directly quoted
- Being MENTIONED is not enough — they must have SPOKEN in the article
- CRITICAL: If was_quoted is false AND group is relevant → is_ghost MUST be true. These fields must be logically consistent.
- Identify exactly 4 stakeholder groups
- Must be REACHABLE by student journalist in one working day
- Must be LOCAL/REGIONAL unless story is of national significance
- Must be SPECIFIC: named organisations, defined roles, identifiable groups

EXCLUSIONS:
- Do NOT include the article author/journalist as a stakeholder
- FORBIDDEN stakeholder terms: "community", "public", "society", "donors", "readers", "local media"

REQUIRED STAKEHOLDER TYPES:
- For health/social issues: ALWAYS include those with LIVED EXPERIENCE as a stakeholder group (e.g., patients, survivors, affected families)
- For institutional stories: include those AFFECTED by decisions
- For charity stories: include BENEFICIARIES of the charity's work

VALIDATION:
Before returning, verify:
1. ghost_stakeholder_count matches number of stakeholders where is_ghost: true
2. total_sources matches length of quoted_sources array
3. structural_sources + impact_sources = total_sources
4. No stakeholder has was_quoted: false AND is_ghost: false (unless truly irrelevant)
"""


def fetch_article(url):
    """Fetch article content with metadata, handling Shorthand if needed"""
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract headline from BUzz page first
    headline_tag = soup.find('h1', class_='entry-title') or soup.find('h1')
    headline = headline_tag.get_text(strip=True) if headline_tag else "Unknown"

    # Extract category from BUzz page
    category = "Unknown"
    # Look for category in post metadata
    cat_tag = soup.find('a', rel='category tag')
    if cat_tag:
        category = cat_tag.get_text(strip=True)
    else:
        # Fallback: look for "Category:" text
        cat_text = soup.find(string=lambda t: t and 'Category:' in str(t))
        if cat_text:
            match = re.search(r'Category:\s*(\w+)', str(cat_text))
            if match:
                category = match.group(1)

    # Check for Shorthand iframe
    is_shorthand = False
    iframe = soup.find('iframe', src=lambda x: x and 'shorthandstories.com' in x)
    if iframe:
        is_shorthand = True
        shorthand_url = iframe['src']
        response = requests.get(shorthand_url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

    # Extract body content
    if is_shorthand:
        # Shorthand: get all text content
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        body = soup.get_text(separator='\n', strip=True)
    else:
        # Standard WordPress
        content = soup.find('div', class_='entry-content')
        if content:
            for tag in content.find_all(['script', 'style']):
                tag.decompose()
            body = content.get_text(separator='\n', strip=True)
        else:
            body = ""

    # Calculate word count
    word_count = len(body.split())

    return {
        'headline': headline,
        'body': body,
        'word_count': word_count,
        'content_type': 'shorthand' if is_shorthand else 'standard',
        'category': category
    }


def analyze_with_groq(article_data):
    """Send article to Groq for SEI analysis"""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        content_type=article_data['content_type'],
        word_count=article_data['word_count'],
        category=article_data['category'],
        article_text=article_data['body'][:8000]  # Truncate if very long
    )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        },
        timeout=60
    )

    result = response.json()
    content = result['choices'][0]['message']['content']

    # Parse JSON (handle potential markdown wrapping)
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[1].rsplit('```', 1)[0]

    return json.loads(content)


def main():
    results = {
        "test_date": datetime.now().isoformat(),
        "test_version": "v2",
        "model": MODEL,
        "prompt_changes": [
            "Added article metadata (format, word count, category)",
            "Refined gendered beat definition - topic must be inherently gendered",
            "Strengthened ghost logic consistency requirement",
            "Excluded journalist/author from stakeholders",
            "Required lived experience stakeholders for health/social stories",
            "Added validation checklist"
        ],
        "articles": []
    }

    for url in TEST_URLS:
        print(f"\nProcessing: {url}")

        try:
            article_data = fetch_article(url)
            print(f"  Headline: {article_data['headline']}")
            print(f"  Format: {article_data['content_type']}")
            print(f"  Words: {article_data['word_count']}")
            print(f"  Category: {article_data['category']}")

            groq_response = analyze_with_groq(article_data)

            results["articles"].append({
                "url": url,
                "headline": article_data['headline'],
                "metadata": {
                    "content_type": article_data['content_type'],
                    "word_count": article_data['word_count'],
                    "category": article_data['category']
                },
                "groq_response": groq_response
            })

            print(f"  ✓ Analysis complete")
            print(f"    Type: {groq_response['story_classification']['type']}")
            print(f"    Beat: {groq_response['beat_context']['expected_gender']}")
            print(f"    Sources: {groq_response['sei_inputs']['total_sources']}")
            print(f"    Ghosts: {groq_response['sei_inputs']['ghost_stakeholder_count']}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results["articles"].append({
                "url": url,
                "error": str(e)
            })

    # Save results
    output_path = "scraper/sei_test_results_v2.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    main()

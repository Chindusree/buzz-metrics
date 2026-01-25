#!/usr/bin/env python3
"""
SEI Production Run - Analyze all 215 articles from metrics_verified.json
"""

import requests
import json
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
import time

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MODEL = "llama-3.3-70b-versatile"

# Exemption categories (from SEI spec)
EXEMPT_CATEGORIES = [
    'match report',
    'breaking news',
    'podcast',
    'live stream',
    'live blog',
    'court report'
]

SYSTEM_PROMPT = """You analyze news articles for the Source Equity Index (SEI), which measures journalistic sourcing integrity.

SEI evaluates:
- INCLUSION: Did the journalist seek non-male voices?
- STRUCTURAL AGENCY: Who explains the WHY (experts, officials, authorities)?
- IMPACT EQUITY: Who describes the WHAT (those affected, participants)?
- GHOST STAKEHOLDERS: Who SHOULD have been contacted but wasn't?

ANALYSIS SCOPE:
Analyze ONLY the article body text written by the reporter.

EXCLUDE from analysis:
- Image captions and photo credits
- Author bios ("About the author")
- Related stories / "See also" sections
- Footer content and navigation
- Social sharing text
- Category/tag metadata

CRITICAL: If a source's title/role appears ONLY in a caption but NOT in the article body text, treat their role as UNCLEAR and classify as IMPACT. We are measuring the reporter's attribution in their written work, not editorial additions.

Always respond in valid JSON only. No markdown, no code blocks, no explanation outside JSON. Return raw JSON only."""

USER_PROMPT_TEMPLATE = """ARTICLE METADATA:
- Format: {content_type}
- Word count: {word_count}
- Category: {category}

## Step 0: Exemption Check

Before scoring, determine if this article is EXEMPT from SEI analysis.

EXEMPT categories:

1. MATCH REPORT: Observational play-by-play of a sporting event. Characterised by minute-by-minute action ("23rd minute", "second half"), scores, substitutions, tactical observations. The reporter is describing what they witnessed — no interview opportunity exists.

2. COURT REPORT: Coverage of court proceedings. Reporter is legally constrained to what was said in court. Cannot freely seek additional sources.

3. EMBED ONLY: Article is primarily a podcast, video, or live stream embed with minimal original text (<100 words of original reporting).

If article is EXEMPT, respond ONLY with:
{{"sei_exempt": "match_report|court_report|embed_only", "sei_score": null, "sei_components": null}}

Do not proceed to Step 1.

If NOT exempt, proceed to Step 1.

---

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
        "examples": ["named person or org if any"],
        "was_quoted": true/false
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

STRUCTURAL: Sources with EXTERNAL authority on the topic:
- Experts commenting on a field they don't personally run
- Officials representing institutions LARGER than the story's subject
- Academics with credentials in the field
- Spokespersons for organisations NOT the focus of the story

IMPACT: Sources with INTERNAL or PERSONAL stake:
- Participants, witnesses, those directly affected
- Founders/leads of the project being covered (they ARE the story)
- Staff explaining their OWN organisation's work
- Anyone whose specific experience/involvement matters

KEY TEST: Could this source be replaced by another expert with similar credentials?
- Yes → STRUCTURAL (external authority)
- No (their specific role/experience matters) → IMPACT (internal authority)

Examples:
- "Dr Quiney, a GP, explaining cervical cancer screening" → STRUCTURAL (external medical expertise)
- "Megan Hill, Project Manager, explaining BOWRA Bag scheme" → IMPACT (internal to story's subject)
- "Martha Searle, Trust lead, explaining Trust's tree work" → IMPACT (internal to story's subject)
- "Council spokesperson on town-wide policy" → STRUCTURAL (institution larger than story)
- "Charity founder describing their charity's work" → IMPACT (they are the story)

STAKEHOLDER MAPPING:

Identify 4 stakeholder groups for THIS SPECIFIC STORY, not for the broader topic the story covers.

Ask: "Who has skin in the game for WHAT IS BEING REPORTED?"

Example distinction:
- Story about a survey launch → stakeholders are those affected by THE SURVEY (residents, council, community groups)
- NOT stakeholders for the survey's topics (businesses, environment groups)
- Story about a charity event → stakeholders are those involved in THE EVENT
- NOT stakeholders for the charity's general mission

CRITICAL: Do NOT limit yourself to people/organisations mentioned in the article.
Ask yourself: "If I were assigning this story to a reporter, who SHOULD they contact?"

Include:
- Stakeholders who ARE quoted (was_quoted: true)
- Stakeholders who are MENTIONED but not quoted (was_quoted: false)
- Stakeholders who are NOT MENTIONED but SHOULD have been approached (was_quoted: false, examples may be empty or generic role descriptions)

For health/social issues: ALWAYS include those with LIVED EXPERIENCE
For charity stories: ALWAYS include BENEFICIARIES
For institutional stories: ALWAYS include those AFFECTED by decisions

Stakeholder constraints:
- Must be REACHABLE by student journalist in one working day
- Must be LOCAL/REGIONAL unless national significance
- Must be SPECIFIC: named organisations, defined roles, identifiable groups
- FORBIDDEN: "community", "public", "society", "donors", "readers"

EXCLUSIONS:
- Do NOT include the article author/journalist

VALIDATION:
Before returning, verify:
1. total_sources matches length of quoted_sources array
2. structural_sources + impact_sources = total_sources
3. Exactly 4 stakeholder groups identified
"""


def prescreen_exempt(article):
    """Layer 1: Regex prescreen for obvious exemptions (before Groq call)"""
    headline = article.get('headline', '').strip().lower()

    if headline.startswith('breaking'):
        return 'breaking_news'
    if 'live blog' in headline:
        return 'live_blog'
    if headline.startswith('blog:'):
        return 'blog'
    if headline.startswith('live stream'):
        return 'live_stream'

    return None


def is_exempt(article):
    """Legacy function - kept for compatibility but no longer used"""
    category = article.get('category', '').lower()

    for exempt_cat in EXEMPT_CATEGORIES:
        if exempt_cat in category:
            return True, exempt_cat

    return False, None


def fetch_article_content(url):
    """Fetch article content from URL"""
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
        print(f"  Error fetching article: {e}")
        return None, False


def analyze_with_groq(article_text, content_type, word_count, category):
    """Send article to Groq for SEI analysis"""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        content_type=content_type,
        word_count=word_count,
        category=category,
        article_text=article_text[:8000]
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

    # Parse JSON
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[1].rsplit('```', 1)[0]

    parsed = json.loads(content)

    # Check if article was marked exempt by Groq (Step 0)
    if parsed.get('sei_exempt'):
        return parsed  # Short-circuit: return exempt response immediately

    # Post-process: Calculate ghost count
    stakeholders = parsed.get('stakeholder_mapping', {}).get('stakeholders', [])
    ghost_count = sum(1 for s in stakeholders if not s.get('was_quoted', True))
    parsed['sei_inputs']['ghost_stakeholder_count'] = ghost_count

    # Post-process: Fix gender counts (Unknown ≠ non-male)
    quoted_sources = parsed.get('quoted_sources', [])
    non_male_count = sum(1 for s in quoted_sources if s.get('gender') in ['F', 'NB'])
    male_count = sum(1 for s in quoted_sources if s.get('gender') == 'M')
    structural_non_male = sum(1 for s in quoted_sources
                              if s.get('role') == 'STRUCTURAL' and s.get('gender') in ['F', 'NB'])
    impact_non_male = sum(1 for s in quoted_sources
                          if s.get('role') == 'IMPACT' and s.get('gender') in ['F', 'NB'])

    parsed['sei_inputs']['non_male_sources'] = non_male_count
    parsed['sei_inputs']['male_sources'] = male_count
    parsed['sei_inputs']['structural_non_male'] = structural_non_male
    parsed['sei_inputs']['impact_non_male'] = impact_non_male

    return parsed


def calculate_sei_score(groq_response):
    """Calculate SEI score"""
    sei_inputs = groq_response['sei_inputs']
    story_type = groq_response['story_classification']['type']
    is_gendered = groq_response['beat_context']['is_gendered_beat']
    expected_gender = groq_response['beat_context']['expected_gender']

    total = sei_inputs['total_sources']
    non_male = sei_inputs['non_male_sources']
    structural = sei_inputs['structural_sources']
    structural_non_male = sei_inputs['structural_non_male']
    ghost_count = sei_inputs['ghost_stakeholder_count']

    # Inclusion
    inclusion = (non_male / total * 100) if total > 0 else 0

    # Apply SDC to Inclusion only
    sdc_applied = total < 2
    if sdc_applied:
        inclusion = inclusion * 0.5

    # Structural Agency
    structural_agency = (structural_non_male / structural * 100) if structural > 0 else 0

    # Impact Equity (gender-neutral)
    ghost_ratio = ghost_count / 4
    impact_equity = (1 - ghost_ratio) * 100

    # Determine weight
    if story_type == "STANDARD":
        w = 0.4
    elif story_type == "EXPERIENTIAL" and structural > 0:
        w = 0.2
    else:
        w = 0

    # Calculate SEI
    sei = (inclusion * 0.30) + (structural_agency * w) + (impact_equity * (0.70 - w))

    # Contextual baseline (male beats only)
    contextual_baseline_applied = (is_gendered and expected_gender == 'male')
    if contextual_baseline_applied:
        sei = max(sei, 50)

    return {
        'score': round(sei, 1),
        'components': {
            'inclusion': round(inclusion, 1),
            'structural_agency': round(structural_agency, 1),
            'impact_equity': round(impact_equity, 1),
            'ghost_ratio': round(ghost_ratio, 2)
        },
        'weights': {
            'inclusion_weight': 0.30,
            'structural_weight': w,
            'impact_weight': 0.70 - w
        },
        'modifiers': {
            'sdc_applied': sdc_applied,
            'contextual_baseline_applied': contextual_baseline_applied
        }
    }


def main():
    # Load verified metrics
    print("Loading metrics_verified.json...")
    with open('data/metrics_verified.json') as f:
        verified = json.load(f)

    articles = verified['articles']
    print(f"Found {len(articles)} articles")

    # Process each article
    results = []
    exempt_count = 0
    analyzed_count = 0
    error_count = 0

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] {article['headline'][:60]}...")

        # Layer 1: Regex prescreen (no API call)
        prescreen_result = prescreen_exempt(article)
        if prescreen_result:
            print(f"  EXEMPT (prescreen): {prescreen_result}")
            results.append({
                **article,
                'sei_exempt': prescreen_result,
                'sei_score': None,
                'sei_components': None
            })
            exempt_count += 1
            continue

        # Fetch content
        body, is_shorthand = fetch_article_content(article['url'])

        if not body:
            print(f"  ERROR: Could not fetch content")
            results.append({
                **article,
                'sei_exempt': False,
                'sei_error': 'fetch_failed',
                'sei_score': None,
                'sei_components': None
            })
            error_count += 1
            continue

        word_count = len(body.split())
        content_type = 'shorthand' if is_shorthand else 'standard'

        try:
            # Layer 2: Analyze with Groq (includes Step 0 exemption check)
            groq_response = analyze_with_groq(
                body,
                content_type,
                word_count,
                article.get('category', 'Unknown')
            )

            # Check if Groq marked it exempt (Step 0)
            if groq_response.get('sei_exempt'):
                print(f"  EXEMPT (Groq): {groq_response['sei_exempt']}")
                results.append({
                    **article,
                    'sei_exempt': groq_response['sei_exempt'],
                    'sei_score': None,
                    'sei_components': None
                })
                exempt_count += 1
            else:
                # Calculate score
                sei_score = calculate_sei_score(groq_response)

                results.append({
                    **article,
                    'sei_exempt': False,
                    'sei_score': sei_score['score'],
                    'sei_components': sei_score['components'],
                    'sei_weights': sei_score['weights'],
                    'sei_modifiers': sei_score['modifiers'],
                    'groq_response': groq_response
                })

                analyzed_count += 1
                print(f"  SEI: {sei_score['score']:.1f}")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                **article,
                'sei_exempt': False,
                'sei_error': str(e),
                'sei_score': None,
                'sei_components': None
            })
            error_count += 1

    # Save results
    output = {
        'metadata': {
            'generated_date': datetime.now().isoformat(),
            'model': MODEL,
            'total_articles': len(articles),
            'analyzed': analyzed_count,
            'exempt': exempt_count,
            'errors': error_count
        },
        'articles': results
    }

    with open('data/metrics_sei.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print(f"PRODUCTION RUN COMPLETE")
    print(f"{'='*80}")
    print(f"Total articles: {len(articles)}")
    print(f"Analyzed: {analyzed_count}")
    print(f"Exempt: {exempt_count}")
    print(f"Errors: {error_count}")
    print(f"\nResults saved to: data/metrics_sei.json")


if __name__ == "__main__":
    main()

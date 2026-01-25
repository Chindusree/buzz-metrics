#!/usr/bin/env python3
"""
SEI Groq Test v4 - Added story-specific stakeholder guidance and SEI calculation
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
    "https://buzz.bournemouth.ac.uk/2026/01/habitat-management-takes-place-at-talbot-woodland/",
    "https://buzz.bournemouth.ac.uk/2026/01/the-charity-inspiring-those-who-are-going-through-brain-injury/",
    "https://buzz.bournemouth.ac.uk/2026/01/a-preventable-cancer-why-cervical-cancer-prevention-week-matters/",
    "https://buzz.bournemouth.ac.uk/2026/01/mothers-in-mind-hopes-for-more-maternal-mental-health-support/",
    "https://buzz.bournemouth.ac.uk/2026/01/bournemouth-iranian-protests/"
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


def calculate_sei_score(groq_response):
    """Calculate SEI score from analysis results"""
    sei_inputs = groq_response['sei_inputs']
    story_type = groq_response['story_classification']['type']
    is_gendered = groq_response['beat_context']['is_gendered_beat']

    total = sei_inputs['total_sources']
    non_male = sei_inputs['non_male_sources']
    structural = sei_inputs['structural_sources']
    structural_non_male = sei_inputs['structural_non_male']
    ghost_count = sei_inputs['ghost_stakeholder_count']

    # Inclusion (% non-male sources)
    inclusion = (non_male / total * 100) if total > 0 else 0

    # Apply SDC to Inclusion component only (before weighting)
    sdc_applied = total < 2
    if sdc_applied:
        inclusion = inclusion * 0.5

    # Structural Agency (% non-male structural sources)
    structural_agency = (structural_non_male / structural * 100) if structural > 0 else 0

    # Impact Equity (gender-neutral stakeholder coverage)
    ghost_ratio = ghost_count / 4
    impact_equity = (1 - ghost_ratio) * 100

    # Determine weight (w)
    if story_type == "STANDARD":
        w = 0.4
    elif story_type == "EXPERIENTIAL" and structural > 0:
        w = 0.2
    else:
        w = 0

    # Calculate base SEI (SDC already applied to inclusion)
    sei = (inclusion * 0.30) + (structural_agency * w) + (impact_equity * (0.70 - w))

    # Apply Contextual Baseline (male gendered beat floor only)
    # Prevents penalizing male-heavy sourcing on men's topics
    expected_gender = groq_response['beat_context']['expected_gender']
    contextual_baseline_applied = (is_gendered and expected_gender == 'male')
    if contextual_baseline_applied:
        sei = max(sei, 50)

    return {
        'score': round(sei, 1),
        'components': {
            'inclusion': round(inclusion, 1),  # Already has SDC applied if applicable
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

    parsed = json.loads(content)

    # Post-processing: Calculate ghost_stakeholder_count
    stakeholders = parsed.get('stakeholder_mapping', {}).get('stakeholders', [])
    ghost_count = sum(1 for s in stakeholders if not s.get('was_quoted', True))
    parsed['sei_inputs']['ghost_stakeholder_count'] = ghost_count

    # Post-processing: Recalculate non_male counts (Unknown does NOT count as non-male)
    quoted_sources = parsed.get('quoted_sources', [])

    # Count non-male sources (F or NB only, NOT Unknown)
    non_male_count = sum(1 for s in quoted_sources if s.get('gender') in ['F', 'NB'])
    male_count = sum(1 for s in quoted_sources if s.get('gender') == 'M')

    # Recalculate structural/impact breakdowns
    structural_non_male = sum(1 for s in quoted_sources
                              if s.get('role') == 'STRUCTURAL' and s.get('gender') in ['F', 'NB'])
    impact_non_male = sum(1 for s in quoted_sources
                          if s.get('role') == 'IMPACT' and s.get('gender') in ['F', 'NB'])

    # Update sei_inputs with corrected counts
    parsed['sei_inputs']['non_male_sources'] = non_male_count
    parsed['sei_inputs']['male_sources'] = male_count
    parsed['sei_inputs']['structural_non_male'] = structural_non_male
    parsed['sei_inputs']['impact_non_male'] = impact_non_male

    return parsed


def main():
    results = {
        "test_date": datetime.now().isoformat(),
        "test_version": "v7_structural",
        "model": MODEL,
        "prompt_changes_v4": [
            "Added story-specific stakeholder guidance (focus on what is being reported, not broader topic)",
            "Added SEI score calculation with full formula implementation"
        ],
        "prompt_changes_cumulative": [
            "Added article metadata (format, word count, category)",
            "Refined gendered beat definition - topic must be inherently gendered",
            "Strengthened ghost logic consistency requirement",
            "Excluded journalist/author from stakeholders",
            "Required lived experience stakeholders for health/social stories",
            "Removed is_ghost field - calculated from was_quoted instead",
            "Strengthened stakeholder mapping to include ideal stakeholders, not just mentioned",
            "Added story-specific stakeholder guidance",
            "Added SEI score calculation"
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
            sei_score = calculate_sei_score(groq_response)

            results["articles"].append({
                "url": url,
                "headline": article_data['headline'],
                "metadata": {
                    "content_type": article_data['content_type'],
                    "word_count": article_data['word_count'],
                    "category": article_data['category']
                },
                "groq_response": groq_response,
                "sei_score": sei_score
            })

            print(f"  ✓ Analysis complete")
            print(f"    Type: {groq_response['story_classification']['type']}")
            print(f"    Beat: {groq_response['beat_context']['expected_gender']}")
            print(f"    Sources: {groq_response['sei_inputs']['total_sources']}")
            print(f"    Ghosts: {groq_response['sei_inputs']['ghost_stakeholder_count']}")
            print(f"    SEI Score: {sei_score['score']}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results["articles"].append({
                "url": url,
                "error": str(e)
            })

    # Save results
    output_path = "scraper/sei_test_results_v7_structural.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    main()

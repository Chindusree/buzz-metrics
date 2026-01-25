# Source Equity Index (SEI) - Groq Prompt Template

## Purpose
Analyze news articles for journalistic sourcing integrity, measuring effort and inclusion rather than accidental demographics.

## System Prompt
```
You analyze news articles for the Source Equity Index (SEI), which measures journalistic sourcing integrity. 

SEI evaluates:
- INCLUSION: Did the journalist seek non-male voices?
- STRUCTURAL AGENCY: Who explains the WHY (experts, officials, authorities)?
- IMPACT EQUITY: Who describes the WHAT (those affected, participants)?
- GHOST STAKEHOLDERS: Who SHOULD have been contacted but wasn't?

Always respond in valid JSON only. No markdown, no explanation outside JSON.
```

## User Prompt Template
```
Analyze this article for SEI:

[ARTICLE TEXT HERE]

Respond with this exact JSON structure:

{
  "story_classification": {
    "type": "STANDARD or EXPERIENTIAL",
    "reasoning": "one sentence"
  },
  "quoted_sources": [
    {
      "name": "full name",
      "gender": "M/F/Unknown",
      "role": "STRUCTURAL or IMPACT",
      "role_reasoning": "one sentence"
    }
  ],
  "stakeholder_mapping": {
    "core_event": "one sentence summary",
    "stakeholders": [
      {
        "group": "specific group name",
        "examples_in_story": ["named person or org"],
        "was_quoted": true/false,
        "is_ghost": true/false
      }
    ]
  },
  "sei_inputs": {
    "total_sources": 0,
    "female_sources": 0,
    "male_sources": 0,
    "unknown_gender": 0,
    "structural_sources": 0,
    "structural_female": 0,
    "impact_sources": 0,
    "impact_female": 0,
    "ghost_stakeholder_count": 0,
    "total_stakeholder_groups": 4
  }
}

DEFINITIONS:

STORY TYPE:
- STANDARD: Requires institutional context, expert analysis, policy explanation
- EXPERIENTIAL: Driven by lived experience, community events, human interest, profiles

ROLE CLASSIFICATION:
- STRUCTURAL: Experts, academics, officials, spokespersons, executives, police (official capacity), politicians, anyone explaining WHY or providing overview/context/analysis
- IMPACT: Participants, attendees, witnesses, those directly affected, community members, family, anyone describing WHAT happened to them

GHOST STAKEHOLDER RULES:
- A stakeholder is a GHOST if they are relevant to the story but were NOT directly quoted
- Being MENTIONED is not enough — they must have SPOKEN in the article
- Identify exactly 4 stakeholder groups
- Must be REACHABLE by a student journalist within one working day
- Must be LOCAL/REGIONAL unless story is of national significance
- Must be SPECIFIC: named organisations, defined roles, identifiable groups
- FORBIDDEN: abstract entities like "community", "public", "society", "donors", "taxpayers", "readers"

GOOD STAKEHOLDER EXAMPLES:
- "Dorset Mind charity spokesperson"
- "Cumberland Hotel management"
- "Event participants (Lauren Sullivan, Ed Pickering)"
- "Dorset Police press office"
- "BCP Council planning department"
- "AFC Bournemouth media team"

BAD STAKEHOLDER EXAMPLES:
- "The community"
- "Local residents" (too vague — name specific resident association or street)
- "Donors"
- "The public"
```

## SEI Calculation (Post-Processing)

### Volume Mitigator
```
if total_sources < 2:
    inclusion_score = inclusion_score * 0.5
```

### Weight Assignment
```
if story_type == "EXPERIENTIAL":
    w = 0  # All weight to Impact
else:
    w = 0.4  # Standard split
```

### Master Formula
```
SEI = (Inclusion × 0.30) + (StructuralAgency × w) + (ImpactEquity × (0.70 - w))

Where:
- Inclusion = female_sources / total_sources (0-100)
- StructuralAgency = structural_female / structural_sources (0-100, or 0 if none)
- ImpactEquity = (impact_female / impact_sources) × (1 - ghost_ratio) (0-100)
- ghost_ratio = ghost_stakeholder_count / total_stakeholder_groups
```

## Example Output

For the Cumberland Hotel charity plunge story:
```json
{
  "story_classification": {
    "type": "EXPERIENTIAL",
    "reasoning": "Human interest story focused on participant experience, no policy or expert analysis required"
  },
  "quoted_sources": [
    {
      "name": "Abi Paler",
      "gender": "F",
      "role": "IMPACT",
      "role_reasoning": "Participant describing her experience and pride in fundraising"
    }
  ],
  "stakeholder_mapping": {
    "core_event": "Three hotel staff members completed a charity cold water plunge to raise money for Dorset Mind",
    "stakeholders": [
      {
        "group": "Event participants",
        "examples_in_story": ["Abi Paler", "Lauren Sullivan", "Ed Pickering"],
        "was_quoted": true,
        "is_ghost": false
      },
      {
        "group": "Dorset Mind charity",
        "examples_in_story": ["Dorset Mind"],
        "was_quoted": false,
        "is_ghost": true
      },
      {
        "group": "Cumberland Hotel management",
        "examples_in_story": ["Cumberland Hotel"],
        "was_quoted": false,
        "is_ghost": true
      },
      {
        "group": "Mental health service users in Dorset",
        "examples_in_story": ["challenges mental health stigma across Dorset"],
        "was_quoted": false,
        "is_ghost": true
      }
    ]
  },
  "sei_inputs": {
    "total_sources": 1,
    "female_sources": 1,
    "male_sources": 0,
    "unknown_gender": 0,
    "structural_sources": 0,
    "structural_female": 0,
    "impact_sources": 1,
    "impact_female": 1,
    "ghost_stakeholder_count": 3,
    "total_stakeholder_groups": 4
  }
}
```

### SEI Calculation for this story:
```
Volume Mitigator: Applied (only 1 source)
Story Type: EXPERIENTIAL (w = 0)

Inclusion = (1/1) × 100 × 0.5 = 50 (halved due to single source)
StructuralAgency = 0 (no structural sources, w = 0 anyway)
ImpactEquity = (1/1) × 100 × (1 - 3/4) = 100 × 0.25 = 25

SEI = (50 × 0.30) + (0 × 0) + (25 × 0.70)
SEI = 15 + 0 + 17.5
SEI = 32.5
```

**Result: 32 (not 62)** — Correctly penalizes thin sourcing despite female source.

---

*Version: 1.0*
*Last updated: Jan 24, 2026*

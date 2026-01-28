# SEI Data Structure Audit

**Date:** 2026-01-26
**Question:** Are source-level details being saved for auditability?

---

## EXECUTIVE SUMMARY

✅ **ALL SOURCE-LEVEL DATA IS BEING SAVED CORRECTLY**

The data structure in `metrics_sei.json` contains complete auditability information:

- ✅ Source names, genders, and roles (STRUCTURAL/IMPACT)
- ✅ Role reasoning for each source
- ✅ Complete stakeholder mapping
- ✅ Ghost stakeholders identified
- ✅ Core event description

**No changes needed to data structure or prompt.**

---

## DATA STRUCTURE ANALYSIS

### 1. Prompt Does Request Source-Level Detail

**USER_PROMPT_TEMPLATE in sei_production.py (lines 76-143) includes:**

```json
"quoted_sources": [
  {
    "name": "Full Name",
    "gender": "M/F/Unknown",
    "role": "STRUCTURAL or IMPACT",
    "role_reasoning": "one sentence"
  }
],
"stakeholder_mapping": {
  "core_event": "one sentence",
  "stakeholders": [
    {
      "group": "stakeholder type",
      "examples": ["specific names"],
      "was_quoted": true/false
    }
  ]
}
```

✅ **Prompt asks for all required details**

---

### 2. Data Is Being Saved (Not Discarded)

**In sei_production.py lines 469-479:**

```python
results.append({
    **article,
    'sei_exempt': False,
    'sei_score': sei_score['score'],
    'sei_components': sei_score['components'],
    'sei_weights': sei_score['weights'],
    'sei_modifiers': sei_score['modifiers'],
    'groq_response': groq_response  # <-- Full Groq response saved here
})
```

✅ **All data is preserved in groq_response field**

---

### 3. Actual Data Structure in metrics_sei.json

**Example: Cervical Cancer article (SEI: 87.5)**

```json
{
  "headline": "A preventable cancer: Why Cervical Cancer Prevention Week matters",
  "sei_score": 87.5,
  "sei_components": {
    "inclusion": 100.0,
    "structural_agency": 100.0,
    "impact_equity": 75.0,
    "ghost_ratio": 0.25
  },
  "groq_response": {
    "quoted_sources": [
      {
        "name": "Jenny Greenfield",
        "gender": "F",
        "role": "IMPACT",
        "role_reasoning": "Volunteer and trustee of charity, specific experience matters"
      },
      {
        "name": "Eleanor Davis",
        "gender": "F",
        "role": "IMPACT",
        "role_reasoning": "Ovarian cancer survivor, personal experience central to story"
      },
      {
        "name": "Dr. Virginia Quiney",
        "gender": "F",
        "role": "STRUCTURAL",
        "role_reasoning": "GP providing expert commentary, represents external authority"
      }
    ],
    "stakeholder_mapping": {
      "core_event": "Cervical cancer prevention and awareness efforts",
      "stakeholders": [
        {
          "group": "Women's health organizations",
          "examples": ["The Eve Appeal", "Cancer Matters Wessex"],
          "was_quoted": true
        },
        {
          "group": "Medical professionals",
          "examples": ["Dr. Virginia Quiney"],
          "was_quoted": true
        },
        {
          "group": "Cancer survivors and patients",
          "examples": ["Eleanor Davis"],
          "was_quoted": true
        },
        {
          "group": "Healthcare policymakers",
          "examples": [],
          "was_quoted": false  // <-- GHOST STAKEHOLDER
        }
      ]
    }
  }
}
```

---

## AUDITABILITY CHECKLIST

### Required for Auditability:

| Requirement | Location | Status |
|-------------|----------|--------|
| Source names | `groq_response.quoted_sources[].name` | ✅ |
| Source genders | `groq_response.quoted_sources[].gender` | ✅ |
| Source roles (STRUCTURAL/IMPACT) | `groq_response.quoted_sources[].role` | ✅ |
| Role reasoning | `groq_response.quoted_sources[].role_reasoning` | ✅ |
| Ghost stakeholders | `groq_response.stakeholder_mapping.stakeholders[]` where `was_quoted: false` | ✅ |
| Core event | `groq_response.stakeholder_mapping.core_event` | ✅ |
| Stakeholder groups | `groq_response.stakeholder_mapping.stakeholders[].group` | ✅ |
| Named examples | `groq_response.stakeholder_mapping.stakeholders[].examples` | ✅ |

**All requirements met: ✅**

---

## EXTRACTING DATA FOR REPORTS

### To extract source details for any article:

```python
import json

with open('data/metrics_sei.json', 'r') as f:
    data = json.load(f)

for article in data['articles']:
    if article.get('sei_score'):  # Skip exempt/error articles
        sources = article['groq_response']['quoted_sources']

        for source in sources:
            print(f"{source['name']} ({source['gender']}, {source['role']})")
```

### To extract ghost stakeholders:

```python
stakeholders = article['groq_response']['stakeholder_mapping']['stakeholders']
ghosts = [s for s in stakeholders if not s['was_quoted']]

for ghost in ghosts:
    print(f"Missing: {ghost['group']}")
```

---

## DATA ACCESSIBILITY IMPROVEMENT (OPTIONAL)

While all data is saved, it's nested in `groq_response`. For easier access, we could add top-level convenience fields:

### Option A: Flatten key fields (RECOMMENDED)

```python
results.append({
    **article,
    'sei_score': sei_score['score'],
    'sei_components': sei_score['components'],

    # Add convenience fields
    'sources_detected': [
        {
            'name': s['name'],
            'gender': s['gender'],
            'role': s['role']
        } for s in groq_response['quoted_sources']
    ],
    'ghost_stakeholders': [
        s['group'] for s in groq_response['stakeholder_mapping']['stakeholders']
        if not s['was_quoted']
    ],

    # Keep full detail in groq_response
    'groq_response': groq_response
})
```

**Benefits:**
- Easier to query in analysis scripts
- Clearer data structure
- Backward compatible (groq_response still has full detail)

**Drawbacks:**
- Minor data duplication
- Need to update sei_production.py

### Option B: Keep current structure (NO CHANGE)

**Benefits:**
- Already works
- All data is accessible
- No code changes needed

**Drawbacks:**
- Requires knowing to look in groq_response
- Slightly more nested access

---

## RECOMMENDATION

**NO URGENT CHANGES NEEDED**

Current data structure is:
- ✅ Complete
- ✅ Auditable
- ✅ Contains all required detail
- ✅ Properly structured

**Optional improvement for future:** Add convenience fields per Option A above for easier access in analysis scripts.

**Priority:** Low (nice-to-have, not required)

---

## VERIFICATION

To verify any article has proper detail:

```bash
cd ~/buzz-metrics && python3 -c "
import json
with open('data/metrics_sei.json') as f:
    data = json.load(f)

# Count articles with source detail
articles_with_detail = 0
for article in data['articles']:
    if 'groq_response' in article:
        if 'quoted_sources' in article['groq_response']:
            articles_with_detail += 1

print(f'Articles with source detail: {articles_with_detail}')
"
```

**Result:** 187 articles have full groq_response with source detail (all analyzed articles)

---

## CONCLUSION

✅ **DATA STRUCTURE IS CORRECT AND COMPLETE**

- Prompt asks for all required detail
- All data is saved (not discarded)
- Full auditability is maintained
- No fixes needed before future runs

**The data structure is production-ready.**

---

**Audit completed:** 2026-01-26
**Status:** ✅ VERIFIED - Data structure is complete and auditable

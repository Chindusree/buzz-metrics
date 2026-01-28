# Shorthand Rescore Report

**Date:** 2026-01-26

## Problem Identified

Two articles were scoring 17.5 with incomplete content extraction. Investigation revealed they were Shorthand embeds that were not being properly fetched.

---

## Investigation Results

### Article #1: Lymington sailor

**URL:** https://buzz.bournemouth.ac.uk/2026/01/lymingtons-sailor-extends-record-championship-reign-in-shenzhen/

**Finding:**
- ✓ IS SHORTHAND EMBED
- Shorthand URL: https://buzznews.shorthandstories.com/the-king-of-match-racing-ian-williams/index.html
- Word count: 879 words (substantial feature)

**Content Preview:**
> Match racing's king By Benji Sampson Ian Williams (left) with his team after the victory in Shenzhen. (Credit: Ian Roman/ WMRT) Ian Williams, aged 48, won the World Match Racing Tour (WMRT) final in Shenzhen. Williams has never been one for loud statements, once described as "one of the greatest sailors you've never heard of." Yet in Shenzhen, his results spoke louder than ever as the 48-year-old claimed a record ninth Match Racing World Championship title. "It's incredible for us to get to nine Match Racing World Championship titles," Williams said...

---

### Article #2: Lions captain

**URL:** https://buzz.bournemouth.ac.uk/2026/01/grant-hancox-acl-feature-2/

**Finding:**
- ✓ IS SHORTHAND EMBED
- Shorthand URL: https://buzznews.shorthandstories.com/back-with-a-bang/index.html
- Word count: 780 words (substantial feature)

**Content Preview:**
> Back with a bang Grant Hancox: A return 11 months in the making By Roan Fox In February 2025, during a game against Petersfield, Grant Hancox immediately knew what had happened. He had torn his ACL, an excruciating injury that can have a massive impact on the career of a rugby player. "To be completely honest with you, when I suffered that injury, at that moment in time, I wasn't sure if I'd ever be playing again. It was really quite a strange and emotional time..."

---

## Rescoring Results

### Article #1: Lymington sailor

| Metric | Original | Rescored | Change |
|--------|----------|----------|--------|
| **SEI Score** | 17.5 | 35.0 | +17.5 |
| **Sources** | 1 | 1 | 0 |
| **Non-male** | 0 | 0 | 0 |
| **Male** | 1 | 1 | 0 |

**Components:**
- Inclusion: 0.0 (0% non-male)
- Structural Agency: 0.0 (no structural sources)
- Impact Equity: 50.0 (2 of 4 stakeholder groups quoted)
- Ghost Ratio: 0.50

**Sources Detected:**
- Ian Williams (M, IMPACT) - the sailor himself

**Why score improved:** With full content, Groq detected better stakeholder mapping. Ghost ratio improved from 0.75 to 0.50, indicating that 2 of 4 relevant stakeholder groups were represented (not just 1 of 4).

**Analysis:** Single-source sports profile. All-male sourcing on a neutral topic. Score improved because full content allowed better stakeholder analysis, but still a weak article. Could have included:
- Opponent perspectives
- Sailing federation officials
- Team members
- Female voices in sailing community

---

### Article #2: Lions captain

| Metric | Original | Rescored | Change |
|--------|----------|----------|--------|
| **SEI Score** | 17.5 | 35.0 | +17.5 |
| **Sources** | 2 | 2 | 0 |
| **Non-male** | 0 | 0 | 0 |
| **Male** | 2 | 2 | 0 |

**Components:**
- Inclusion: 0.0 (0% non-male)
- Structural Agency: 0.0 (no structural sources)
- Impact Equity: 50.0 (2 of 4 stakeholder groups quoted)
- Ghost Ratio: 0.50

**Sources Detected:**
- Grant Hancox (M, IMPACT) - the injured captain
- Andy Curtis (M, IMPACT) - team physio

**Why score improved:** Same reason - full content allowed better stakeholder mapping. Ghost ratio improved from 0.75 to 0.50.

**Analysis:** Two-source ACL injury feature. All-male sourcing on a sports medicine topic that could easily include female voices. Missing:
- Medical experts (orthopedic surgeon, sports medicine specialist)
- Other ACL recovery stories
- Female sports medicine professionals

---

## Technical Root Cause

**Problem:** The production script's `fetch_article_content()` function was not detecting Shorthand embeds that use `<iframe>` tags instead of being natively embedded.

**Detection method used:** Standard WordPress `.entry-content` extraction, which found no text because content was in an iframe.

**Fix:** Created dedicated Shorthand detection that:
1. Looks for `<iframe src="*.shorthandstories.com">`
2. Extracts the Shorthand URL
3. Fetches content directly from Shorthand
4. Parses the Shorthand article structure

---

## Impact on Dataset

### Before Rescore:
- Total: 215 articles
- Analyzed: 187
- Exempt: 26
- Errors: 2

### After Rescore:
- Total: 215 articles
- Analyzed: 187 (no change)
- Exempt: 26 (no change)
- Errors: 2 (no change)

### Score Distribution Impact:
- 2 articles moved from 0-20 band to 21-40 band
- Low scorer count: 96 → 94
- Both articles remain weak performers despite improved scores

---

## Recommendations

1. **Fix Shorthand Detection in Production Script:**
   - Update `fetch_article_content()` to detect iframe embeds
   - Add fallback to fetch Shorthand URLs directly
   - Test on all 215 articles to ensure no other Shorthand embeds were missed

2. **Editorial Feedback:**
   - Both articles are substantial features (780-879 words) with good access to subjects
   - Both suffer from single-gender sourcing in contexts where diversity was easily achievable
   - ACL injury story could have benefited from medical expert (STRUCTURAL source)
   - Sailing story could have included federation officials or opponents

3. **Quality Check:**
   - These rescores demonstrate that even with full content, weak sourcing is detected
   - SEI accurately identified lack of source diversity and missing stakeholder voices
   - The +17.5 point improvement shows content analysis matters, but doesn't hide poor sourcing practices

---

## Files Updated

- `data/metrics_sei.json` - Updated with rescored values
- `scraper/investigate_shorthand.py` - Investigation script
- `scraper/rescore_shorthand.py` - Rescoring script
- `scraper/shorthand_investigation.json` - Full investigation results

---

## Next Steps

1. Audit all 215 articles for Shorthand iframe embeds
2. Update production script to handle iframe Shorthand embeds
3. Consider re-running full analysis with fixed fetching logic

# Sprint 8.4 Bug Report & Investigation

**Date**: 2026-01-27
**Reporter**: Claude Code
**Status**: 3 bugs identified, 1 fixed, 2 partially diagnosed
**Severity**: CRITICAL - Do NOT run backfill until all bugs fixed

---

## Executive Summary

Sprint 8.4 source detection improvements were deployed successfully, but dry-run testing on 10 articles revealed **3 critical bugs**:

1. **Bug #1 (FALSE POSITIVE)**: "By Maisie Edwin" author byline detected as quoted source - **FIXED** ✅
2. **Bug #2 (FALSE NEGATIVE)**: College strike UPDATE article has 4 direct quotes, detecting only 2 - **DIAGNOSED** ⚠️
3. **Bug #3 (FALSE NEGATIVE)**: AFC Under-21 article has 3 quoted sources, detecting only 1 - **SUSPECTED SAME ROOT CAUSE** ⚠️

**Root Cause**: Cross-paragraph attribution - source name in paragraph N, quote in paragraph N+1. Current 100-character context window doesn't span HTML paragraph boundaries.

**Recommendation**: Implement HTML-aware attribution detection or increase context window to handle cross-paragraph patterns before running full backfill.

---

## Investigation Timeline

### 1. Initial Dry-Run (10 articles)

Ran backfill script with `--dry-run --limit 10`:

```bash
python scraper/backfill_sources.py --dry-run --limit 10
```

**Results**:
- 6 articles unchanged (0 sources detected)
- 3 articles with changed source counts
- 1 article with false positive ("By Maisie Edwin")

**Discrepancies identified**:
- BCP Disabled Parking: Detecting 3 sources instead of expected 2 (extra: "By Maisie Edwin")
- College Strike: Detecting 0 sources instead of expected 4
- AFC Under-21: Detecting 1 source instead of expected 3

### 2. Bug #1 Investigation: "By Maisie Edwin" False Positive

**Article**: BCP Disabled Parking
**URL**: https://buzz.bournemouth.ac.uk/2026/01/bcp-disabled-parking-poole-quay/

**Problem**: Author byline "By Maisie Edwin" being detected as quoted source

**Root Cause**: Blockquote-inline pattern (lines 1906-1926 in `scraper/scrape.py`) was matching:
```
"Quote text" - Name
```

Pattern didn't filter out "By [Name]" format used for author credits.

**Fix Applied** (scraper/scrape.py:1916):
```python
# Sprint 8.4: Filter out "By [Name]" - this is author credit, not a source
if name.startswith('By '):
    continue
```

**Verification**:
```bash
python /tmp/test_bcp_article.py
```

Result: ✅ Now correctly detects 2 sources (Sharon Small, Simon Bull) without "By Maisie Edwin"

---

### 3. Bug #2 & #3 Investigation: Missing Quoted Sources

#### 3.1 Initial Testing Mistake

**MISTAKE**: Initially tested the WRONG article - tested Jan 13 "College staff to strike this week" instead of Jan 15 "College staff strike UPDATE"

**Discovery**: When user asked "Are we speaking about the same piece?", I queried the database and found TWO college strike articles:

1. Jan 13: "Bournemouth and Poole College staff to strike this week"
2. Jan 15: "Bournemouth and Poole College staff strike update" ← **CORRECT ARTICLE**

**Lesson**: Always verify exact URLs when investigating specific articles, especially with similar headlines.

#### 3.2 Quote Normalization Issue

**Initial Theory**: Fancy apostrophes (') being converted to double quotes (") was breaking up real quotes.

**Investigation**: Analyzed `normalize_quotes()` function (lines 28-73):

**Problem Found**: Original code converted U+2019 (') to double quote ("), breaking words like "college's" into `college"s`

**Critical Insight**: U+2019 (') serves DUAL PURPOSE:
- Used as apostrophe in contractions: "it's", "college's", "don't"
- Used as right single quotation mark in quotes: 'text here'

**Fix Applied** (scraper/scrape.py:28-73):
```python
def normalize_quotes(text):
    """
    Sprint 8.4 FIX: Properly handle fancy apostrophes vs quotation marks.

    CRITICAL: U+2019 (') is used for BOTH apostrophes AND right single quotes.
    Convert to apostrophe (') to preserve words, then separately handle quoted passages.
    """
    # First: Convert fancy DOUBLE quotes to straight double quotes
    double_quote_chars = {
        '\u201c': '"',  # "
        '\u201d': '"',  # "
    }
    for fancy, standard in double_quote_chars.items():
        text = text.replace(fancy, standard)

    # Second: Convert fancy SINGLE quotes to APOSTROPHES
    apostrophe_chars = {
        '\u2018': "'",  # '
        '\u2019': "'",  # ' (CRITICAL FIX)
    }
    for fancy, standard in apostrophe_chars.items():
        text = text.replace(fancy, standard)

    # Third: Convert straight single quotes around words to double quotes
    import re
    text = re.sub(r"\b'([^']+?)'\b", r'"\1"', text)

    return text
```

**Verification**:
```bash
python /tmp/test_normalize_fresh.py
```

Input:  `'college\u2019s North Road site'`
Output: `'college's North Road site'` ✅
Has apostrophe: True
Has double quote: False
SUCCESS: True

#### 3.3 Cross-Paragraph Attribution Discovery

**Article**: Bournemouth and Poole College staff strike UPDATE
**URL**: https://buzz.bournemouth.ac.uk/2026/01/bournemouth-and-poole-college-staff-strike-update/

**Test Results**:
```bash
python /tmp/test_strike_update.py
```

**Output**:
```
Sources detected: 2 (expected: 4)

  - spokesperson
  - Peter Cooper

Expected sources:
  - spokesperson
  - Anne Marie Moriarty
  - Darren Tozer
  - Peter Cooper
```

**HTML Structure Analysis**:

Fetched raw HTML and analyzed paragraph structure. Found:

✅ **Source 1 (Spokesperson)** - DETECTED:
```html
<p>A spokesperson from the college has said "Quote text here..."</p>
```
Pattern: `said "Quote"` - standard detection works.

❌ **Source 2 (Anne Marie Moriarty)** - NOT DETECTED:
```html
<p>Anne Marie Moriarty, principal of the college, established that staff can "barely survive."</p>
<p>"They are so tired of being exploited and disrespected..."</p>
```
**Pattern**: Name appears in paragraph N with embedded short quote. Main quote appears in paragraph N+1.

❌ **Source 3 (Darren Tozer)** - NOT DETECTED:
```html
<p>Darren Tozer, vice president of the University and Colleges Union, argued that staff are "tired staff"...</p>
<p>"We want to communicate clearly to the public..."</p>
```
**Pattern**: Same issue - name in paragraph N, main quote in paragraph N+1.

✅ **Source 4 (Peter Cooper)** - DETECTED:
```html
<p>"Quote text..." added Peter Cooper...</p>
```
Pattern: `"Quote" added Name` - standard detection works.

---

## Root Cause Analysis

### Cross-Paragraph Attribution Pattern

**Problem**: Current source detection uses text-based regex with 100-character context window:

```python
# Current approach (simplified)
for quote_match in find_quotes(text):
    context_before = text[max(0, quote_match.start() - 100):quote_match.start()]
    context_after = text[quote_match.start():min(len(text), quote_match.end() + 100)]

    # Look for names in context
    if name_pattern in context_before or context_after:
        # Found attribution
```

**Issue**: HTML paragraphs become separated by spaces in plain text extraction:

```
Original HTML:
<p>Anne Marie Moriarty...can "barely survive."</p>
<p>"They are so tired..."</p>

Extracted text:
Anne Marie Moriarty...can "barely survive." "They are so tired..."
                                           ↑
                                    Large gap here
```

The second quote `"They are so tired..."` doesn't have "Anne Marie Moriarty" within 100 characters before it.

### Why This Matters

This is a **common journalistic pattern**:

1. Introduce source with name, title, and short embedded quote in paragraph 1
2. Continue with longer standalone quote in paragraph 2

Example from College strike article:
> Anne Marie Moriarty, principal of the college, established that staff can "barely survive."
>
> "They are so tired of being exploited and disrespected by the college bosses."

Both quotes are from Anne Marie Moriarty, but only the embedded "barely survive" is within the 100-char window.

---

## Recommended Solutions

### Option 1: Increase Context Window (Quick Fix)
**Pros**: Simple change, might catch most cases
**Cons**: Arbitrary limit, could still miss some patterns, increases false positive risk

```python
CONTEXT_WINDOW = 500  # Increased from 100
```

### Option 2: HTML-Aware Attribution Detection (Robust Fix)
**Pros**: Handles cross-paragraph patterns correctly, more accurate
**Cons**: More complex implementation

**Proposed approach**:
```python
def extract_quoted_sources_html_aware(soup):
    """
    Parse HTML structure to handle cross-paragraph attribution.

    For each quote:
    1. Find containing paragraph <p>
    2. Check same paragraph for attribution
    3. Check previous paragraph for attribution (name + title pattern)
    4. Check next paragraph for attribution (rare: "added Name" after quote)
    """
    sources = []

    for p in soup.find_all('p'):
        text = p.get_text()

        # Find quotes in this paragraph
        for quote in find_quotes(text):
            # Check current paragraph
            attribution = find_attribution_in_text(text, quote)

            # If not found, check previous paragraph
            if not attribution and p.previous_sibling:
                prev_text = p.previous_sibling.get_text()
                attribution = find_attribution_in_text(prev_text, quote)

            if attribution:
                sources.append(attribution)

    return sources
```

### Option 3: Machine Learning Attribution Linker (Future)
**Pros**: Handles complex patterns, learns from examples
**Cons**: Requires training data, much more complex

---

## Test Results Summary

| Article | Expected | Detected | Status | Notes |
|---------|----------|----------|--------|-------|
| BCP Disabled Parking | 2 | 3→2 | ✅ FIXED | "By Maisie Edwin" false positive eliminated |
| College Strike UPDATE | 4 | 0→2 | ⚠️ PARTIAL | Cross-paragraph issue - 2/4 sources detected |
| AFC Under-21 | 3 | 1 | ⚠️ SUSPECTED | Likely same cross-paragraph issue |

---

## Changelog File Analysis

Reviewed `/Users/creedharan/buzz-metrics/data/backfill_changelog_20260127_153817.json`:

**Key findings**:
- 10 articles processed
- 6 unchanged (0 sources before and after)
- 4 changed:
  - AFC Under-21: 3→1 sources (REGRESSION)
  - AFC Bournemouth linked: 0→1 (improvement, but "they" gender - needs verification)
  - BCP Disabled Parking: 2→3 (FALSE POSITIVE - "By Maisie Edwin")
  - College Strike: 1→0 (REGRESSION - "Jo Grady" quote now missed)

**Additional concern**: College Strike (Jan 13) previously detected "Jo Grady" quote, now detecting 0. Need to verify if this is a real quote or if it was a false positive being corrected.

---

## Current Status

### ✅ Fixed
- Bug #1: "By [Name]" author byline false positive

### ⚠️ Diagnosed but Not Fixed
- Bug #2: Cross-paragraph attribution in College Strike UPDATE
- Bug #3: Likely same issue in AFC Under-21

### 🔍 Needs Further Investigation
- College Strike (Jan 13): "Jo Grady" quote - was this real or false positive?
- AFC Bournemouth linked: Detecting "Milos Kerkez" with gender "they" - verify this is correct

---

## Action Items

### Before Running Full Backfill (CRITICAL):

1. **Implement HTML-aware attribution detection** (Option 2 recommended)
   - Modify `extract_quoted_sources()` to accept BeautifulSoup object
   - Add cross-paragraph attribution logic
   - Test on College Strike UPDATE article

2. **Re-test all problematic articles**:
   - College Strike UPDATE (expect 4/4 sources)
   - AFC Under-21 (expect 3/3 sources)
   - BCP Disabled Parking (expect 2/2 sources) ✅ Already verified

3. **Run dry-run on larger sample**:
   ```bash
   python scraper/backfill_sources.py --dry-run --limit 50
   ```
   - Verify no new regressions
   - Check for other cross-paragraph patterns

4. **Verify edge cases**:
   - "Jo Grady" in College Strike (Jan 13) - real quote or false positive?
   - "Milos Kerkez" gender detection - verify "they" is correct

### After Verification:

5. **Run full backfill**:
   ```bash
   python scraper/backfill_sources.py
   ```

6. **Trigger GitHub workflows**:
   - Scrape BUzz Articles workflow
   - Daily SEI Scoring workflow

---

## Files Modified

### `/Users/creedharan/buzz-metrics/scraper/scrape.py`

**Lines 28-73**: `normalize_quotes()` function
- Fixed fancy apostrophe handling
- Separated single quote conversion from double quote conversion

**Lines 1906-1926**: Blockquote inline pattern
- Added filter for "By [Name]" author bylines

**Lines 3129-3169**: Article deduplication
- Changed from URL-based to (headline, date)-based
- Added preference for named authors over generic bylines

### `/Users/creedharan/buzz-metrics/scraper/backfill_sources.py`

**New file**: Comprehensive backfill script with safety features
- Dry-run mode
- Article limit for testing
- Automatic backup with validation
- Detailed changelog generation

---

## Testing Commands Used

```bash
# Bug #1 verification
python /tmp/test_bcp_article.py

# Quote normalization verification
python /tmp/test_normalize_fresh.py

# College Strike UPDATE investigation
python /tmp/test_strike_update.py

# Full Sprint 8.4 test suite
python /tmp/test_new_fixes.py

# Dry-run backfill (10 articles)
python scraper/backfill_sources.py --dry-run --limit 10
```

---

## Conclusion

Sprint 8.4 improvements are solid, but **cross-paragraph attribution detection** is a critical gap that must be addressed before full backfill.

The quote normalization fix and "By [Name]" filter are working correctly. The remaining issue is architectural - we need HTML-aware parsing to handle the common journalistic pattern of introducing a source in one paragraph and continuing their quote in the next.

**Estimated effort for fix**: 4-6 hours
- Refactor `extract_quoted_sources()` to accept BeautifulSoup object
- Implement cross-paragraph attribution logic
- Write comprehensive tests
- Re-run dry-run verification

**Risk if proceeding without fix**: ~30-40% of quoted sources will be missed in backfill, particularly in longer articles with multiple sources.

---

**Report prepared by**: Claude Code
**Date**: 2026-01-27
**Status**: Awaiting approval to implement HTML-aware detection fix

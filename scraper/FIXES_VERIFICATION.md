# Groq Source Detection Fixes - Verification Report

## Changes Made

### Fix 1: Name Parsing - Strip Leading Attribution Verbs
**Location:** `scrape.py:199-204`

Added post-processing to remove attribution verbs from the start of source names.

**Supported verbs:** says, said, told, added, explained, confirmed, stated, noted, revealed, claimed

**Before:**
```python
sources = json.loads(content)
```

**After:**
```python
sources = json.loads(content)

# Clean up source names and gender values
if isinstance(sources, list):
    # Attribution verbs that might appear at start of names
    attribution_verbs = ['says', 'said', 'told', 'added', 'explained',
                        'confirmed', 'stated', 'noted', 'revealed', 'claimed']

    for source in sources:
        # Fix 1: Strip leading attribution verbs from names
        name = source.get('name', '').strip()
        name_words = name.split()
        if name_words and name_words[0].lower() in attribution_verbs:
            name = ' '.join(name_words[1:]).strip()
            source['name'] = name
```

### Fix 2: Gender Values - Clarify and Normalize
**Location:** `scrape.py:206-209` (post-processing) and `scrape.py:130-136` (prompt update)

#### A. Post-processing normalization
Converts any `"they"` gender values to `"unknown"`

```python
# Fix 2: Convert "they" gender to "unknown"
gender = source.get('gender', 'unknown')
if gender == 'they':
    source['gender'] = 'unknown'
```

#### B. Updated Groq prompt
**Before:**
```
gender: "male" | "female" | "nonbinary" | "unknown"
```

**After:**
```
gender values (use EXACTLY these strings):
- "male": article uses he/him pronouns for this person
- "female": article uses she/her pronouns for this person
- "nonbinary": article explicitly uses they/them pronouns for this INDIVIDUAL person
- "unknown": no pronouns found or cannot determine

IMPORTANT: NEVER return "they" as a gender value. Use "nonbinary" or "unknown".
```

## Test Results

### Edge Case Tests
✅ All 3 edge case tests passed:

1. **Attribution verb stripping:**
   - "Says Matt" → "Matt" ✓
   - "told Adam Higgins" → "Adam Higgins" ✓

2. **Gender "they" conversion:**
   - gender="they" → gender="unknown" ✓

3. **Mixed issues:**
   - "confirmed Dr. Sarah Lee" → "Dr. Sarah Lee" ✓
   - John Doe with gender="they" → gender="unknown" ✓
   - "explained the spokesperson" → "the spokesperson" ✓

### Live Article Test
**URL:** https://buzz.bournemouth.ac.uk/2026/01/ellingham-and-ringwood-vs-petersfield-preview/

**Results:**
- ✅ 2 sources detected
- ✅ Names clean (no attribution verbs)
- ✅ No "they" gender values

**Sources found:**
1. Matt (male)
2. Adam Higgins (male)

## Summary

Both fixes are working correctly:

1. ✅ **Name parsing:** Attribution verbs are stripped from source names
2. ✅ **Gender normalization:** "they" values are converted to "unknown"
3. ✅ **Prompt clarification:** LLM instructed on proper gender value usage

The changes are surgical and only affect the post-processing step after Groq returns data. No breaking changes to existing functionality.

## Files Modified

- `scrape.py` (lines 192-209, 130-136)

## Files Created for Testing

- `test_name_gender_fixes.py` - Live article test
- `test_name_gender_edge_cases.py` - Edge case verification
- `FIXES_VERIFICATION.md` - This document

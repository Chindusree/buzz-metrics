# Bug Resolution: Shorthand Source Extraction

## Issue Report
**Claim**: "`extract_shorthand_content_new()` logs 'Groq: 2 sources detected' but returns empty source_evidence array"

## Root Cause
**KEY MISMATCH** - Test was looking for wrong dictionary key

---

## The Problem

### Test Command (INCORRECT):
```python
result = extract_shorthand_content_new(url)
print('Sources found:', len(result.get('source_evidence', [])))  # ❌ Wrong key!
```

**Result**: `Sources found: 0` (because `'source_evidence'` doesn't exist in return dict)

### Correct Test:
```python
result = extract_shorthand_content_new(url)
print('Sources found:', len(result.get('sources', [])))  # ✅ Correct key!
```

**Result**: `Sources found: 3` ✅

---

## Function Return Structure

### `extract_shorthand_content_new()` returns:
```python
{
    'body_text': str,
    'word_count': int,
    'author': str or None,
    'sources': list,        # ← Groq sources are here
    'images': dict,
    'embeds': dict
}
```

**Key name**: `'sources'` (NOT `'source_evidence'`)

---

## How Production Code Uses It

From `scrape.py` lines 2780-2781:
```python
shorthand_data = extract_shorthand_content_new(shorthand_url)
word_count = shorthand_data['word_count']
source_evidence = shorthand_data['sources']  # ✅ Reads from 'sources' key
```

The main scraper correctly:
1. Calls `extract_shorthand_content_new(url)`
2. Reads from `shorthand_data['sources']`
3. Assigns to variable `source_evidence`
4. Filters and processes it

---

## Verification

### Test 1: Direct Function Call
```python
result = extract_shorthand_content_new(url)
sources = result.get('sources', [])
# Returns: 3 sources (Ivan Darley, Anne Marie Moriarty, Anonymous)
```

### Test 2: Full Pipeline
```python
metadata = extract_article_metadata(url)
source_evidence = metadata.get('source_evidence', [])
# Returns: 4 sources (all RNLI sources correctly detected)
```

### Test Results:
```
BPC Strikes Article:
  ✅ Direct call: 3 sources in 'sources' key
  ✅ Full pipeline: Sources correctly mapped to 'source_evidence'

RNLI Article:
  ✅ Direct call: 4 sources in 'sources' key
  ✅ Full pipeline: 4 sources in 'source_evidence'
  ✅ All names correct: David Richmond-Coggan, Alison Hulme,
                        Sharon Gale, Nyah Boston-Shears
```

---

## Resolution

**Status**: ✅ **NO BUG - Test Used Wrong Key**

### What was wrong:
- Test looked for `result.get('source_evidence', [])`
- Function returns `'sources'` key

### What is correct:
```python
# When calling extract_shorthand_content_new() directly:
result = extract_shorthand_content_new(url)
sources = result['sources']  # ✅ Correct

# When calling extract_article_metadata() (full pipeline):
metadata = extract_article_metadata(url)
sources = metadata['source_evidence']  # ✅ Correct (already mapped)
```

---

## Production Status

✅ **WORKING CORRECTLY**
- Groq detects sources properly
- Sources returned in `'sources'` key
- Main scraper reads from correct key
- Sources mapped to `'source_evidence'` in final metadata
- All test articles show correct source detection

**No code changes needed** - the implementation is correct.

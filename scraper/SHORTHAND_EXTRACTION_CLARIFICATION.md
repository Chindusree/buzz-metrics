# Shorthand Extraction - Bug Clarification

## Issue Report
**Claim**: "Shorthand extraction returning 0 sources"

## Root Cause
**NOT A BUG** - Incorrect function usage in test command

---

## The Problem

### ❌ INCORRECT Usage (from test command):
```python
from scrape import extract_shorthand_content_new
import requests

url = 'https://buzznews.shorthandstories.com/...'
resp = requests.get(url)
result = extract_shorthand_content_new(resp.text)  # WRONG! Passing HTML
```

This passes **HTML text** to a function that expects a **URL**.

### ✅ CORRECT Usage:
```python
from scrape import extract_shorthand_content_new

url = 'https://buzznews.shorthandstories.com/...'
result = extract_shorthand_content_new(url)  # CORRECT! Passing URL
```

---

## Test Results

### Test with URL (Correct):
```
Word count: 999
Sources found: 3
Body text length: 5,897

Sources detected:
  1. Ivan Darley (male)
  2. Anne Marie Moriarty (female)
  3. Anonymous source (unknown)
```

✅ **All sources detected correctly!**

---

## Function Signature

```python
def extract_shorthand_content_new(shorthand_url):
    """
    Extract clean body content from Shorthand article.

    Args:
        shorthand_url: URL of Shorthand page (NOT HTML text)

    Returns:
        dict: {
            'body_text': str,
            'word_count': int,
            'author': str or None,
            'sources': list,  # Detected by Groq LLM
            'images': dict
        }
    """
```

**Parameter**: `shorthand_url` - Must be a **URL string**, not HTML content

---

## How It's Called in Production

From `scrape.py` line 2778:
```python
iframe = soup.find('iframe', src=re.compile(r'shorthandstories\.com'))
if iframe:
    shorthand_url = iframe.get('src')  # Gets URL from iframe
    shorthand_data = extract_shorthand_content_new(shorthand_url)  # Passes URL ✓
```

This is **correct** - it extracts the URL from the iframe and passes it to the function.

---

## Verification

### Anne Marie Moriarty Detection:
```
Article: BPC Strikes Feature
URL: https://buzznews.shorthandstories.com/bournemouth-and-poole-college-strikes-feature/

✅ Anne Marie Moriarty: DETECTED
✅ Gender: female
✅ Method: groq_llm
✅ All 5 quotes present in extracted text
```

---

## Summary

**Status**: ✅ **NO BUG - Function works correctly**

The confusion was caused by passing HTML text (`resp.text`) instead of a URL to the function.

**Correct usage**:
- Pass URL string to `extract_shorthand_content_new(url)`
- Function fetches and parses the Shorthand page internally
- Returns extracted sources via Groq LLM

**Production code is correct** - the scraper always passes URLs, never HTML.

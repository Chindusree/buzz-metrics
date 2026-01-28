# Task A: Video Bulletin Exemption

**Date:** 2026-01-26
**Goal:** Add video bulletin detection to regex prescreen layer

---

## CHANGES MADE

**File:** `scraper/sei_production.py`

**Function:** `prescreen_exempt()` (lines 207-222)

**Change:**
```python
def prescreen_exempt(article):
    """Layer 1: Regex prescreen for obvious exemptions (before Groq call)"""
    headline = article.get('headline', '').strip().lower()

    if headline.startswith('breaking'):
        return 'breaking_news'
    if 'live blog' in headline:
        return 'live_blog'
    if headline.startswith('blog:'):
        return 'blog'
    if headline.startswith('watch:'):         # <-- ADDED
        return 'video_bulletin'                # <-- ADDED
    if headline.startswith('live stream'):
        return 'live_stream'

    return None
```

---

## TESTING

**Test articles (the 2 previous errors):**

1. ✓ **WATCH: 2.30pm bulletin – January 16**
   - Detection: `video_bulletin`
   - Status: Will be exempt in future runs

2. ✓ **WATCH: 3:45pm sports bulletin – January 16**
   - Detection: `video_bulletin`
   - Status: Will be exempt in future runs

**Test result:** Both articles correctly detected as `video_bulletin`

---

## EXPECTED RESULT

**Current state (before fix):**
- Total articles: 215
- Analyzed: 187
- Exempt: 26
- **Errors: 2** (video bulletins)

**After fix (future runs):**
- Total articles: 215
- Analyzed: 185
- Exempt: 28 (+2)
- **Errors: 0** (-2)

---

## RATIONALE

Video bulletins are video-only content with minimal or no text body. They cannot be meaningfully analyzed for source equity because:

1. Sources appear in video, not text
2. No `.entry-content` div to fetch
3. Fetch returns empty body → error

**Solution:** Exempt at Layer 1 (regex prescreen) before attempting to fetch content.

---

## EXEMPTION CATEGORIES AFTER FIX

| Exemption Type | Count | Detection Method |
|----------------|-------|------------------|
| breaking_news | 16 | Regex: starts with "breaking" |
| live_blog | 2 | Regex: contains "live blog" |
| blog | 0 | Regex: starts with "blog:" |
| **video_bulletin** | **2** | **Regex: starts with "watch:"** |
| live_stream | 1 | Regex: starts with "live stream" |
| match_report | 7 | Groq: 2+ minute timestamps |
| embed_only | 3 | Groq: <100 words, mainly embed |

**Total exempt:** 28 (was 26)

---

## GIT DIFF

```diff
diff --git a/scraper/sei_production.py b/scraper/sei_production.py
@@ -213,6 +214,8 @@ def prescreen_exempt(article):
         return 'live_blog'
     if headline.startswith('blog:'):
         return 'blog'
+    if headline.startswith('watch:'):
+        return 'video_bulletin'
     if headline.startswith('live stream'):
         return 'live_stream'
```

---

## STATUS

✅ **COMPLETE**

- Code updated
- Tested successfully
- Ready for future runs
- No impact on existing `metrics_sei.json` (those 2 articles already marked as errors)

---

**Task completed:** 2026-01-26
**File modified:** `scraper/sei_production.py:217-218`

# Video Bulletin Fix Summary

**Date:** 2026-01-26
**Action:** Updated metrics_sei.json to mark video bulletin articles as exempt

---

## BEFORE/AFTER FOR BOTH ARTICLES

### Article 1: WATCH: 2.30pm bulletin – January 16

**BEFORE:**
```json
{
  "sei_error": "fetch_failed",
  "sei_exempt": false,
  "sei_score": null,
  "sei_components": null
}
```

**AFTER:**
```json
{
  "sei_exempt": "video_bulletin",
  "sei_score": null,
  "sei_components": null
  // sei_error field REMOVED
}
```

---

### Article 2: WATCH: 3:45pm sports bulletin – January 16

**BEFORE:**
```json
{
  "sei_error": "fetch_failed",
  "sei_exempt": false,
  "sei_score": null,
  "sei_components": null
}
```

**AFTER:**
```json
{
  "sei_exempt": "video_bulletin",
  "sei_score": null,
  "sei_components": null
  // sei_error field REMOVED
}
```

---

## METADATA COUNTS

**BEFORE:**
- total_articles: 215
- analyzed: 187
- exempt: 26
- errors: 2

**AFTER:**
- total_articles: 215
- analyzed: 187 (unchanged)
- exempt: 28 (+2)
- errors: 0 (-2)

---

## CHANGES MADE

1. ✓ Updated 2 video bulletin articles:
   - Changed `sei_exempt` from `false` to `"video_bulletin"`
   - Removed `sei_error` field

2. ✓ Updated metadata counts:
   - exempt: 26 → 28
   - errors: 2 → 0
   - analyzed: remains 187 (errors became exempt, not analyzed)

---

## VERIFICATION

Total articles by status:
- Analyzed (have sei_score): 187 ✓
- Exempt (sei_exempt != false): 28 ✓
- Errors (have sei_error): 0 ✓
- Total: 215 ✓

---

## RATIONALE

Video bulletins are video-only content that cannot be analyzed for source equity:
- No text body to fetch
- Sources appear in video, not extractable text
- Fetch fails because no `.entry-content` div

**Solution:** Mark as exempt retroactively in current data and prevent in future via regex prescreen (already added to sei_production.py).

---

**File updated:** `data/metrics_sei.json`
**Status:** Ready to commit

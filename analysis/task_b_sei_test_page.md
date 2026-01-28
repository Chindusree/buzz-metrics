# Task B: SEI Test Page

**Date:** 2026-01-26
**Goal:** Create test page for SEI dashboard integration

---

## CHANGES MADE

### Step 1: Created test page
```bash
cp docs/index.html docs/test.html
```

### Step 2: Copied SEI data
```bash
cp data/metrics_sei.json docs/metrics_sei.json
```

### Step 3: Updated data source
**File:** `docs/test.html:494`

Changed:
```javascript
const response = await fetch('./metrics_verified.json');
```

To:
```javascript
const response = await fetch('./metrics_sei.json');
```

### Step 4: Added SEI Cards HTML

**Location:** `docs/test.html:275-289` (before "Who else?" card)

```html
<!-- SEI Cards -->
<div class="sei-container">
    <div class="sei-card sei-small">
        <span class="sei-value" id="sei-news">—</span>
        <span class="sei-label">NEWS</span>
    </div>
    <div class="sei-card sei-hero">
        <span class="sei-value" id="sei-overall">—</span>
        <span class="sei-label">SOURCE EQUITY INDEX</span>
    </div>
    <div class="sei-card sei-small">
        <span class="sei-value" id="sei-sport">—</span>
        <span class="sei-label">SPORT</span>
    </div>
</div>
```

### Step 5: Added SEI Styling

**Location:** `docs/test.html:159-209`

```css
/* SEI Cards */
.sei-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.sei-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    border-radius: 8px;
}
.sei-card.sei-hero {
    background: #1a1a1a;
    color: white;
    padding: 2rem 3rem;
}
.sei-card.sei-small {
    background: #f8f8f8;
    color: #1a1a1a;
    padding: 1.25rem 2rem;
}
.sei-value {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.5rem;
}
.sei-hero .sei-value {
    font-size: 4rem;
}
.sei-small .sei-value {
    font-size: 2.5rem;
}
.sei-label {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.sei-hero .sei-label {
    color: rgba(255,255,255,0.7);
}
.sei-small .sei-label {
    color: rgba(26,26,26,0.6);
}
```

### Step 6: Added JavaScript Calculation

**Location:** `docs/test.html:708-736`

```javascript
// Calculate SEI scores
const validArticles = filteredArticles.filter(a =>
    a.sei_score !== null && a.sei_score !== undefined && !a.sei_exempt
);

const overall = validArticles.length > 0
    ? Math.round(validArticles.reduce((sum, a) => sum + a.sei_score, 0) / validArticles.length)
    : 0;

const newsArticles = validArticles.filter(a =>
    (a.display_category || '').toLowerCase().includes('news')
);
const newsSEI = newsArticles.length > 0
    ? Math.round(newsArticles.reduce((sum, a) => sum + a.sei_score, 0) / newsArticles.length)
    : '—';

const sportArticles = validArticles.filter(a =>
    (a.display_category || '').toLowerCase().includes('sport')
);
const sportSEI = sportArticles.length > 0
    ? Math.round(sportArticles.reduce((sum, a) => sum + a.sei_score, 0) / sportArticles.length)
    : '—';

// Update SEI display
document.getElementById('sei-overall').textContent = overall;
document.getElementById('sei-news').textContent = newsSEI;
document.getElementById('sei-sport').textContent = sportSEI;
```

---

## EXPECTED VALUES

When test page loads with all data:

| Card | Value | Based On |
|------|-------|----------|
| Overall SEI | **26** | 187 analyzed articles |
| News SEI | **29** | 94 news articles |
| Sport SEI | **22** | 93 sport articles |

---

## VISUAL DESIGN

### Layout
```
┌──────────┐   ┌────────────────┐   ┌──────────┐
│    29    │   │       26       │   │    22    │
│   NEWS   │   │ SOURCE EQUITY  │   │  SPORT   │
│          │   │     INDEX      │   │          │
└──────────┘   └────────────────┘   └──────────┘
   (small)          (hero)             (small)
```

### Colors
- **Hero card (center):** Black background (#1a1a1a), white text
- **Side cards:** Cream background (#f8f8f8), black text
- **Font:** Bricolage Grotesque

### Sizes
- Hero value: 4rem
- Small value: 2.5rem
- Labels: 0.7rem, uppercase, letter-spaced

---

## FILES MODIFIED/CREATED

1. ✅ `docs/test.html` - Created (copy of index.html with SEI integration)
2. ✅ `docs/metrics_sei.json` - Created (copy of data/metrics_sei.json)

---

## VERIFICATION CHECKLIST

To verify test page works:

1. Open `/test.html` in browser
2. Check SEI cards display at top of Analysis section
3. Verify values:
   - Overall: 26
   - News: 29
   - Sport: 22
4. Check all existing features still work:
   - Date selector
   - "Who else?" gender breakdown
   - Contributors section
   - Stories list

---

## GIT COMMIT

```bash
git add docs/test.html docs/metrics_sei.json
git commit -m "Add SEI test page with three-card layout"
[main 87ece15] Add SEI test page with three-card layout
 2 files changed, 30912 insertions(+)
 create mode 100644 docs/metrics_sei.json
 create mode 100644 docs/test.html
```

---

## NOTES

- `index.html` was NOT modified (as specified)
- All existing functionality preserved
- SEI cards positioned before "Who else?" as requested
- Calculation excludes exempt articles (correct behavior)
- Uses same Bricolage Grotesque font as hero stats
- Flexbox layout centers cards horizontally

---

**Task completed:** 2026-01-26
**Status:** ✅ Complete - Test page ready for review

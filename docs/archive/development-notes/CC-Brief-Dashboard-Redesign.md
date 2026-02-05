# Brief for Claude Code: Dashboard Redesign (Sprint 10)

## CRITICAL SAFETY RULES

1. **DO NOT modify docs/index.html** — this is live in production
2. Create new file: `docs/index-new.html`
3. All testing happens on the new file first
4. No deployment until Chindu explicitly approves

---

## Objective

Create a fresh, mobile-first dashboard with a bold editorial aesthetic. The new dashboard should:
- Pull from the same data source: `../data/metrics_verified.json`
- Replicate all existing functionality
- Be fully responsive (mobile-first)
- Look significantly more professional and distinctive

---

## Design Specifications

### Fonts
- **Headlines**: Bricolage Grotesque (Google Fonts)
- **Body**: Georgia (system font fallback)

### Colours
```css
--buzz-red: #c41230;
--ink: #1a1a1a;
--ink-muted: #767676;
--paper: #f8f6f1;
--paper-dark: #edeae3;
--white: #ffffff;
--female: #7c3aed;
--male: #0891b2;
--unknown: #9ca3af;
--success: #1a7f4b;
--warning: #b45309;
--danger: #c41230;
```

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (dark #1a1a1a, sticky)                               │
│ [Logo] Article Metrics                    [Date Selector]   │
│ ─────────────────────────────────────────────────────────── │
│ At a Glance · Analysis · Targets · Stories · Contributors   │
│ (red underline on active, horizontal scroll on mobile)      │
├─────────────────────────────────────────────────────────────┤
│ 3px BUzz red border                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AT A GLANCE                                                 │
│ ───────────────────────────── (2px black border)            │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              17 QUOTED SOURCES (featured card)          │ │
│ │              2.4 avg per story                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ 7        │ │ 3,948    │ │ 19       │ │ 2.4      │        │
│ │ Stories  │ │ Words    │ │ Images   │ │ Avg Src  │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                             │
│ ANALYSIS                                                    │
│ ─────────────────────────────                               │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ Inclusive   │ │ By Section  │ │ Publication │            │
│ │ Project     │ │             │ │ Rhythm      │            │
│ │ (gender)    │ │ (list)      │ │ (heatmap)   │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                             │
│ TARGETS                                                     │
│ ───────────────────────────── (editorial expectations)      │
│                                                             │
│ STORIES                                                     │
│ ───────────────────────────── (sortable table)              │
│                                                             │
│ CONTRIBUTORS                                                │
│ ───────────────────────────── (today/week toggle)           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ FOOTER (dark #1a1a1a)                                       │
│ Disclaimers + Editorial Expectations box                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Specific Design Fixes from Preview

1. **Logo**: Use `buzz-logo-dash-nowhite.png` (not text)
2. **By Section card**: Needs more padding — items feel cramped. Add `padding: 0.75rem 0` to items
3. **Section header borders**: 2px solid #1a1a1a (bold, not subtle)
4. **Gender bars**: 16-20px height, chunky and confident
5. **Heatmap**: Ensure readable on mobile (horizontal scroll if needed)

---

## Functionality Requirements

All existing functionality must work:

| Feature | Implementation |
|---------|----------------|
| Date selector | Filters ALL dashboard data to selected date |
| Section filter | Dropdown filters stories table by category |
| Sort controls | Sort stories by time/words/sources |
| Column sorting | Click table headers to sort |
| Sources modal | Click source count → modal shows evidence |
| Contributors toggle | Today / This Week buttons |
| Responsive | Mobile-first, works on iPhone SE → desktop |
| Headlines link | Open article URL in new tab |

---

## Data Source

```javascript
fetch('../data/metrics_verified.json')
```

Use the SAME JSON structure as current dashboard. Key fields:
- `articles[]` — array of article objects
- Each article has: headline, url, author, date, time, category, category_normalised, word_count, quoted_sources, source_evidence[], images{}, source_genders{}

---

## Technical Requirements

1. **Single HTML file** — all CSS in `<style>`, all JS in `<script>`
2. **No frameworks** — vanilla JS only, no React/Vue
3. **No build step** — must work directly on GitHub Pages
4. **Google Fonts** — Bricolage Grotesque via CDN link
5. **Chart.js** — NOT required (use CSS for bars/heatmap)

---

## File Location

Create: `docs/index-new.html`

DO NOT TOUCH: `docs/index.html`

---

## Testing Checklist

Before showing to Chindu:

- [ ] Loads without errors in browser console
- [ ] Date selector changes all data
- [ ] All sections display correctly
- [ ] Gender bars render with correct percentages
- [ ] Heatmap shows publication pattern
- [ ] Stories table sorts correctly
- [ ] Sources modal opens with evidence
- [ ] Contributors toggle works
- [ ] Mobile view (iPhone SE 375px) — no horizontal overflow
- [ ] Tablet view (768px) — 2-column grids
- [ ] Desktop view (1200px) — 3/4-column grids
- [ ] Logo displays correctly

---

## Local Testing Command

```bash
cd ~/buzz-metrics/docs && python3 -m http.server 8000
# Open: http://localhost:8000/index-new.html
```

---

## What NOT To Do

- ❌ Do not modify index.html
- ❌ Do not use React or any framework
- ❌ Do not create separate CSS/JS files
- ❌ Do not push until local testing complete
- ❌ Do not use Inter font (too generic)
- ❌ Do not use thin/wispy visual elements

---

## Reference Design

The design preview is attached. Key aesthetic: "Editorial Confident"
- Dark header anchors the page
- Bold section dividers (2px black)
- Chunky data visualisation (not thin lines)
- BUzz red as accent, not overwhelming
- Cream background (#f8f6f1) for warmth

---

## Approval Process

1. CC creates docs/index-new.html
2. Test locally with `python3 -m http.server`
3. Show Chindu for review
4. If approved → push to GitHub
5. Test at https://chindusree.github.io/buzz-metrics/index-new.html
6. Only after live testing approved → proceed with swap plan

---

## Questions?

Ask Chindu before making assumptions. When in doubt, match existing functionality from index.html.

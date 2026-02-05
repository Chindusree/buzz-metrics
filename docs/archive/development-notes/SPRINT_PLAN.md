# BUzz Metrics - Sprint Plan

## Current State
- 215 articles (Jan 13-16, 20-23)
- Newsdays end: Jan 30, 2026
- Expected total: ~350 articles

---

## Stage 1: Aggregate Views (Priority)

### 1.1 Date Picker - "All Dates" Option
- [ ] Add "All Dates" as first option in dropdown
- [ ] When selected, aggregate all data across dates
- [ ] All sections respond to this selection

### 1.2 Stories Section - Filters & Pagination
- [ ] Add filter toggles (same style as Contributors Today/This Week)
  - "All" | "News" | "Sport" buttons
- [ ] Add pagination: 50 articles per page
- [ ] "Previous / Next" controls
- [ ] Show "Page X of Y" indicator
- [ ] Maintain sort functionality within filtered/paginated view

### 1.3 Analysis - Section Cards with Gender
Current cards show:
- Stories count
- Avg sources

Add to each card:
- [ ] Gender breakdown row: "XX% W" (matching existing stat style)
- [ ] Same design pattern: label left, value right
- [ ] Card layout:
```
  NEWS
  ─────────────────────────
  Stories                18
  Avg sources           0.7
  Gender              33% W
```

### 1.4 Contributors - Show All
- [ ] "Today" / "This Week" toggle (already exists per screenshot)
- [ ] For "All Dates": show ALL contributors (60+ cards)
- [ ] Sort by article count (descending)
- [ ] Each card: Name, # articles, avg sources, gender ratio

### 1.5 Targets Table - Totals Row
- [ ] Add totals row at TOP when "All Dates" selected
- [ ] Bold styling to distinguish from date rows
- [ ] Shows: Total stories, Overall first published, Overall gender %

---

## Stage 2: Originals vs Secondary (All Dates Only)

### 2.1 New Analysis Card - Content Originality
Only shows when "All Dates" selected:
```
ORIGINALITY
─────────────────────────
Original images        142
Stock/Secondary         73
─────────────────────────
Original sources       189
Agency sources          26
```

### 2.2 Data Requirements
- [ ] Track image source (original vs stock) - needs backend update
- [ ] Track source type (original interview vs agency quote) - needs backend update
- [ ] May require manual tagging or heuristic detection

---

## Technical Notes

### Performance
- Ensure smooth rendering with 350+ articles
- Consider lazy loading for contributor cards
- Pagination essential for Stories table

### Design Consistency
- All toggles: same style as Contributors Today/This Week
- All cards: same padding, typography, divider style
- Gender display: "XX% W" format (matches BBC 50:50 style)

---

## Timeline
- Stage 1: Complete by Jan 27 (before final newsday week)
- Stage 2: Complete by Jan 31 (post-newsday analysis)

---

## Files to Modify
- `docs/index.html` - All frontend changes
- `scraper/scrape.py` - If backend tracking needed (Stage 2)

---

*Last updated: Jan 24, 2026*

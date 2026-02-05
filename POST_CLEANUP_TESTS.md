# Post-Cleanup Verification Tests

**Purpose:** Verify live dashboard functionality after cleanup
**Date:** 2026-02-05
**Site:** https://chindusree.github.io/buzz-metrics/

---

## ✅ Test 1: Live Dashboard Loads with Data

### What to check:
The main dashboard loads successfully and displays all three index cards with real data.

### Steps:
1. Open https://chindusree.github.io/buzz-metrics/ in browser
2. Wait for page load (should be < 3 seconds)
3. Verify you see:
   - ✅ Header: "BUzz Metrics" with date selector
   - ✅ Three index cards: SEI, ORI, BNS
   - ✅ SEI card shows a number (e.g., "63")
   - ✅ ORI card shows a number (e.g., "56")
   - ✅ BNS card shows a number (e.g., "67")
   - ✅ Article table below with rows of data

### Expected result:
- Dashboard loads without errors
- All three metrics display numeric scores
- Article table populates with 312 articles

### What this tests:
- ✅ index.html deployed correctly
- ✅ Data files (metrics_sei.json, metrics_ssi.json, metrics_bns.json) accessible
- ✅ JavaScript data merging working
- ✅ GitHub Pages serving files correctly

### If this fails:
```bash
# Check if data files exist in docs/
ls -lh docs/metrics_*.json

# Check GitHub Pages deployment status
# Visit: https://github.com/Chindusree/buzz-metrics/deployments

# Verify index.html wasn't archived by mistake
ls -lh docs/index.html
```

---

## ✅ Test 2: Date Filter Functionality

### What to check:
The date selector works and updates all three index cards + article table.

### Steps:
1. On live dashboard, locate date dropdown (top right)
2. Note current scores for SEI/ORI/BNS
3. Change date from "All dates" to a specific newsday (e.g., "2026-01-30")
4. Verify:
   - ✅ SEI score changes (different from "All dates")
   - ✅ ORI score changes
   - ✅ BNS score changes (or shows "—" if no breaking news)
   - ✅ Article table filters to show only that date
   - ✅ Article count updates in section subtitle
5. Change back to "All dates"
6. Verify scores return to original values

### Expected result:
- Date filter updates all cards instantly
- Article table filters correctly
- No JavaScript errors in browser console

### What this tests:
- ✅ JavaScript filter logic working
- ✅ Data structure correct (articles have proper date fields)
- ✅ State management functional
- ✅ No broken dependencies from archived scripts

### If this fails:
```bash
# Check browser console for errors (F12 → Console tab)
# Look for: "Uncaught ReferenceError" or "Cannot read property"

# Verify no production JS was accidentally archived
ls scraper/*.py | grep -E "scrape|sei_production|ssi_score"
```

---

## ✅ Test 3: Methodology Popup Opens with Links

### What to check:
All three methodology popups (SEI, ORI, BNS) open and display correct content with working hyperlinks.

### Steps:
1. On live dashboard, scroll to SEI card
2. Click "See how this is **calculated**" link
3. Verify SEI popup opens with:
   - ✅ Headline: "How we calculate SEI" (with rose accent)
   - ✅ Cream background (#faf9f6)
   - ✅ Methodology text visible
   - ✅ Two clickable links (Notion pages) with keyword underlines
4. Click one of the links → should open in new tab
5. Close popup (X button)
6. Repeat for ORI card → Click methodology link
7. Verify ORI popup with "Soleless Journalism" link
8. Repeat for BNS card → Click methodology link
9. Verify BNS popup with "Breaking News Score" link

### Expected result:
- All 3 popups open/close smoothly
- All external links work (5 total: BBC 50:50, Diversity Pledge, WAN-IFRA in footer + methodology links)
- No layout/styling issues
- Cream backgrounds visible

### What this tests:
- ✅ HTML modal structure intact
- ✅ CSS styling preserved
- ✅ External links functional
- ✅ Footer content updated correctly (with BUzz hyperlink and date range)
- ✅ No hardcoded paths broken by archive moves

### If this fails:
```bash
# Check if index.html was modified during cleanup
git diff v4.5-pre-cleanup:docs/index.html docs/index.html

# Verify CSS/JS sections intact
grep -c "modal-overlay" docs/index.html  # Should return 4+
```

---

## Quick Verification Checklist

Run these three tests in order. If all pass, cleanup was successful.

| Test | What It Validates | Status |
|------|-------------------|--------|
| **Test 1: Dashboard Loads** | Data files, deployment, basic functionality | ⬜ |
| **Test 2: Date Filter** | JavaScript logic, data structure | ⬜ |
| **Test 3: Popups & Links** | HTML structure, external resources | ⬜ |

---

## Additional Quick Checks (Optional)

### Check 4: Footer Content
- Scroll to bottom of page
- Verify footer text mentions "January 12 and January 30, 2026"
- Verify BUzz hyperlink works (buzz.bournemouth.ac.uk)
- Verify 4 external links work (BBC 50:50, Diversity Pledge, WAN-IFRA, BUzz)

### Check 5: Browser Console Clean
- Open browser DevTools (F12)
- Go to Console tab
- Refresh page
- Verify no red errors (warnings OK)

### Check 6: Mobile Responsiveness
- Resize browser window to narrow width (~400px)
- Verify layout stacks properly
- Verify cards remain readable
- Verify table scrolls horizontally if needed

---

## Automated Verification (Optional)

If you want to automate these checks:

```bash
# Test 1: Check if index.html loads
curl -s https://chindusree.github.io/buzz-metrics/ | grep -q "BUzz Metrics" && echo "✓ Dashboard loads"

# Test 2: Check if data files are accessible
curl -s https://chindusree.github.io/buzz-metrics/metrics_sei.json | jq -e '.articles | length' && echo "✓ Data files accessible"

# Test 3: Check if modals exist in HTML
curl -s https://chindusree.github.io/buzz-metrics/ | grep -q "modal-overlay" && echo "✓ Modals present"
```

---

## Troubleshooting Guide

### Problem: Dashboard shows blank page
**Likely cause:** GitHub Pages hasn't rebuilt yet (1-5 min delay)
**Solution:** Wait 5 minutes, hard refresh (Cmd+Shift+R / Ctrl+Shift+F5)

### Problem: Scores show "—" for everything
**Likely cause:** Data files not loading (404 error)
**Solution:**
```bash
# Check data files deployed
ls docs/metrics_*.json
git status  # Ensure working tree clean
```

### Problem: Date filter doesn't work
**Likely cause:** JavaScript error
**Solution:** Check browser console (F12) for errors

### Problem: Popups don't open
**Likely cause:** JavaScript function broken or CSS issue
**Solution:**
```bash
# Verify index.html intact
git diff v4.4-live:docs/index.html docs/index.html
```

### Problem: Links go to 404
**Likely cause:** Hardcoded paths broken
**Solution:** All external links should use full URLs (https://...)

---

## Expected Test Results (Pass Criteria)

### Test 1: PASS
- SEI: ~63 (mean across all dates)
- ORI: ~56 (mean across all dates)
- BNS: ~67 (mean across breaking news articles)
- Article table: 312 rows visible

### Test 2: PASS
- Selecting "2026-01-30" changes scores
- Article count updates to match filtered date
- Selecting "All dates" restores original scores

### Test 3: PASS
- 3 methodology popups open/close
- 5+ external links functional
- Footer shows date range and BUzz link

---

## Recovery Commands (If Tests Fail)

### Nuclear Option: Restore to pre-cleanup
```bash
git reset --hard v4.5-pre-cleanup
git push origin main --force
```

### Surgical Fix: Restore just index.html
```bash
git checkout v4.5-pre-cleanup -- docs/index.html
git commit -m "fix: Restore index.html from pre-cleanup"
git push origin main
```

### Data File Fix: Re-copy data to docs/
```bash
cp data/metrics_sei.json docs/
cp data/metrics_ssi.json docs/
cp data/metrics_bns.json docs/
git add docs/metrics_*.json
git commit -m "fix: Re-deploy data files"
git push origin main
```

---

## Sign-Off

After running all three tests:

- [ ] Test 1: Dashboard loads with data ✅
- [ ] Test 2: Date filter works ✅
- [ ] Test 3: Popups and links work ✅
- [ ] Browser console clean (no errors) ✅
- [ ] Footer content correct ✅

**If all checked:** Cleanup successful, site functional! 🎉

**If any unchecked:** See troubleshooting guide above.

---

**Created:** 2026-02-05
**Site:** https://chindusree.github.io/buzz-metrics/
**Last verified:** ___ (fill in after testing)

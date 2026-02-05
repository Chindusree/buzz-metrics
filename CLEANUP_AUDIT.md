# Repository Cleanup Audit — 2026-02-05

**Status:** Awaiting approval before execution
**Purpose:** Safe archival of development artifacts after v4.4-live deployment

---

## Current State

- **Live dashboard:** `docs/index.html` (101K, deployed 5 Feb)
- **Dev dashboard:** `docs/staff-test.html` (101K, identical to live)
- **Latest backup:** `docs/index-backup-20260204.html` (64K, pre-deployment)
- **Workflows:** All disabled (sei_daily, ssi_daily, scrape)
- **Last deployment tag:** v4.4-live (5 Feb 2026)

---

## CATEGORY 1: HTML Files in docs/ (19 files total)

### ✅ KEEP (3 files)
| File | Size | Status |
|------|------|--------|
| `index.html` | 101K | **LIVE PRODUCTION** |
| `staff-test.html` | 101K | **ACTIVE DEVELOPMENT** |
| `index-backup-20260204.html` | 64K | **SAFETY CHECKPOINT** (pre-v4.4) |

### 🗄️ ARCHIVE — Old Development Versions (11 files, 22 Jan)
**Reason:** Superseded by current v4.4 dashboard
**Action:** Move to `docs/archive/development/`

| File | Size | Date | Notes |
|------|------|------|-------|
| `index-new.html` | 53K | 22 Jan | Development iteration |
| `index-new-FUNCTIONAL-COMPLETE.html` | 46K | 22 Jan | Milestone version |
| `index-new-interactive-SAFE.html` | 51K | 22 Jan | Safe checkpoint |
| `index-new-modified.html` | 51K | 22 Jan | Modified version |
| `index-new-backup.html` | 51K | 22 Jan | Backup copy |
| `index-new-SAFE-TAG.html` | 20K | 22 Jan | Tagged checkpoint |
| `index-new-static-backup.html` | 22K | 22 Jan | Static backup |
| `index-v7-archive.html` | 51K | 22 Jan | Version 7 archive |
| `buzz-visual-preview.html` | 20K | 22 Jan | Visual prototype |
| `compare.html` | 5.4K | 22 Jan | Comparison tool |
| `index-student.html` | 34K | 20 Jan | Student-facing prototype |

### 🗄️ ARCHIVE — Old Staff Versions (3 files)
**Action:** Move to `docs/archive/staff-versions/`

| File | Size | Date | Notes |
|------|------|------|-------|
| `staff.html` | 71K | 27 Jan | Pre-staff-test version |
| `staff-test-backup.html` | 78K | 30 Jan | Backup before ORI rename |
| `staff-test-gradient.html` | 78K | 30 Jan | Gradient experiment |

### 🗄️ ARCHIVE — Old Backups (2 files)
**Action:** Move to `docs/archive/backups/`

| File | Size | Date | Notes |
|------|------|------|-------|
| `index-backup.html` | 68K | 22 Jan | Undated backup |
| `index-backup-20260124_115104.html` | 57K | 26 Jan | January 24 backup |

---

## CATEGORY 2: Root Documentation Files (6 files)

### ✅ KEEP (1 file)
| File | Size | Status |
|------|------|--------|
| `README.md` | 3.3K | **ACTIVE** — Public-facing documentation |

### 🗄️ ARCHIVE — Development Documentation (5 files)
**Action:** Move to `docs/archive/development-notes/`

| File | Size | Date | Purpose |
|------|------|------|---------|
| `CC-Brief-Dashboard-Redesign.md` | 8.9K | 22 Jan | Design brief for dashboard redesign |
| `DEVELOPMENT.md` | 5.5K | 20 Jan | Development notes |
| `HANDOVER_2026-01-24.md` | 4.7K | 26 Jan | Dated handover document |
| `SPRINT_PLAN.md` | 2.9K | 26 Jan | Sprint planning notes |
| `BREAKING_stories_list.txt` | 3.3K | 31 Jan | Breaking news article list |

**Note:** These contain valuable development context but are no longer active references.

---

## CATEGORY 3: Python Scripts in scraper/ (59 files)

### ✅ KEEP — Production Scripts (6 files)
| File | Size | Purpose |
|------|------|---------|
| `scrape.py` | 132K | **MAIN SCRAPER** (disabled via workflow) |
| `verify.py` | 6.2K | **VERIFICATION** pipeline |
| `compare.py` | 15K | **RECONCILIATION** pipeline |
| `sei_production.py` | 18K | **SEI SCORING** (disabled via workflow) |
| `ssi_score.py` | 23K | **ORI SCORING** (disabled via workflow) |
| `reconcile.py` | 14K | **COMPARISON** reconciliation |

### 🗄️ ARCHIVE — Debug Scripts (15 files)
**Action:** Move to `scraper/archive/debug/`

All `debug_*.py` and `test_*_fixes.py` files from 22 Jan development sprints:
- `debug_anne_marie.py`, `debug_iframe_detection.py`, `debug_man_charged.py`
- `debug_mcadam.py`, `debug_normalized_text.py`, `debug_quotes.py`
- `debug_rugby_article.py`, `debug_rugby_groq_text.py`
- `test_after_fixes.py`, `test_anne_marie_final.py`, `test_before_fixes.py`
- `test_detailed_before.py`, `test_evidence_recording.py`
- `test_groq_debug.py`, `test_groq_single.py`, `verify_anne_marie.py`

### 🗄️ ARCHIVE — Sprint Test Scripts (15 files)
**Action:** Move to `scraper/archive/sprint-tests/`

All `test_sprint_*.py` files from January 19 development:
- `test_sprint_7_10.py` through `test_sprint_7_17.py`
- Plus edge case tests: `test_controlled.py`, `test_extraction.py`, etc.

### 🗄️ ARCHIVE — Migration & Audit Scripts (12 files)
**Action:** Move to `scraper/archive/migrations/`

One-time migration and audit scripts (20-26 Jan):
- `add_historical.py`, `add_missing.py`, `migrate_categories.py`
- `migrate_to_groq.py`, `backfill_wordcount.py`, `backfill_sources.py`
- `audit_wordpress_fetch.py`, `investigate_shorthand.py`, `shorthand_audit.py`
- `full_shorthand_scan.py`, `rescore_shorthand.py`, `fetch_spot_check_text.py`

### 🗄️ ARCHIVE — Test/Experimental Scripts (11 files)
**Action:** Move to `scraper/archive/experimental/`

Testing and experimental scripts:
- `sei_test.py`, `sei_exemption_test.py`, `ssi_test_v2.1.py`
- `test_groq_3articles.py`, `test_groq_integration.py`
- `test_name_gender_edge_cases.py`, `test_name_gender_fixes.py`
- `test_source_fixes.py`, `test_wp_audit.py`, `scrape_test.py`
- `groq_verify.py`, `scrape_regex_backup.py`

### ⚠️ REVIEW — Utility Scripts (5 files)
**Action:** Manual review needed — may still be useful

| File | Size | Date | Purpose |
|------|------|------|---------|
| `analyze_sei_results.py` | 5.5K | 26 Jan | SEI results analysis |
| `oi_adaptive.py` | 6.6K | 29 Jan | OI scoring experiments |

---

## CATEGORY 4: Configuration Files

### ⚠️ FIX — .gitignore (duplicate entries)

**Current:**
```
venv/
__pycache__/
*.pyc
.DS_Store
.env            # ← line 5
data/comparison.json
.env            # ← line 7 (DUPLICATE)
data/comparison.json  # ← line 8 (DUPLICATE)
```

**Proposed:**
```
venv/
__pycache__/
*.pyc
.DS_Store
.env
data/comparison.json
```

---

## CATEGORY 5: .github/workflows (3 disabled files)

### ✅ KEEP AS-IS (disabled state)
| File | Status |
|------|--------|
| `sei_daily.yml.disabled` | Archived (was 2x daily) |
| `ssi_daily.yml.disabled` | Archived (was daily) |
| `scrape.yml.disabled` | Archived (was hourly) |

**Reason:** Kept for reference. Can be restored if needed.

---

## Execution Plan (Safe Steps)

### Step 1: Create Archive Structure
```bash
mkdir -p docs/archive/{development,staff-versions,backups}
mkdir -p docs/archive/development-notes
mkdir -p scraper/archive/{debug,sprint-tests,migrations,experimental}
```

### Step 2: Move HTML Files (test first with -n)
```bash
# Test with -n (dry run)
git mv -n docs/index-new*.html docs/archive/development/
git mv -n docs/index-v7*.html docs/archive/development/
# ... etc
```

### Step 3: Move Documentation
```bash
git mv CC-Brief-Dashboard-Redesign.md docs/archive/development-notes/
git mv DEVELOPMENT.md docs/archive/development-notes/
# ... etc
```

### Step 4: Move Python Scripts
```bash
cd scraper
git mv debug_*.py archive/debug/
git mv test_sprint_*.py archive/sprint-tests/
# ... etc
```

### Step 5: Fix .gitignore
```bash
# Edit to remove duplicate lines 7-8
```

### Step 6: Commit & Tag
```bash
git commit -m "chore: Archive development artifacts post-v4.4"
git tag v4.5-cleanup
git push origin main --tags
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Accidentally delete live files | Use `git mv` (reversible), keep dry-run logs |
| Break relative paths | Only moving archived files, not active ones |
| Lose development history | All files remain in git history |
| Need old file later | Easy to restore from archive/ or git history |

---

## Approval Required

Before proceeding, confirm:
- [ ] Archive structure is acceptable
- [ ] File categorization is correct
- [ ] No active dependencies on archived files
- [ ] Safe to proceed with Step 1

---

**Generated:** 2026-02-05
**Current branch:** main (2 commits ahead of origin)
**Working tree:** Clean

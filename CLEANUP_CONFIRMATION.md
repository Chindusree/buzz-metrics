# Cleanup Confirmation — Ready to Execute

**Date:** 2026-02-05
**Current State:** Working tree clean, all changes committed and pushed

---

## Safe Workflow Overview

### ✅ Safety Measures in Place:

1. **Using `git mv`** — All moves are tracked by git and fully reversible
2. **Dry-run testing** — Will use `-n` flag to preview moves before executing
3. **Working tree clean** — No uncommitted changes to lose
4. **Already pushed** — All recent work is safely on GitHub
5. **Creating checkpoint tag** — Will tag v4.5-pre-cleanup before starting
6. **Archive structure** — Files move to organized folders, not deleted

### Workflow Steps:

```
1. Tag current state as v4.5-pre-cleanup
2. Create archive folder structure
3. Test moves with git mv -n (dry run)
4. Execute moves with git mv
5. Review with git status
6. Commit as "chore: Archive development artifacts"
7. Tag as v4.5-cleanup
8. Push to GitHub
```

---

## Files to Archive (88 total)

### ✅ Category 1: HTML Files (16 files)

**KEEPING (3 files):**
- ✅ `docs/index.html` (101K) — LIVE PRODUCTION
- ✅ `docs/staff-test.html` (101K) — ACTIVE DEVELOPMENT
- ✅ `docs/index-backup-20260204.html` (64K) — SAFETY CHECKPOINT

**ARCHIVING (16 files):**

To `docs/archive/development/` (11 files):
- index-new.html (53K)
- index-new-FUNCTIONAL-COMPLETE.html (46K)
- index-new-interactive-SAFE.html (51K)
- index-new-modified.html (51K)
- index-new-backup.html (51K)
- index-new-SAFE-TAG.html (20K)
- index-new-static-backup.html (22K)
- index-v7-archive.html (51K)
- buzz-visual-preview.html (20K)
- compare.html (5.4K)
- index-student.html (34K)

To `docs/archive/staff-versions/` (3 files):
- staff.html (71K)
- staff-test-backup.html (78K)
- staff-test-gradient.html (78K)

To `docs/archive/backups/` (2 files):
- index-backup.html (68K)
- index-backup-20260124_115104.html (57K)

---

### ✅ Category 2: Root Documentation (5 files)

**KEEPING (1 file):**
- ✅ `README.md` — PUBLIC DOCUMENTATION

**ARCHIVING to `docs/archive/development-notes/` (5 files):**
- CC-Brief-Dashboard-Redesign.md (8.9K)
- DEVELOPMENT.md (5.5K)
- HANDOVER_2026-01-24.md (4.7K)
- SPRINT_PLAN.md (2.9K)
- BREAKING_stories_list.txt (3.3K)

---

### ✅ Category 3: Python Scripts (53 files)

**KEEPING (6 files):**
- ✅ `scraper/scrape.py` — MAIN SCRAPER
- ✅ `scraper/verify.py` — VERIFICATION
- ✅ `scraper/compare.py` — COMPARISON
- ✅ `scraper/reconcile.py` — RECONCILIATION
- ✅ `scraper/sei_production.py` — SEI SCORING
- ✅ `scraper/ssi_score.py` — ORI SCORING

**ARCHIVING (53 files):**

To `scraper/archive/debug/` (15 files):
- debug_anne_marie.py
- debug_iframe_detection.py
- debug_man_charged.py
- debug_mcadam.py
- debug_normalized_text.py
- debug_quotes.py
- debug_rugby_article.py
- debug_rugby_groq_text.py
- test_after_fixes.py
- test_anne_marie_final.py
- test_before_fixes.py
- test_detailed_before.py
- test_evidence_recording.py
- test_groq_debug.py
- verify_anne_marie.py

To `scraper/archive/sprint-tests/` (15 files):
- test_controlled.py
- test_extraction.py
- test_groq_3articles.py
- test_groq_integration.py
- test_groq_single.py
- test_sprint_7_10.py through test_sprint_7_17.py (8 files)
- test_wp_audit.py

To `scraper/archive/migrations/` (12 files):
- add_historical.py
- add_missing.py
- backfill_sources.py
- backfill_wordcount.py
- migrate_categories.py
- migrate_to_groq.py
- audit_wordpress_fetch.py
- investigate_shorthand.py
- shorthand_audit.py
- full_shorthand_scan.py
- rescore_shorthand.py
- fetch_spot_check_text.py

To `scraper/archive/experimental/` (11 files):
- sei_test.py
- sei_exemption_test.py
- ssi_test_v2.1.py
- test_name_gender_edge_cases.py
- test_name_gender_fixes.py
- test_source_fixes.py
- scrape_test.py
- scrape_regex_backup.py
- groq_verify.py
- analyze_sei_results.py
- oi_adaptive.py

---

### ✅ Category 4: .gitignore Fix

**Current (with duplicates):**
```
venv/
__pycache__/
*.pyc
.DS_Store
.env
data/comparison.json
.env            # ← DUPLICATE (line 7)
data/comparison.json  # ← DUPLICATE (line 8)
```

**After cleanup:**
```
venv/
__pycache__/
*.pyc
.DS_Store
.env
data/comparison.json
```

---

## Files NOT Being Archived

### Production Components (Stay in Place):
- ✅ All 6 production Python scripts
- ✅ All 3 LLM prompts (sei_prompt, ssi_prompt, ngi_prompt)
- ✅ All 85 data JSON files
- ✅ 3 active HTML files (index, staff-test, backup)
- ✅ All documentation (README, ARCHITECTURE, SCOPE_OF_WORK, ADRs)
- ✅ 3 disabled workflow files (.yml.disabled)
- ✅ scraper/requirements.txt
- ✅ .env, .gitignore (after fixing duplicates)

### Analysis Folder (Stay in Place):
- ✅ All 10 investigation reports in `analysis/`

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Accidentally delete live files | **ZERO** | Using `git mv`, not `rm` |
| Break relative paths | **ZERO** | Only moving archived files |
| Lose development history | **ZERO** | All files remain in git history |
| Need old file later | **LOW** | Easy to restore from archive/ |
| Commit mistakes | **ZERO** | Dry-run testing + git revert available |

---

## Archive Structure to Create

```
buzz-metrics/
├── docs/
│   └── archive/
│       ├── development/          # 11 old dashboard versions
│       ├── staff-versions/       # 3 staff dashboard iterations
│       ├── backups/              # 2 old backups
│       └── development-notes/    # 5 root documentation files
│
└── scraper/
    └── archive/
        ├── debug/                # 15 debug scripts
        ├── sprint-tests/         # 15 test scripts
        ├── migrations/           # 12 migration scripts
        └── experimental/         # 11 experimental scripts
```

---

## Execution Commands Preview

### Step 1: Tag & Create Structure
```bash
git tag v4.5-pre-cleanup
mkdir -p docs/archive/{development,staff-versions,backups,development-notes}
mkdir -p scraper/archive/{debug,sprint-tests,migrations,experimental}
```

### Step 2: Test Moves (Dry Run)
```bash
git mv -n docs/index-new*.html docs/archive/development/
# ... etc (will show what would happen)
```

### Step 3: Execute Moves
```bash
git mv docs/index-new*.html docs/archive/development/
# ... etc (actual moves)
```

### Step 4: Commit & Tag
```bash
git commit -m "chore: Archive development artifacts post-v4.4"
git tag v4.5-cleanup
git push origin main --tags
```

---

## Confirmation Checklist

Before proceeding, verify:

- [x] Working tree is clean (✅ confirmed)
- [x] All recent changes pushed (✅ confirmed)
- [x] Backup exists (✅ index-backup-20260204.html)
- [x] Production files identified (✅ 3 HTML, 6 Python, 3 prompts)
- [x] Archive targets identified (✅ 88 files)
- [x] No active dependencies on archived files (✅ all superseded)
- [x] Git tags ready (✅ v4.5-pre-cleanup, v4.5-cleanup)

---

## Ready to Proceed?

All safety measures are in place. The cleanup is fully reversible via:
- `git revert` (undo commit)
- `git checkout <file>` (restore individual file)
- `git mv` back (move file back to original location)
- Git history (always accessible)

**Next step:** Execute cleanup workflow step-by-step.

---

**Generated:** 2026-02-05
**Status:** AWAITING APPROVAL

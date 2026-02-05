# Safe Cleanup Workflow with Reversal Steps

**Date:** 2026-02-05
**Objective:** Archive 88 development artifacts while maintaining full reversal capability

---

## Step-by-Step Safe Flow

### STEP 1: Create Checkpoint Tag
**Command:**
```bash
git tag v4.5-pre-cleanup
git push origin v4.5-pre-cleanup
```

**Purpose:** Creates a named restore point BEFORE any changes

**Reversal:**
```bash
git checkout v4.5-pre-cleanup
# or
git reset --hard v4.5-pre-cleanup
```

---

### STEP 2: Create Archive Folder Structure
**Command:**
```bash
mkdir -p docs/archive/{development,staff-versions,backups,development-notes}
mkdir -p scraper/archive/{debug,sprint-tests,migrations,experimental}
```

**Purpose:** Creates destination folders for archived files

**Reversal:**
```bash
# If needed (before commit):
rm -rf docs/archive scraper/archive
```

---

### STEP 3: Test HTML Moves (Dry Run)
**Command:**
```bash
# Test moving development versions
git mv -n docs/index-new*.html docs/archive/development/
git mv -n docs/index-v7-archive.html docs/archive/development/
git mv -n docs/buzz-visual-preview.html docs/archive/development/
git mv -n docs/compare.html docs/archive/development/
git mv -n docs/index-student.html docs/archive/development/

# Test moving staff versions
git mv -n docs/staff.html docs/archive/staff-versions/
git mv -n docs/staff-test-backup.html docs/archive/staff-versions/
git mv -n docs/staff-test-gradient.html docs/archive/staff-versions/

# Test moving old backups
git mv -n docs/index-backup.html docs/archive/backups/
git mv -n docs/index-backup-20260124_115104.html docs/archive/backups/
```

**Purpose:** Preview moves WITHOUT actually executing them (`-n` = dry run)

**Expected Output:** List of "Renaming X to Y" messages with no errors

**Reversal:** Not needed (dry run doesn't change anything)

---

### STEP 4: Execute HTML Moves
**Command:** (Same as Step 3 but WITHOUT `-n` flag)
```bash
git mv docs/index-new*.html docs/archive/development/
git mv docs/index-v7-archive.html docs/archive/development/
git mv docs/buzz-visual-preview.html docs/archive/development/
git mv docs/compare.html docs/archive/development/
git mv docs/index-student.html docs/archive/development/

git mv docs/staff.html docs/archive/staff-versions/
git mv docs/staff-test-backup.html docs/archive/staff-versions/
git mv docs/staff-test-gradient.html docs/archive/staff-versions/

git mv docs/index-backup.html docs/archive/backups/
git mv docs/index-backup-20260124_115104.html docs/archive/backups/
```

**Purpose:** Actually move HTML files to archive

**Verification:**
```bash
git status  # Should show "renamed" entries
ls docs/archive/development/  # Should show 11 files
ls docs/archive/staff-versions/  # Should show 3 files
ls docs/archive/backups/  # Should show 2 files
```

**Reversal (if needed before commit):**
```bash
git mv docs/archive/development/* docs/
git mv docs/archive/staff-versions/* docs/
git mv docs/archive/backups/* docs/
```

---

### STEP 5: Test Documentation Moves (Dry Run)
**Command:**
```bash
git mv -n CC-Brief-Dashboard-Redesign.md docs/archive/development-notes/
git mv -n DEVELOPMENT.md docs/archive/development-notes/
git mv -n HANDOVER_2026-01-24.md docs/archive/development-notes/
git mv -n SPRINT_PLAN.md docs/archive/development-notes/
git mv -n BREAKING_stories_list.txt docs/archive/development-notes/
```

**Purpose:** Preview documentation moves

**Reversal:** Not needed (dry run)

---

### STEP 6: Execute Documentation Moves
**Command:** (Same as Step 5 without `-n`)
```bash
git mv CC-Brief-Dashboard-Redesign.md docs/archive/development-notes/
git mv DEVELOPMENT.md docs/archive/development-notes/
git mv HANDOVER_2026-01-24.md docs/archive/development-notes/
git mv SPRINT_PLAN.md docs/archive/development-notes/
git mv BREAKING_stories_list.txt docs/archive/development-notes/
```

**Verification:**
```bash
git status
ls docs/archive/development-notes/  # Should show 5 files
```

**Reversal (before commit):**
```bash
git mv docs/archive/development-notes/* .
```

---

### STEP 7: Test Python Script Moves (Dry Run)
**Command:**
```bash
# Debug scripts
cd scraper
git mv -n debug_*.py archive/debug/
git mv -n test_after_fixes.py archive/debug/
git mv -n test_anne_marie_final.py archive/debug/
git mv -n test_before_fixes.py archive/debug/
git mv -n test_detailed_before.py archive/debug/
git mv -n test_evidence_recording.py archive/debug/
git mv -n test_groq_debug.py archive/debug/
git mv -n verify_anne_marie.py archive/debug/

# Sprint tests
git mv -n test_controlled.py archive/sprint-tests/
git mv -n test_extraction.py archive/sprint-tests/
git mv -n test_groq_3articles.py archive/sprint-tests/
git mv -n test_groq_integration.py archive/sprint-tests/
git mv -n test_groq_single.py archive/sprint-tests/
git mv -n test_sprint_*.py archive/sprint-tests/
git mv -n test_wp_audit.py archive/sprint-tests/

# Migrations
git mv -n add_historical.py archive/migrations/
git mv -n add_missing.py archive/migrations/
git mv -n backfill_sources.py archive/migrations/
git mv -n backfill_wordcount.py archive/migrations/
git mv -n migrate_categories.py archive/migrations/
git mv -n migrate_to_groq.py archive/migrations/
git mv -n audit_wordpress_fetch.py archive/migrations/
git mv -n investigate_shorthand.py archive/migrations/
git mv -n shorthand_audit.py archive/migrations/
git mv -n full_shorthand_scan.py archive/migrations/
git mv -n rescore_shorthand.py archive/migrations/
git mv -n fetch_spot_check_text.py archive/migrations/

# Experimental
git mv -n sei_test.py archive/experimental/
git mv -n sei_exemption_test.py archive/experimental/
git mv -n ssi_test_v2.1.py archive/experimental/
git mv -n test_name_gender_edge_cases.py archive/experimental/
git mv -n test_name_gender_fixes.py archive/experimental/
git mv -n test_source_fixes.py archive/experimental/
git mv -n scrape_test.py archive/experimental/
git mv -n scrape_regex_backup.py archive/experimental/
git mv -n groq_verify.py archive/experimental/
git mv -n analyze_sei_results.py archive/experimental/
git mv -n oi_adaptive.py archive/experimental/

cd ..
```

**Purpose:** Preview Python script moves

**Reversal:** Not needed (dry run)

---

### STEP 8: Execute Python Script Moves
**Command:** (Same as Step 7 without `-n`)

**Verification:**
```bash
cd scraper
ls archive/debug/  # Should show 15 files
ls archive/sprint-tests/  # Should show 15 files
ls archive/migrations/  # Should show 12 files
ls archive/experimental/  # Should show 11 files
cd ..
```

**Reversal (before commit):**
```bash
cd scraper
git mv archive/debug/* .
git mv archive/sprint-tests/* .
git mv archive/migrations/* .
git mv archive/experimental/* .
cd ..
```

---

### STEP 9: Fix .gitignore Duplicates
**Command:**
```bash
# Edit .gitignore to remove duplicate lines 7-8
```

**Manual edit removes:**
```
.env            # Line 7 (duplicate)
data/comparison.json  # Line 8 (duplicate)
```

**Verification:**
```bash
cat .gitignore  # Should show 6 lines, no duplicates
```

**Reversal (before commit):**
```bash
git checkout .gitignore
```

---

### STEP 10: Update README.md
**Add section after "Repository Structure":**

```markdown
### Archived Files

Development artifacts from the January 2026 build have been archived:
- [HTML prototypes](docs/archive/development/) — 11 dashboard iterations
- [Staff versions](docs/archive/staff-versions/) — 3 staff dashboard variants
- [Development notes](docs/archive/development-notes/) — Sprint plans, handover docs
- [Debug scripts](scraper/archive/debug/) — 15 debugging scripts
- [Test scripts](scraper/archive/sprint-tests/) — 15 sprint test files
- [Migration scripts](scraper/archive/migrations/) — 12 one-time operations
- [Experimental scripts](scraper/archive/experimental/) — 11 experimental features

All archived files remain accessible in git history and in `archive/` folders.
```

**Verification:**
```bash
git diff README.md  # Review changes
```

**Reversal (before commit):**
```bash
git checkout README.md
```

---

### STEP 11: Review All Changes
**Command:**
```bash
git status
git diff --stat
git diff --cached --stat
```

**Expected Output:**
- 88 files renamed
- 1 file modified (.gitignore)
- 1 file modified (README.md)
- 8 new directories created

**If anything looks wrong:** Use reversals from steps above

---

### STEP 12: Commit Changes
**Command:**
```bash
git add -A
git commit -m "chore: Archive development artifacts post-v4.4

Archived 88 files to maintain clean repository structure:
- 16 HTML files → docs/archive/ (development, staff-versions, backups)
- 5 documentation files → docs/archive/development-notes/
- 53 Python scripts → scraper/archive/ (debug, sprint-tests, migrations, experimental)
- Fixed .gitignore duplicates

All production files remain in place. Archived files accessible via git history.

See CLEANUP_AUDIT.md for full inventory.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Verification:**
```bash
git log -1  # Review commit
git show --stat  # Show commit details
```

**Reversal:**
```bash
git reset --soft HEAD~1  # Undo commit, keep changes staged
# or
git reset --hard HEAD~1  # Undo commit AND changes
# or
git revert HEAD  # Create new commit undoing changes
```

---

### STEP 13: Tag Cleanup Version
**Command:**
```bash
git tag v4.5-cleanup -a -m "Cleanup: Archived 88 development artifacts"
```

**Verification:**
```bash
git tag | grep v4.5
# Should show:
# v4.5-pre-cleanup
# v4.5-cleanup
```

**Reversal:**
```bash
git tag -d v4.5-cleanup  # Delete tag locally
```

---

### STEP 14: Push to GitHub
**Command:**
```bash
git push origin main
git push origin --tags
```

**Verification:**
```bash
# Check GitHub repository online
# Verify archive folders visible
```

**Reversal:**
```bash
# If pushed by mistake:
git push origin :refs/tags/v4.5-cleanup  # Delete remote tag
git revert HEAD  # Create reversal commit
git push origin main  # Push reversal
```

---

## Emergency Reversal (Nuclear Option)

If everything goes wrong and you need to completely undo:

```bash
# Go back to pre-cleanup state
git reset --hard v4.5-pre-cleanup

# Force push (DANGEROUS - only if needed)
git push origin main --force

# Alternative: Restore from GitHub
git fetch origin
git reset --hard origin/main
```

---

## Files to Update During Cleanup

### 1. README.md
**Section to add:** "Archived Files" (after Repository Structure)
**Purpose:** Document where archived files are located

### 2. .gitignore
**Change:** Remove duplicate lines 7-8
**Purpose:** Clean up configuration file

### 3. CLEANUP_AUDIT.md (optional)
**Change:** Update status from "Awaiting approval" to "Completed 2026-02-05"
**Purpose:** Record completion

### 4. CLEANUP_CONFIRMATION.md (optional)
**Change:** Add "EXECUTED" status
**Purpose:** Record execution

---

## Post-Cleanup Verification

After completing all steps:

```bash
# Verify production files still in place
ls docs/index.html docs/staff-test.html  # Should exist
ls scraper/scrape.py scraper/sei_production.py  # Should exist
ls data/metrics_*.json  # Should show 85+ files

# Verify archived files moved
ls docs/archive/development/  # Should show 11 files
ls scraper/archive/debug/  # Should show 15 files

# Verify git history intact
git log --oneline | head -20  # Should show all commits

# Verify remote sync
git status  # Should show "up to date with origin/main"
```

---

## Safety Guarantees

1. ✅ **No files deleted** — All files moved to archive/ folders
2. ✅ **Git history preserved** — All commits remain accessible
3. ✅ **Reversible at any point** — Each step has documented reversal
4. ✅ **Checkpoint tags** — v4.5-pre-cleanup and v4.5-cleanup
5. ✅ **Dry-run testing** — Preview before execution
6. ✅ **Step-by-step verification** — Check after each step

---

**Ready to execute:** Yes, workflow is safe and reversible.
**Estimated time:** 10-15 minutes with verification steps.
**Risk level:** VERY LOW (all changes reversible).

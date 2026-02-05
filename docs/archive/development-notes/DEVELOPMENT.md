# Development Safety Guidelines

## CRITICAL: Preventing Data Loss

During Sprint 7.22 testing, production data was accidentally overwritten, losing Jan 20 articles. These guidelines prevent this from happening again.

---

## Rule 1: NEVER Run scrape.py During Development

**DO NOT** run the full pipeline (`scrape.py` → `verify.py` → `compare.py`) when testing extraction changes.

### ✅ SAFE: Use test_extraction.py

```bash
cd scraper
python3 test_extraction.py <article_url>
```

This script:
- ✓ Tests extraction functions
- ✓ Prints results to console
- ✓ NEVER modifies data/*.json files

### Example Usage

```bash
# Test a single article
python3 test_extraction.py https://buzz.bournemouth.ac.uk/2026/01/article-name/

# Test text patterns
python3 test_extraction.py --text "Name, who did thing, said something"
```

---

## Rule 2: Safety Check in scrape.py

The scraper now includes a **critical safety check** that prevents data loss:

```python
# CRITICAL SAFETY CHECK: Never reduce article count (prevents data loss)
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)
        existing_count = len(existing.get('articles', []))
        if len(articles) < existing_count:
            print("⚠️  SAFETY BLOCK: Refusing to overwrite data")
            print(f"New data has {len(articles)} articles, existing has {existing_count}")
            return
```

### What This Does

- **Blocks** any attempt to reduce article count
- **Prevents** accidental overwrites during testing
- **Requires** manual file deletion if intentional

### If You Need to Purge Data

```bash
# Only do this if you intend to start fresh
rm data/metrics_raw.json
python3 scrape_test.py  # Or scrape.py
```

---

## Rule 3: Backup Before Every Sprint

**FIRST ACTION** of every sprint:

```bash
# Create timestamped backup
cp data/metrics_verified.json data/backups/metrics_verified_$(date +%Y%m%d_%H%M%S).json

# Or quick backup
cp data/metrics_verified.json data/metrics_verified.backup.json
```

### Verify Backup

```bash
# Check backup exists and has data
python3 -c "import json; d=json.load(open('data/metrics_verified.backup.json')); print(f'Backup: {len(d[\"articles\"])} articles')"
```

---

## Rule 4: Verify Data Integrity After Changes

**BEFORE COMMITTING** any code changes, verify data integrity:

```bash
# Check article count and dates
python3 -c "
import json
d = json.load(open('data/metrics_verified.json'))
print(f'Articles: {len(d[\"articles\"])}')
dates = sorted(set(a['date'] for a in d['articles']))
print(f'Date range: {dates[0]} to {dates[-1]}')
print(f'Dates present: {dates}')
"
```

### Expected Output (as of 2026-01-20)

```
Articles: 40
Date range: 2026-01-16 to 2026-01-20
Dates present: ['2026-01-16', '2026-01-20']
```

### If Article Count Dropped

```bash
# DO NOT COMMIT! Restore from backup
cp data/metrics_verified.backup.json data/metrics_verified.json
```

---

## Safe Development Workflow

### 1. Before Starting Work

```bash
# Backup data
cp data/metrics_verified.json data/metrics_verified.backup.json

# Verify backup
ls -lh data/metrics_verified.backup.json
```

### 2. During Development

```bash
# Use safe test script
python3 test_extraction.py <article_url>

# DO NOT run scrape.py unless deploying to production
```

### 3. Testing Changes

```bash
# Test on specific article
python3 test_extraction.py https://buzz.bournemouth.ac.uk/2026/01/article/

# Or test text pattern
python3 test_extraction.py --text "Jadien Davies, who ran the event, said that..."
```

### 4. Before Committing

```bash
# Verify data integrity
python3 -c "import json; d=json.load(open('data/metrics_verified.json')); print(f'Articles: {len(d[\"articles\"])}')"

# Check for unexpected changes
git diff data/

# Only commit if data is intact
git add scraper/scrape.py
git commit -m "Sprint X.XX: Description"
```

---

## When to Run Full Pipeline

**ONLY** run `scrape.py` → `verify.py` → `compare.py` when:

1. **Deploying to production** (GitHub Actions)
2. **Intentionally collecting new data** (after verifying backup exists)
3. **Testing incremental scraping** (with backup and monitoring)

### Full Pipeline Checklist

- [ ] Backup exists: `data/metrics_verified.backup.json`
- [ ] Backup verified: Article count matches expected
- [ ] Understand what data will be scraped
- [ ] Monitor output for unexpected article counts
- [ ] Verify data integrity after pipeline completes

---

## Emergency: Data Loss Recovery

If data is accidentally lost:

```bash
# 1. Stop immediately - don't run anything else
# 2. Check if backup exists
ls -lh data/metrics_verified.backup.json

# 3. Restore from backup
cp data/metrics_verified.backup.json data/metrics_verified.json

# 4. Verify restoration
python3 -c "import json; d=json.load(open('data/metrics_verified.json')); print(f'Restored: {len(d[\"articles\"])} articles')"

# 5. Check git history for recent good version
git log --oneline data/metrics_verified.json
git show <commit>:data/metrics_verified.json > data/metrics_verified_restored.json
```

---

## Summary: Safety Checklist

**Every Sprint:**
- [ ] Create backup before starting
- [ ] Use `test_extraction.py` for testing, NOT `scrape.py`
- [ ] Verify data integrity before committing
- [ ] Never commit reduced article count without investigation

**When in Doubt:**
- ✅ Test with `test_extraction.py`
- ✅ Check backup exists
- ✅ Verify article count
- ❌ Don't run scrape.py during development
- ❌ Don't commit without verification

---

**Last Updated:** 2026-01-20 (Post Sprint 7.22 data loss incident)

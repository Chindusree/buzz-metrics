# BUzz Metrics — System Architecture

**Version:** 4.4 (live as of 2026-02-05)
**Status:** Production (newsday scraping complete, workflows disabled)

---

## System Overview

BUzz Metrics is an automated journalism quality measurement system consisting of:
- **Backend:** Python scrapers + LLM-based analysis
- **Frontend:** Static HTML/JS dashboard (GitHub Pages)
- **Data:** 85 JSON files (312 articles from January 2026)
- **Automation:** GitHub Actions workflows (now disabled)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         BUZZ METRICS                             │
│                    (Journalism Analytics)                        │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER
┌──────────────────────────────────────────────────────────────┐
│  BUzz Newsroom (WordPress)                                   │
│  └─ 312 articles (Jan 2026)                                  │
│     ├─ News (350w target)                                    │
│     ├─ Features (800w target)                                │
│     └─ Shorthand embeds (longform multimedia stories)        │
└──────────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────────┐
│  SCRAPING LAYER (Python + BeautifulSoup)                     │
│  ├─ scrape.py (3,453 lines) ← Main scraper                   │
│  │   ├─ WordPress HTML extraction (BeautifulSoup)            │
│  │   ├─ Shorthand iframe detection                           │
│  │   └─ Shorthand JSON API fallback                          │
│  ├─ verify.py (209 lines) ← Data validation                  │
│  └─ compare.py (376 lines) ← Reconciliation                  │
│                                                               │
│  Output: data/metrics_verified.json                          │
└──────────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────────┐
│  SCORING LAYER (Python + Groq LLM)                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ SEI Pipeline (Source Equity Index)                      ││
│  │ ├─ sei_production.py (18K)                              ││
│  │ ├─ sei_prompt_template.md                               ││
│  │ └─ Output: data/metrics_sei.json + docs/metrics_sei.json││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ORI Pipeline (Original Reporting Index)                 ││
│  │ ├─ ssi_score.py (23K)  ← "ssi" = legacy name            ││
│  │ ├─ ssi_prompt_v2.1.md / ngi_prompt_v2.2.md              ││
│  │ └─ Output: data/metrics_ssi.json + docs/metrics_ssi.json││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ BNS Pipeline (Breaking News Score)                      ││
│  │ └─ Integrated in scrape.py                              ││
│  │    Output: data/metrics_bns.json + docs/metrics_bns.json││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────────┐
│  PUBLICATION LAYER (GitHub Pages)                            │
│  ├─ docs/index.html (101K) ← Live dashboard                 │
│  ├─ docs/staff-test.html (101K) ← Dev version               │
│  └─ docs/metrics_*.json ← Deployed data                     │
│                                                               │
│  Merges SEI + ORI + BNS on client-side by article URL       │
└──────────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────────┐
│  USER LAYER                                                   │
│  └─ https://chindusree.github.io/buzz-metrics/              │
│     ├─ Filter by date/category                              │
│     ├─ View 3 index cards (SEI, ORI, BNS)                   │
│     └─ Explore article-level scores                         │
└──────────────────────────────────────────────────────────────┘

AUTOMATION (Disabled post-newsday)
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions Workflows                                    │
│  ├─ scrape.yml.disabled (was: hourly 8am-5pm Mon-Fri)       │
│  ├─ sei_daily.yml.disabled (was: 1pm + 4pm Mon-Fri)         │
│  └─ ssi_daily.yml.disabled (was: 5pm Mon-Fri)               │
└──────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
buzz-metrics/
├── README.md                          # Public documentation
├── CLEANUP_AUDIT.md                   # Maintenance plan
├── .env                               # API keys (gitignored)
├── .gitignore
│
├── .github/workflows/                 # Automation (disabled)
│   ├── scrape.yml.disabled
│   ├── sei_daily.yml.disabled
│   └── ssi_daily.yml.disabled
│
├── data/                              # Production data (85 files)
│   ├── metrics_sei.json              # SEI scores + article metadata
│   ├── metrics_ssi.json              # ORI scores (legacy name)
│   ├── metrics_bns.json              # Breaking news scores
│   ├── metrics_verified.json         # Scraper output
│   ├── imr_*.json                    # Inter-Model Reliability validation
│   └── [82 other JSON files]         # Historical/backup data
│
├── docs/                              # GitHub Pages deployment
│   ├── index.html                     # 🔴 LIVE DASHBOARD
│   ├── staff-test.html                # Development version
│   ├── metrics_sei.json              # Deployed SEI data
│   ├── metrics_ssi.json              # Deployed ORI data
│   ├── metrics_bns.json              # Deployed BNS data
│   ├── index-backup-20260204.html    # Pre-deployment backup
│   ├── [16 archived HTML files]       # Old development versions
│   │
│   └── decisions/                     # Architecture Decision Records
│       ├── 001-data-architecture.md   # Why separate JSON files
│       └── 002-ssi-ori-naming.md      # Why keep SSI filenames
│
├── scraper/                           # Backend processing
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── [PRODUCTION SCRIPTS - 6 files]
│   ├── scrape.py                      # Main scraper (132K)
│   ├── verify.py                      # Validation pipeline
│   ├── compare.py                     # Data reconciliation
│   ├── reconcile.py                   # Comparison logic
│   ├── sei_production.py              # SEI scoring
│   └── ssi_score.py                   # ORI scoring (legacy name)
│   │
│   ├── [LLM PROMPTS - 3 files]
│   ├── sei_prompt_template.md         # SEI scoring instructions
│   ├── ssi_prompt_v2.1.md             # ORI v2.1 prompt
│   └── ngi_prompt_v2.2.md             # ORI v2.2 prompt (NGI = old name)
│   │
│   ├── [DOCUMENTATION - 9 files]
│   ├── GROQ_SETUP.md
│   ├── BUG_RESOLUTION.md
│   ├── FIXES_VERIFICATION.md
│   ├── ANNE_MARIE_DEBUG_REPORT.md
│   ├── SHORTHAND_EXTRACTION_CLARIFICATION.md
│   └── COMPARISON_BEFORE_AFTER.md
│   │
│   └── [SUPPORT SCRIPTS - 47 files]
│       ├── debug_*.py (15 files)      # Debugging scripts
│       ├── test_*.py (21 files)       # Test/validation scripts
│       └── [11 migration/audit scripts]
│
└── analysis/                          # Investigation reports
    └── [10 markdown reports]
```

---

## Component Inventory

### Production Components (101 items)
| Category | Count | Purpose |
|----------|-------|---------|
| **Python scripts** | 6 | Scraping + scoring pipelines |
| **LLM prompts** | 3 | SEI + ORI scoring instructions |
| **Dashboards** | 2 | Live + development HTML |
| **Data files** | 85 | Article scores + metadata |
| **Workflows** | 3 | Automation (disabled) |
| **ADRs** | 2 | Architecture decisions |

### Support Components (115 items)
| Category | Count | Purpose |
|----------|-------|---------|
| **Debug scripts** | 36 | Development troubleshooting |
| **Migration scripts** | 11 | One-time data operations |
| **Archive HTML** | 17 | Old dashboard versions |
| **Documentation** | 9 | Technical notes |
| **Analysis reports** | 10 | Investigation findings |
| **Config files** | 5 | Git, Python, env |
| **Root docs** | 6 | README, cleanup, handover |
| **Backup data** | ~21 | Historical JSON files |

### Total Project Files: **216 files**
(Excluding venv/ and .git/)

---

## Data Flow

### 1. Article Collection
```
WordPress API → scrape.py → metrics_verified.json
- Extracts: headline, text, date, URL, category, word_count
- Handles: Shorthand embeds, iframe content
- Validates: Text extraction, duplicate detection
```

### 2. SEI Scoring (Source Equity Index)
```
metrics_verified.json → sei_production.py → metrics_sei.json
- LLM: Groq (Llama 3.1 70B)
- Prompt: sei_prompt_template.md
- Components: Inclusion, Agency, Perspectives
- Output: 266 scored articles (46 exempt)
```

### 3. ORI Scoring (Original Reporting Index)
```
metrics_verified.json → ssi_score.py → metrics_ssi.json
- LLM: Groq (Llama 3.1 70B)
- Prompt: ngi_prompt_v2.2.md (latest)
- Components: WE, SD, AR, CD, OI
- Output: 295 scored articles (17 exempt)
```

### 4. BNS Scoring (Breaking News Score)
```
Integrated in scrape.py → metrics_bns.json
- Compares BUzz publish time vs external media
- Output: 17 breaking news articles
```

### 5. Frontend Merge
```javascript
// Client-side merge in index.html
const merged = sei_articles.map(article => ({
  ...article,
  ssi_score: ssi_data.find(s => s.url === article.url)?.ssi_score,
  bns_score: bns_data.find(b => b.url === article.url)?.bns_score
}))
```

---

## Key Design Decisions

### 1. Separate JSON Files (ADR-001)
**Why:** Race condition prevention during concurrent workflow runs
- `metrics_sei.json` — Article metadata + SEI
- `metrics_ssi.json` — ORI scores only
- `metrics_bns.json` — BNS scores only

### 2. Keep SSI Filenames (ADR-002)
**Why:** Stability over consistency
- Backend: `ssi_score.py`, `metrics_ssi.json` (unchanged)
- Frontend: "ORI" everywhere visible to users
- No user impact, preserves git history

### 3. GitHub Pages Deployment
**Why:** Zero hosting cost, automatic SSL, version control
- Every push triggers rebuild (1-5 min)
- Data files live in `docs/` for direct access

### 4. Client-Side Data Merge
**Why:** Simplicity + independence
- No build step required
- Each index can be updated independently
- ~10 lines of JavaScript, <50ms latency

---

## Technology Stack

### Backend
- **Python 3.9+** — Scraping + scoring
- **BeautifulSoup4** — HTML parsing
- **spaCy** — Named entity recognition
- **Groq API** — LLM inference (Llama 3.1 70B)
- **requests** — HTTP client

### Frontend
- **Vanilla JavaScript** — No framework
- **HTML5 + CSS3** — Responsive design
- **GitHub Pages** — Static hosting

### Automation
- **GitHub Actions** — Scheduled workflows (now disabled)
- **Ubuntu 20.04** — Runner environment

### Data
- **JSON** — All data storage
- **85 files** — ~50MB total

---

## Validation & Quality

### Inter-Model Reliability (IMR)
- **Method:** 10% stratified sample, two independent LLMs
- **SEI:** 84.5% agreement (N=31)
- **ORI:** 85.0% agreement (N=30)
- **Interpretation:** Validates extraction consistency

### Exemptions
- **SEI:** 46 exempt (match reports, court registers, breaking, live blogs)
- **ORI:** 17 exempt (video/audio only, non-text content)

---

## Deployment Timeline

| Version | Date | Milestone |
|---------|------|-----------|
| v7.37.1-stable | 20 Jan | Pre-ORI rename |
| v8.2 | 22 Jan | Mobile responsiveness |
| v4.3-pre-live | 4 Feb | Staff dashboard complete |
| v4.4-live | 5 Feb | 🔴 **PRODUCTION DEPLOYMENT** |
| v4.5-pre-cleanup | 5 Feb | Checkpoint before cleanup |
| v4.5-cleanup | 5 Feb | ✅ **Archived 75 development files** |

---

## Maintenance Status

**As of 2026-02-05:**
- ✅ Newsday scraping complete (312 articles)
- ✅ All workflows disabled
- ✅ Dashboard live at chindusree.github.io/buzz-metrics
- ✅ Repository cleanup complete (75 files archived)
- ⏸️ No further automated updates planned
- 📦 Archive accessible via `archive/` folders and git tags

---

## For Developers

### Quick Start
```bash
git clone https://github.com/Chindusree/buzz-metrics.git
cd buzz-metrics/scraper
pip install -r requirements.txt
```

### Run Scoring Locally
```bash
# Requires GROQ_API_KEY in .env
python3 sei_production.py    # SEI scoring
python3 ssi_score.py          # ORI scoring
```

### View Dashboard Locally
```bash
cd docs
python3 -m http.server 8000
# Open http://localhost:8000
```

### Architecture Decisions
See `docs/decisions/*.md` for rationale behind key design choices.

---

**Generated:** 2026-02-05
**Maintained by:** Chindu Sreedharan (csreedharan@bournemouth.ac.uk)

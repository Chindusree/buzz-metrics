# BUzz Metrics Scraper

Automated tool to scrape articles from BUzz (https://buzz.bournemouth.ac.uk/), extract quality metrics, and display on a dashboard.

## Purpose
Track student journalism output for teaching and editorial feedback.

## Metrics Extracted
- Headline, Author, Date, Time
- Category (Sport/News/Features)
- Word count
- Quoted source count (with evidence trail)
- Content type (standard/shorthand)
- **SEI** (Source Evidence Index) - Citation quality score
- **SSI** (Story Substance Index) - Reporting depth and originality
- **BNS** (Breaking News Score) - Speed vs professional outlets

## Architecture
- `scraper/scrape.py` - Primary extraction (regex-based)
- `scraper/verify.py` - Secondary verification (spaCy NLP)
- `scraper/compare.py` - Cross-checks and flags discrepancies
- `scraper/sei_production.py` - Source Evidence Index scoring
- `scraper/ssi_score.py` - Story Substance Index scoring (v2.1)
- `data/` - JSON output files (see Data Files below)
- `docs/` - Dashboard (GitHub Pages)

## Data Files

| File | Contents | Updated By |
|------|----------|------------|
| `metrics_sei.json` | Base article data + SEI scores | sei_daily.yml (1pm, 4pm) |
| `metrics_ssi.json` | SSI scores and components | ssi_daily.yml |
| `metrics_bns.json` | BNS scores (BREAKING only) | TBD |

**Why separate files?** See [ADR-001: Data Architecture](docs/decisions/001-data-architecture.md)

## Setup
```bash
cd scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage
```bash
python scrape.py
```

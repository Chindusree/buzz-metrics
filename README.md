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

## Architecture
- `scraper/scrape.py` - Primary extraction (regex-based)
- `scraper/verify.py` - Secondary verification (spaCy NLP)
- `scraper/compare.py` - Cross-checks and flags discrepancies
- `data/` - JSON output files
- `docs/` - Dashboard (GitHub Pages)

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

#!/usr/bin/env python3
"""Migrate articles to Groq-detected sources"""
import json
import time
import shutil
from pathlib import Path
from scrape import analyze_article_with_groq, extract_shorthand_content_new
import requests
from bs4 import BeautifulSoup

DATA_FILE = Path(__file__).parent.parent / 'data' / 'metrics_raw.json'
BACKUP_FILE = Path(__file__).parent.parent / 'data' / 'metrics_raw_pre_migration.json'

def fetch_text(url):
    """Fetch article text from URL"""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'lxml')
    article = soup.find('article')
    return article.get_text(separator=' ', strip=True) if article else ""

def calculate_gender_breakdown(articles):
    """Calculate gender totals"""
    male = sum(1 for a in articles for s in a.get('source_evidence', []) if s.get('gender') == 'male')
    female = sum(1 for a in articles for s in a.get('source_evidence', []) if s.get('gender') == 'female')
    unknown = sum(1 for a in articles for s in a.get('source_evidence', []) if s.get('gender') == 'unknown')
    return {'male': male, 'female': female, 'unknown': unknown}

# Backup
if not BACKUP_FILE.exists():
    shutil.copy(DATA_FILE, BACKUP_FILE)
    print(f"Backup created: {BACKUP_FILE}")

# Load data
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Processing {len(data['articles'])} articles...\n")

# Process each article
for i, article in enumerate(data['articles'], 1):
    print(f"[{i}/{len(data['articles'])}] {article['headline'][:60]}")

    try:
        # Fetch text (different method for Shorthand vs WordPress)
        if article.get('shorthand_url'):
            result = extract_shorthand_content_new(article['shorthand_url'])
            text = result.get('body_text', '')
        else:
            text = fetch_text(article['url'])

        # Get Groq sources
        groq_sources = analyze_article_with_groq(text)

        if groq_sources is None:
            print(f"  ✗ Groq failed, skipping")
            continue

        # Update ONLY source fields
        article['source_evidence'] = groq_sources
        article['quoted_sources'] = len(groq_sources)

        print(f"  ✓ {len(groq_sources)} sources")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Checkpoint every 10
    if i % 10 == 0:
        data['gender_breakdown'] = calculate_gender_breakdown(data['articles'])
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  💾 Checkpoint saved\n")

    # Rate limit
    time.sleep(1)

# Final save
data['gender_breakdown'] = calculate_gender_breakdown(data['articles'])
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Complete! Gender breakdown: {data['gender_breakdown']}")

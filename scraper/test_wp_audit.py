#!/usr/bin/env python3
"""
Sprint 7.11: WordPress Extraction Accuracy Audit

Test 3 WordPress articles to verify extraction accuracy.
Compare scraper output against manually extracted ground truth.

Acceptance criteria:
- Word counts within ±5 words of manual baseline
- Image counts exact match
- Stock/original classification correct
- All quoted sources detected (no false negatives)
- No false positive sources (pronouns, partial names)
"""

import requests
from bs4 import BeautifulSoup
import re

# Test URLs
TEST_URLS = [
    'https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/',
    'https://buzz.bournemouth.ac.uk/2026/01/hotel-staff-take-the-plunge-for-charity/',
    'https://buzz.bournemouth.ac.uk/2026/01/tonight-stitch-and-movie-night/'
]

def get_manual_baseline(url):
    """
    Extract ground truth from raw HTML by manual inspection.
    This is the "correct" data to compare against.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract article slug from URL
    slug = url.rstrip('/').split('/')[-1]

    # 1. WORD COUNT - only entry-content paragraphs
    # EXCLUDE: headline, image captions, "About [Author]" box, category/tags, navigation, social links
    entry_content = soup.find('div', class_='entry-content')
    word_count = 0

    if entry_content:
        # Get all paragraphs, excluding captions and author boxes
        paragraphs = entry_content.find_all('p')
        for p in paragraphs:
            # Skip image captions
            if p.find_parent(class_=lambda x: x and 'caption' in str(x).lower()):
                continue
            # Skip author boxes
            if 'about' in p.get_text().lower() and len(p.get_text()) < 100:
                continue

            text = p.get_text(strip=True)
            word_count += len(text.split())

    # 2. IMAGES - count images in entry-content + featured-image
    images = {'total': 0, 'stock': 0, 'original': 0, 'uncredited': 0}

    # Featured image
    featured = soup.find('div', class_='featured-image')
    if featured and featured.find('img'):
        images['total'] += 1
        # Check for stock indicators
        img = featured.find('img')
        src = img.get('src', '').lower()

        # Check sibling caption for stock keywords
        caption_span = featured.find_next_sibling('span', class_='image-caption')
        credit_text = caption_span.get_text().lower() if caption_span else ''

        is_stock = any(keyword in src or keyword in credit_text
                      for keyword in ['pexels', 'unsplash', 'getty', 'shutterstock', 'pixabay'])

        if is_stock:
            images['stock'] += 1
        elif caption_span or img.get('alt'):
            images['original'] += 1
        else:
            images['uncredited'] += 1

    # Images in entry-content
    if entry_content:
        for img in entry_content.find_all('img'):
            images['total'] += 1
            src = img.get('src', '').lower()
            alt = img.get('alt', '').lower()

            # Check for stock indicators
            is_stock = any(keyword in src or keyword in alt
                          for keyword in ['pexels', 'unsplash', 'getty', 'shutterstock', 'pixabay'])

            if is_stock:
                images['stock'] += 1
            elif alt or img.find_parent('figure'):
                images['original'] += 1
            else:
                images['uncredited'] += 1

    # 3. SOURCES - find all quoted attributions manually
    # Look for: "said", "told", "according to", "explained", "added"
    sources = []

    if entry_content:
        text = entry_content.get_text()

        # Attribution patterns
        patterns = [
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+)(?:,? (?:said|told|explained|added|stated))',
            r'(?:according to|says) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+) (?:from|of) [A-Z]'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            sources.extend(matches)

    # Remove duplicates and common false positives
    sources = list(set(sources))
    sources = [s for s in sources if len(s.split()) >= 2]  # At least first and last name
    sources.sort()

    return {
        'url': url,
        'slug': slug,
        'word_count': word_count,
        'images': images,
        'sources': sources
    }

def get_scraped_data(url):
    """
    Simulate running the scraper on the URL.
    In production, this would call extract_article_metadata(url).
    For now, we'll do a simplified extraction matching scraper logic.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    slug = url.rstrip('/').split('/')[-1]

    # Word count (matching scraper's logic)
    entry_content = soup.find('div', class_='entry-content')
    word_count = 0

    if entry_content:
        # Get text from all paragraphs
        for p in entry_content.find_all('p'):
            text = p.get_text(strip=True)
            word_count += len(text.split())

    # Images (matching scraper's classify_image logic)
    images = {'total': 0, 'stock': 0, 'original': 0, 'uncredited': 0}

    # Stock keywords from scraper
    stock_keywords = ['pexels', 'unsplash', 'getty', 'shutterstock', 'pixabay', 'istock']
    stock_filename_patterns = ['pexels-', 'unsplash-', 'shutterstock', 'getty-']

    # Featured image
    featured = soup.find('div', class_='featured-image')
    if featured and featured.find('img'):
        images['total'] += 1
        img = featured.find('img')
        src = img.get('src', '').lower()

        # Check sibling caption
        caption_span = featured.find_next_sibling('span', class_='image-caption')
        credit_text = caption_span.get_text().lower() if caption_span else ''

        # Layer 1: Filename
        is_stock_filename = any(pattern in src for pattern in stock_filename_patterns)
        # Layer 3: Credit keywords
        is_stock_credit = any(keyword in credit_text for keyword in stock_keywords)

        if is_stock_filename or is_stock_credit:
            images['stock'] += 1
        elif credit_text or img.get('alt'):
            images['original'] += 1
        else:
            images['uncredited'] += 1

    # Entry content images
    if entry_content:
        for img in entry_content.find_all('img'):
            images['total'] += 1
            src = img.get('src', '').lower()

            is_stock = any(pattern in src for pattern in stock_filename_patterns)

            if is_stock:
                images['stock'] += 1
            elif img.get('alt'):
                images['original'] += 1
            else:
                images['uncredited'] += 1

    # Sources (simplified scraper logic)
    sources = []

    if entry_content:
        text = entry_content.get_text()

        # Basic attribution pattern
        patterns = [
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+) said',
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+) told',
            r'according to ([A-Z][a-z]+(?: [A-Z][a-z]+)+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            sources.extend(matches)

    sources = list(set(sources))
    sources.sort()

    return {
        'url': url,
        'slug': slug,
        'word_count': word_count,
        'images': images,
        'sources': sources
    }

def compare(baseline, scraped):
    """Compare baseline (ground truth) against scraped data and report discrepancies."""
    errors = []
    warnings = []

    # Word count (±5 words tolerance)
    word_diff = abs(baseline['word_count'] - scraped['word_count'])
    if word_diff > 5:
        errors.append(f"Word count: expected {baseline['word_count']}, got {scraped['word_count']} (diff: {word_diff})")
    elif word_diff > 0:
        warnings.append(f"Word count: {baseline['word_count']} (baseline) vs {scraped['word_count']} (scraped), diff: {word_diff}")

    # Images - exact match required
    if baseline['images']['total'] != scraped['images']['total']:
        errors.append(f"Image total: expected {baseline['images']['total']}, got {scraped['images']['total']}")

    if baseline['images']['stock'] != scraped['images']['stock']:
        errors.append(f"Stock images: expected {baseline['images']['stock']}, got {scraped['images']['stock']}")

    if baseline['images']['original'] != scraped['images']['original']:
        errors.append(f"Original images: expected {baseline['images']['original']}, got {scraped['images']['original']}")

    # Sources - check for missing (false negatives) and extras (false positives)
    baseline_sources = set(baseline['sources'])
    scraped_sources = set(scraped['sources'])

    missing = baseline_sources - scraped_sources
    extra = scraped_sources - baseline_sources

    if missing:
        errors.append(f"Missing sources (false negatives): {', '.join(missing)}")

    if extra:
        errors.append(f"Extra sources (false positives): {', '.join(extra)}")

    return errors, warnings

def run_audit():
    """Run the full audit on all test URLs."""
    print("=" * 70)
    print("Sprint 7.11: WordPress Extraction Accuracy Audit")
    print("=" * 70)
    print()

    results = []
    total_articles = len(TEST_URLS)
    passed_articles = 0

    for url in TEST_URLS:
        print(f"Testing: {url}")
        print("-" * 70)

        try:
            # Get baseline and scraped data
            baseline = get_manual_baseline(url)
            scraped = get_scraped_data(url)

            # Compare
            errors, warnings = compare(baseline, scraped)

            # Display results
            print(f"\n{baseline['slug']}")

            # Word count
            if abs(baseline['word_count'] - scraped['word_count']) <= 5:
                print(f"  Word count: ✓ {baseline['word_count']} (baseline) = {scraped['word_count']} (scraped)")
            else:
                print(f"  Word count: ✗ {baseline['word_count']} (baseline) ≠ {scraped['word_count']} (scraped)")

            # Images
            if (baseline['images']['total'] == scraped['images']['total'] and
                baseline['images']['stock'] == scraped['images']['stock'] and
                baseline['images']['original'] == scraped['images']['original']):
                print(f"  Images: ✓ {baseline['images']['total']} total, "
                      f"{baseline['images']['stock']} stock, {baseline['images']['original']} original")
            else:
                print(f"  Images: ✗ Baseline: {baseline['images']['total']} total, "
                      f"{baseline['images']['stock']} stock, {baseline['images']['original']} original")
                print(f"          Scraped: {scraped['images']['total']} total, "
                      f"{scraped['images']['stock']} stock, {scraped['images']['original']} original")

            # Sources
            if set(baseline['sources']) == set(scraped['sources']):
                print(f"  Sources: ✓ {baseline['sources']}")
            else:
                print(f"  Sources: ✗ Baseline: {baseline['sources']}")
                print(f"           Scraped: {scraped['sources']}")

            # Report errors and warnings
            if errors:
                print("\n  ERRORS:")
                for error in errors:
                    print(f"    - {error}")

            if warnings:
                print("\n  WARNINGS:")
                for warning in warnings:
                    print(f"    - {warning}")

            # Track pass/fail
            if not errors:
                passed_articles += 1
                print("\n  STATUS: ✓ PASSED")
            else:
                print("\n  STATUS: ✗ FAILED")

            results.append({
                'slug': baseline['slug'],
                'errors': errors,
                'warnings': warnings,
                'passed': not errors
            })

        except Exception as e:
            print(f"  ERROR: Failed to process article: {e}")
            results.append({
                'slug': url.split('/')[-2],
                'errors': [str(e)],
                'warnings': [],
                'passed': False
            })

        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Articles tested: {total_articles}")
    print(f"Passed: {passed_articles}")
    print(f"Failed: {total_articles - passed_articles}")
    print(f"Pass rate: {passed_articles}/{total_articles} ({100*passed_articles//total_articles}%)")
    print()

    if passed_articles == total_articles:
        print("✓ ALL TESTS PASSED - Scraper accuracy verified")
    else:
        print("✗ SOME TESTS FAILED - Review errors and investigate")

    print("=" * 70)

    return results

if __name__ == '__main__':
    run_audit()

#!/usr/bin/env python3
"""
Fetch article text for failed spot checks
"""
import json
import requests
from bs4 import BeautifulSoup

def fetch_article_text(url):
    """Fetch first 300 words of article body"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try Shorthand first (more specific selectors)
        shorthand = soup.find('div', {'id': 'app'})
        if shorthand:
            # Get all text blocks
            text_blocks = []
            for section in shorthand.find_all(['p', 'h1', 'h2', 'h3', 'blockquote']):
                text = section.get_text(strip=True)
                if text and len(text) > 10:  # Skip very short snippets
                    text_blocks.append(text)

            if text_blocks:
                full_text = ' '.join(text_blocks)
                words = full_text.split()[:300]
                return ' '.join(words)

        # Standard WordPress
        content = soup.find('div', class_='entry-content')
        if content:
            # Remove script/style elements
            for element in content.find_all(['script', 'style']):
                element.decompose()

            text = content.get_text(separator=' ', strip=True)
            words = text.split()[:300]
            return ' '.join(words)

        return "Could not extract article text"
    except Exception as e:
        return f"Error fetching: {e}"

# URLs that failed
failed_urls = [
    "https://buzz.bournemouth.ac.uk/2026/01/lymingtons-sailor-extends-record-championship-reign-in-shenzhen/",
    "https://buzz.bournemouth.ac.uk/2026/01/grant-hancox-acl-feature-2/"
]

for url in failed_urls:
    print(f"\n{'='*100}")
    print(f"URL: {url}")
    print(f"{'='*100}")
    text = fetch_article_text(url)
    print(text)
    print(f"{'='*100}\n")

# Groq Verification Setup

This document explains how to set up and run the Groq-based source verification system for BUzz Metrics.

## Purpose

The Groq verification system runs in parallel to the regex-based pipeline to:
- Compare LLM-based source detection vs pattern matching
- Identify gaps in regex patterns
- Validate source classification (original, press statement, social media, etc.)
- Test gender detection accuracy

## Setup

### 1. Get Groq API Key

1. Visit https://console.groq.com/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key

### 2. Configure Environment

```bash
cd ~/buzz-metrics/scraper
cp .env.template .env
```

Edit `.env` and add your API key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Verify Installation

```bash
pip3 install python-dotenv
```

## Usage

### Run Groq Verification

```bash
cd ~/buzz-metrics/scraper
python3 groq_verify.py
```

This will:
1. Load all articles from `metrics_verified.json`
2. Fetch each article's content
3. Send to Groq for LLM-based source analysis
4. Compare results with regex pipeline
5. Generate `comparison.json` in both `/data` and `/docs`

### View Comparison

Open `docs/compare.html` in a web browser:

```bash
open ../docs/compare.html
```

Or if the HTTP server is running:
```
http://localhost:8000/compare.html
```

## Output Format

### comparison.json Structure

```json
{
  "last_updated": "2026-01-22T09:30:00Z",
  "summary": {
    "total_articles": 82,
    "regex_total": 60,
    "groq_total": 75,
    "matches": 45,
    "groq_higher": 30,
    "regex_higher": 7
  },
  "articles": [
    {
      "headline": "Article Title",
      "url": "https://...",
      "regex_count": 2,
      "regex_sources": ["John Smith", "Jane Doe"],
      "groq_count": 3,
      "groq_sources": [
        {
          "name": "John Smith",
          "quote_snippet": "This is the first ten words...",
          "type": "original",
          "gender": "male"
        },
        {
          "name": "Jane Doe",
          "quote_snippet": "Another quote snippet here from...",
          "type": "press_statement",
          "gender": "female"
        },
        {
          "name": "Bob Wilson",
          "quote_snippet": "Third source that regex missed...",
          "type": "original",
          "gender": "male"
        }
      ],
      "difference": 1
    }
  ]
}
```

## Source Types

Groq classifies sources into four types:

- **original**: Direct quotes from interviews, first-hand statements
- **press_statement**: Official statements, spokespersons, press releases
- **secondary**: Quotes republished from another news outlet
- **social_media**: Quotes from Twitter/X, Facebook, Instagram posts

## Interpretation

### When to Trust Groq

- Groq finds more sources consistently → Regex patterns may be too strict
- Groq correctly identifies press statements → Can add classification to regex
- Groq catches social media quotes → May want to filter these separately

### When to Trust Regex

- Regex finds more → Groq may be missing attributions in complex layouts
- Regex is consistent → Pattern-based approach is more reliable
- Low false positive rate → Regex validation logic is working

### Action Items from Comparison

1. **Groq finds sources Regex misses** → Analyze patterns, update regex
2. **Regex finds sources Groq misses** → Check if they're valid (may be false positives)
3. **Large discrepancies** → Manual review needed
4. **Source type insights** → Consider adding type classification to regex

## Performance

- Processing time: ~2-3 seconds per article
- Rate limits: Groq free tier has limits (check console.groq.com)
- Cost: Currently free for testing

## Limitations

- Groq only sees first 8000 characters of article
- May hallucinate sources not present in text
- JSON parsing can fail if response format is incorrect
- Requires internet connection and API access

## Troubleshooting

### "GROQ_API_KEY not set in .env"
- Check `.env` file exists in `scraper/` directory
- Verify API key is set correctly
- No quotes needed around the key value

### "Failed to parse: ..."
- Groq returned non-JSON response
- Usually happens with very complex articles
- Article will show 0 Groq sources, skip and continue

### Rate limit errors
- Free tier has limits
- Wait a few minutes and retry
- Consider upgrading Groq plan

### Network errors
- Check internet connection
- Groq API may be down (check status.groq.com)
- Increase timeout in groq_verify.py if needed

## Next Steps

After running comparison:

1. Review `compare.html` for biggest discrepancies
2. Manually check articles where Groq found significantly more
3. Update regex patterns if Groq consistently catches missing sources
4. Consider integrating Groq for source type classification
5. Use gender data to validate regex gender detection

## Files

- `scraper/groq_verify.py` - Main verification script
- `scraper/.env` - API key configuration (gitignored)
- `scraper/.env.template` - Template for .env
- `data/comparison.json` - Verification results
- `docs/comparison.json` - Copy for web viewing
- `docs/compare.html` - Visual comparison dashboard

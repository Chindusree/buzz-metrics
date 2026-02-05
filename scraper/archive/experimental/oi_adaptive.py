#!/usr/bin/env python3
"""
Adaptive Originality Index (OI) Detection
No hardcoded news organizations — detects any external attribution
"""

import re


def get_oi_adaptive(source_name, snippet, headline):
    """
    Calculate Originality Index using adaptive pattern matching.
    No hardcoded news orgs — catches any external attribution.

    Args:
        source_name: Name of the quoted source
        snippet: Quote snippet/context from article
        headline: Article headline

    Returns:
        (oi_score, reason): Tuple of float score (0.0-1.0) and string explanation
    """
    name_lower = source_name.lower()
    snippet_lower = (snippet or '').lower()
    headline_lower = headline.lower()

    # === TIER 1: EXPLICIT ORIGINAL (1.0) ===
    # Attribution to BUzz specifically
    original_patterns = [
        r'told buzz',
        r'speaking to buzz',
        r'in an interview with buzz',
        r'buzz understands',
        r'said to buzz',
    ]
    for pattern in original_patterns:
        if re.search(pattern, snippet_lower):
            return 1.0, "original: told BUzz"

    # === TIER 2: STORY SUBJECT (1.0) ===
    # Source name appears in headline — likely interviewed
    name_parts = [p for p in name_lower.split() if len(p) > 3]
    if any(part in headline_lower for part in name_parts):
        return 1.0, "original: story subject"

    # === TIER 3: EXTERNAL ATTRIBUTION (0.3) ===
    # "told [not BUzz]", "speaking to [not BUzz]", "interview with [not BUzz]"
    external_attribution = [
        r'told (?!buzz)\w+',              # told BBC, told Sky, told reporters
        r'speaking to (?!buzz)\w+',        # speaking to CNN
        r'in an interview with (?!buzz)',  # in an interview with Guardian
        r'said to (?!buzz)\w+',            # said to Reuters
    ]
    for pattern in external_attribution:
        if re.search(pattern, snippet_lower):
            return 0.3, "secondary: external attribution"

    # === TIER 4: WIRE/AGENCY INDICATORS (0.3) ===
    # Generic patterns that indicate lifted content
    wire_patterns = [
        r'according to\s+\w+',             # according to [anyone]
        r'\w+\s+reports\s+that',           # [org] reports that
        r'reported by\s+\w+',              # reported by [org]
        r'as reported\s+(by|in)',          # as reported by/in
        r'said in a (statement|release)',  # said in a statement
        r'(posted|wrote|tweeted)\s+on',    # posted on X/Twitter
        r'at a press conference',          # at a press conference
        r'during a press conference',
        r'in a press release',
        r'issued a statement',
    ]
    for pattern in wire_patterns:
        if re.search(pattern, snippet_lower):
            return 0.3, "secondary: wire/statement"

    # === TIER 5: NATIONAL FIGURE DETECTION (0.3) ===
    # Detect by title/role, not by name
    national_titles = [
        r'prime minister',
        r'(home|foreign|defence) secretary',
        r'chancellor of the exchequer',
        r'(labour|conservative|liberal democrat) leader',
        r'mp for (?!bournemouth|poole|dorset|mid dorset|north dorset|south dorset|west dorset)',  # MP but not local
        r'(us |american )?president',
        r'ceo of (tesla|meta|amazon|apple|google|microsoft|x corp)',
        r'(king|prince|princess|duke|duchess) (charles|william|harry|george|kate|meghan)',
    ]
    for pattern in national_titles:
        if re.search(pattern, snippet_lower) or re.search(pattern, name_lower):
            return 0.3, "secondary: national figure"

    # === TIER 6: INSTITUTIONAL SPOKESMAN (0.5-0.6) ===
    if re.search(r'spokesman|spokesperson|representative|official', name_lower):
        # Check if local
        local_markers = ['dorset', 'bournemouth', 'poole', 'bcp', 'christchurch',
                         'weymouth', 'wareham', 'ferndown', 'ringwood', 'wimborne']
        is_local = any(loc in snippet_lower or loc in name_lower for loc in local_markers)

        if is_local:
            return 0.6, "institutional: local"
        else:
            return 0.5, "institutional: national"

    # === TIER 7: GOOD FAITH DEFAULT (0.8) ===
    # No indicators of secondary sourcing — assume original
    return 0.8, "good faith: local source assumed"


if __name__ == "__main__":
    # Run the test as requested
    import json

    print("=" * 95)
    print("ADAPTIVE OI DETECTION TEST")
    print("=" * 95)

    # Load verified data
    with open('../data/metrics_verified.json') as f:
        ver = json.load(f)

    # Test on variety of stories
    test_keywords = [
        ('musk', 'Tech billionaire'),
        ('starmer', 'Prime Minister'),
        ('police', 'Police story'),
        ('council', 'Council story'),
        ('student', 'Student story'),
        ('bournemouth', 'Local story'),
    ]

    for keyword, label in test_keywords:
        matches = [a for a in ver['articles']
                   if keyword in a.get('headline', '').lower()
                   and a.get('source_evidence', [])][:1]

        if matches:
            a = matches[0]
            print(f"\n[{label}] {a['headline'][:50]}")

            oi_scores = []
            for s in a.get('source_evidence', []):
                name = s.get('name', 'Unknown')
                snippet = s.get('snippet', '')
                oi, reason = get_oi_adaptive(name, snippet, a['headline'])
                oi_scores.append(oi)
                print(f"  • {name[:35]:<35} OI={oi:.1f}  ({reason})")

            if oi_scores:
                print(f"  ▸ Average OI: {sum(oi_scores)/len(oi_scores):.2f}")

    print("\n" + "=" * 95)
    print("SYNTHETIC TEST CASES")
    print("=" * 95)

    synthetic = [
        ("Boris Johnson", "The Prime Minister told Sky News that...", "UK economy faces challenges"),
        ("Joe Biden", "The US President said in a statement...", "US foreign policy shift"),
        ("Sarah Mitchell", "She told BUzz about her experience...", "Local woman wins award"),
        ("Thames Valley Police spokesman", "A spokesman said officers responded...", "Man arrested in Reading"),
        ("Dorset Police spokesman", "A Dorset Police spokesman confirmed...", "Crash closes A35"),
        ("Dr James Wilson", "The researcher explained his findings...", "BU study reveals health trends"),
        ("Elon Musk", "Musk posted on X that the company...", "Tesla announces new factory"),
        ("Local MP", "The MP for Bournemouth East said...", "MP backs local hospital"),
    ]

    for name, snippet, headline in synthetic:
        oi, reason = get_oi_adaptive(name, snippet, headline)
        print(f"  {name:<30} OI={oi:.1f}  ({reason})")
        print(f"    \"{snippet[:50]}...\"")

    print("\n" + "=" * 95)

#!/usr/bin/env python3
"""
Test source detection fixes for two specific cases:
1. Iraola quote with "described" (should be detected)
2. Dorset Police paraphrase (should NOT be detected)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape import extract_quoted_sources

# Test Case 1: Iraola with "described" - should DETECT
test1_text = """
Bournemouth secured a stunning victory over Liverpool.
Andoni Iraola described it as "probably the best moment to score"
after his team's late winner sealed the three points.
"""

print("="*80)
print("TEST 1: Iraola with 'described' (should be DETECTED)")
print("="*80)
print("Text:", test1_text.strip())
print()

sources1 = extract_quoted_sources(test1_text)
print(f"Sources detected: {len(sources1)}")
for src in sources1:
    print(f"  - {src['name']} (position: {src['position']})")
    print(f"    Quote: {src['quote_snippet'][:50]}")
print()

if len(sources1) > 0 and any('Iraola' in s['name'] for s in sources1):
    print("✅ PASS: Iraola detected correctly")
else:
    print("❌ FAIL: Iraola not detected")
print()

# Test Case 2: Dorset Police paraphrase - should NOT detect
test2_text = """
Emergency services responded to a serious crash in Christchurch on Tuesday afternoon.
A spokesperson for Dorset Police said officers attended the scene at around 2pm.
The road was closed for several hours while investigation work took place.
"""

print("="*80)
print("TEST 2: Dorset Police paraphrase (should NOT be detected)")
print("="*80)
print("Text:", test2_text.strip())
print()

sources2 = extract_quoted_sources(test2_text)
print(f"Sources detected: {len(sources2)}")
for src in sources2:
    print(f"  - {src['name']} (position: {src['position']})")
    print(f"    Quote: {src['quote_snippet'][:50] if src['quote_snippet'] else '(no quote)'}")
print()

if len(sources2) == 0 or not any('Police' in s['name'] or 'Dorset' in s['name'] for s in sources2):
    print("✅ PASS: Dorset Police paraphrase correctly rejected")
else:
    print("❌ FAIL: Dorset Police paraphrase incorrectly detected")
print()

# Test Case 3: Dorset Police WITH quote - SHOULD detect
test3_text = """
Emergency services responded to a serious crash in Christchurch on Tuesday afternoon.
A spokesperson for Dorset Police said: "Officers attended the scene at around 2pm and
found a vehicle had collided with a barrier."
The road was closed for several hours.
"""

print("="*80)
print("TEST 3: Dorset Police WITH quote (should be DETECTED)")
print("="*80)
print("Text:", test3_text.strip())
print()

sources3 = extract_quoted_sources(test3_text)
print(f"Sources detected: {len(sources3)}")
for src in sources3:
    print(f"  - {src['name']} (position: {src['position']})")
    print(f"    Quote: {src['quote_snippet'][:50]}")
print()

if len(sources3) > 0:
    print("✅ PASS: Dorset Police WITH quote detected correctly")
else:
    print("❌ FAIL: Dorset Police WITH quote not detected")
print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Test 1 (Iraola 'described'): {'PASS' if len(sources1) > 0 else 'FAIL'}")
print(f"Test 2 (Dorset Police paraphrase): {'PASS' if len(sources2) == 0 else 'FAIL'}")
print(f"Test 3 (Dorset Police with quote): {'PASS' if len(sources3) > 0 else 'FAIL'}")

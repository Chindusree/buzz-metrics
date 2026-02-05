#!/usr/bin/env python3
"""
Sprint 7.17: Test Embedded Video/Audio Detection

Problem: We track word count, sources, and images, but don't capture video/audio embeds.
Students' multimedia work (YouTube interviews, SoundCloud clips, etc.) gets no credit.

Fix: Detect embedded video and audio content in articles.

Platforms:
- YouTube (iframe youtube.com or youtu.be)
- Vimeo (iframe vimeo.com)
- SoundCloud (iframe soundcloud.com)
- Spotify (iframe spotify.com)
- HTML5 native (<video>, <audio> tags)
- BU Media (iframe bournemouth.ac.uk)

Test cases:
✓ YouTube embed → video_count: 1
✓ SoundCloud embed → audio_count: 1
✓ HTML5 video → video_count: 1
✓ HTML5 audio → audio_count: 1
✓ Multiple embeds → correct counts
✓ No embeds → video_count: 0, audio_count: 0
"""

import sys
import os
from bs4 import BeautifulSoup

# Add scraper directory to path
scraper_dir = os.path.dirname(os.path.abspath(__file__))
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

from scrape import extract_embeds


def test_video_platforms():
    """
    Test video platform detection (YouTube, Vimeo, BU Media)
    """
    print("=" * 70)
    print("Test 1: Video Platform Detection")
    print("=" * 70)
    print()

    test_cases = [
        {
            'name': 'YouTube embed',
            'html': '<iframe src="https://www.youtube.com/embed/abc123"></iframe>',
            'expected_video': 1,
            'expected_audio': 0,
            'expected_platforms': ['youtube']
        },
        {
            'name': 'YouTube short URL',
            'html': '<iframe src="https://youtu.be/xyz789"></iframe>',
            'expected_video': 1,
            'expected_audio': 0,
            'expected_platforms': ['youtube']
        },
        {
            'name': 'Vimeo embed',
            'html': '<iframe src="https://player.vimeo.com/video/123456"></iframe>',
            'expected_video': 1,
            'expected_audio': 0,
            'expected_platforms': ['vimeo']
        },
        {
            'name': 'BU Media embed',
            'html': '<iframe src="https://media.bournemouth.ac.uk/video/player.php?id=123"></iframe>',
            'expected_video': 1,
            'expected_audio': 0,
            'expected_platforms': ['bu-media']
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        name = test['name']
        html = test['html']
        expected_video = test['expected_video']
        expected_audio = test['expected_audio']
        expected_platforms = test['expected_platforms']

        soup = BeautifulSoup(html, 'lxml')
        result = extract_embeds(soup)

        video_count = result['video_count']
        audio_count = result['audio_count']
        platforms = [e['platform'] for e in result['video_evidence']]

        if video_count == expected_video and audio_count == expected_audio and platforms == expected_platforms:
            print(f"✓ PASS - {name}")
            print(f"  Video: {video_count}, Audio: {audio_count}, Platforms: {platforms}")
            passed += 1
        else:
            print(f"✗ FAIL - {name}")
            print(f"  Expected: V:{expected_video}, A:{expected_audio}, P:{expected_platforms}")
            print(f"  Got: V:{video_count}, A:{audio_count}, P:{platforms}")
            failed += 1

    print()
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_audio_platforms():
    """
    Test audio platform detection (SoundCloud, Spotify)
    """
    print("=" * 70)
    print("Test 2: Audio Platform Detection")
    print("=" * 70)
    print()

    test_cases = [
        {
            'name': 'SoundCloud embed',
            'html': '<iframe src="https://w.soundcloud.com/player/?url=https://soundcloud.com/artist/track"></iframe>',
            'expected_video': 0,
            'expected_audio': 1,
            'expected_platforms': ['soundcloud']
        },
        {
            'name': 'Spotify embed',
            'html': '<iframe src="https://open.spotify.com/embed/episode/abc123"></iframe>',
            'expected_video': 0,
            'expected_audio': 1,
            'expected_platforms': ['spotify']
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        name = test['name']
        html = test['html']
        expected_video = test['expected_video']
        expected_audio = test['expected_audio']
        expected_platforms = test['expected_platforms']

        soup = BeautifulSoup(html, 'lxml')
        result = extract_embeds(soup)

        video_count = result['video_count']
        audio_count = result['audio_count']
        platforms = [e['platform'] for e in result['audio_evidence']]

        if video_count == expected_video and audio_count == expected_audio and platforms == expected_platforms:
            print(f"✓ PASS - {name}")
            print(f"  Video: {video_count}, Audio: {audio_count}, Platforms: {platforms}")
            passed += 1
        else:
            print(f"✗ FAIL - {name}")
            print(f"  Expected: V:{expected_video}, A:{expected_audio}, P:{expected_platforms}")
            print(f"  Got: V:{video_count}, A:{audio_count}, P:{platforms}")
            failed += 1

    print()
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_html5_native():
    """
    Test HTML5 native video/audio tags
    """
    print("=" * 70)
    print("Test 3: HTML5 Native Elements")
    print("=" * 70)
    print()

    test_cases = [
        {
            'name': 'HTML5 video with src',
            'html': '<video src="video.mp4"></video>',
            'expected_video': 1,
            'expected_audio': 0
        },
        {
            'name': 'HTML5 video with source tag',
            'html': '<video><source src="video.webm" type="video/webm"></video>',
            'expected_video': 1,
            'expected_audio': 0
        },
        {
            'name': 'HTML5 audio with src',
            'html': '<audio src="audio.mp3"></audio>',
            'expected_video': 0,
            'expected_audio': 1
        },
        {
            'name': 'HTML5 audio with source tag',
            'html': '<audio><source src="podcast.ogg" type="audio/ogg"></audio>',
            'expected_video': 0,
            'expected_audio': 1
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        name = test['name']
        html = test['html']
        expected_video = test['expected_video']
        expected_audio = test['expected_audio']

        soup = BeautifulSoup(html, 'lxml')
        result = extract_embeds(soup)

        video_count = result['video_count']
        audio_count = result['audio_count']

        if video_count == expected_video and audio_count == expected_audio:
            print(f"✓ PASS - {name}")
            print(f"  Video: {video_count}, Audio: {audio_count}")
            passed += 1
        else:
            print(f"✗ FAIL - {name}")
            print(f"  Expected: V:{expected_video}, A:{expected_audio}")
            print(f"  Got: V:{video_count}, A:{audio_count}")
            failed += 1

    print()
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print()

    return failed == 0


def test_multiple_embeds():
    """
    Test articles with multiple embeds
    """
    print("=" * 70)
    print("Test 4: Multiple Embeds")
    print("=" * 70)
    print()

    html = '''
    <article>
        <iframe src="https://www.youtube.com/embed/video1"></iframe>
        <iframe src="https://player.vimeo.com/video/12345"></iframe>
        <iframe src="https://w.soundcloud.com/player/?url=track1"></iframe>
        <video src="local-video.mp4"></video>
        <audio><source src="podcast.mp3"></audio>
    </article>
    '''

    soup = BeautifulSoup(html, 'lxml')
    result = extract_embeds(soup)

    expected_video = 3  # YouTube + Vimeo + HTML5 video
    expected_audio = 2  # SoundCloud + HTML5 audio

    video_count = result['video_count']
    audio_count = result['audio_count']

    print(f"HTML contains:")
    print(f"  - 1 YouTube embed")
    print(f"  - 1 Vimeo embed")
    print(f"  - 1 SoundCloud embed")
    print(f"  - 1 HTML5 video")
    print(f"  - 1 HTML5 audio")
    print()
    print(f"Expected: V:{expected_video}, A:{expected_audio}")
    print(f"Got: V:{video_count}, A:{audio_count}")
    print()

    if video_count == expected_video and audio_count == expected_audio:
        print("✓ PASS - Multiple embeds detected correctly")
        return True
    else:
        print("✗ FAIL - Incorrect counts")
        return False


def test_no_embeds():
    """
    Test articles with no embeds
    """
    print("=" * 70)
    print("Test 5: No Embeds")
    print("=" * 70)
    print()

    html = '''
    <article>
        <p>This is a text-only article.</p>
        <img src="image.jpg" alt="Photo">
        <p>No video or audio content.</p>
    </article>
    '''

    soup = BeautifulSoup(html, 'lxml')
    result = extract_embeds(soup)

    expected_video = 0
    expected_audio = 0

    video_count = result['video_count']
    audio_count = result['audio_count']

    print(f"HTML contains: Text and image only (no embeds)")
    print(f"Expected: V:{expected_video}, A:{expected_audio}")
    print(f"Got: V:{video_count}, A:{audio_count}")
    print()

    if video_count == expected_video and audio_count == expected_audio:
        print("✓ PASS - No false positives")
        return True
    else:
        print("✗ FAIL - Detected embeds where none exist")
        return False


if __name__ == '__main__':
    print("Sprint 7.17: Embedded Video/Audio Detection - Test Suite")
    print()

    all_passed = True

    # Run tests
    all_passed &= test_video_platforms()
    all_passed &= test_audio_platforms()
    all_passed &= test_html5_native()
    all_passed &= test_multiple_embeds()
    all_passed &= test_no_embeds()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Sprint 7.17 embed detection working")
        print()
        print("Summary:")
        print("- Video platforms detected: YouTube, Vimeo, BU Media")
        print("- Audio platforms detected: SoundCloud, Spotify")
        print("- HTML5 native elements detected: <video>, <audio>")
        print("- Multiple embeds counted correctly")
        print("- No false positives on text-only articles")
        print()
        print("Next step: Run full pipeline to verify integration:")
        print("  cd ~/buzz-metrics/scraper")
        print("  python3 scrape.py && python3 verify.py && python3 compare.py")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 70)

from groq_verify import fetch_article_text

url = 'https://buzz.bournemouth.ac.uk/2026/01/man-charged-after-human-remains-found/'
text = fetch_article_text(url)

print(f'Length: {len(text)}')
print(f'Has straight double: {chr(34) in text}')
print(f'Has curly left: {chr(8220) in text}')
print(f'Has curly right: {chr(8221) in text}')
print(f'Has single: {chr(39) in text}')
print()
print('First 500 chars:')
print(text[:500])

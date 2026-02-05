import os
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# Fetch article
resp = requests.get('https://buzz.bournemouth.ac.uk/2026/01/mark-mcadam-speaks-cherries-transfers/')
soup = BeautifulSoup(resp.text, 'lxml')
article = soup.find('article')
for tag in article.find_all(['nav', 'footer', 'aside']):
    tag.decompose()
text = article.get_text(separator=' ', strip=True)

# Read prompt from file
with open('groq_verify.py') as f:
    code = f.read()
PROMPT = code.split('PROMPT = """')[1].split('"""')[0]

# Call Groq
response = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {os.environ["GROQ_API_KEY"]}', 'Content-Type': 'application/json'},
    json={'model': 'llama-3.1-8b-instant', 'messages': [{'role': 'user', 'content': PROMPT + text[:8000]}], 'temperature': 0.1, 'max_tokens': 4000},
    timeout=30
)
content = response.json()['choices'][0]['message']['content']

print(f'Length: {len(content)}')
print(f'First 300 chars: {repr(content[:300])}')
print(f'Has backticks: {"```" in content}')

# Try parsing
try:
    parsed = json.loads(content.strip())
    print(f'Parsed OK: {len(parsed)} items')
except Exception as e:
    print(f'Parse failed: {e}')

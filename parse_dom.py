from bs4 import BeautifulSoup
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('comment_launcher/data/failed_dom.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

print("Looking for elements with 'comment'...")
for el in soup.find_all(string=lambda t: t and 'comment' in t.lower()):
    if len(el.strip()) > 100: continue
    parent = el.parent
    print(f"Text: {el.strip()}, Parent Tag: {parent.name}, Parent Role: {parent.get('role', '')}")

print("\nLooking for input tags...")
for el in soup.find_all('input'):
    print(f"Found input: type={el.get('type')}, placeholder={el.get('placeholder')}, aria-label={el.get('aria-label')}")

print("\nLooking for aria-label with 'comment'...")
for el in soup.find_all(attrs={'aria-label': lambda v: v and 'comment' in v.lower()}):
    print(f"Found aria-label comment: Tag: {el.name}, aria-label: {el.get('aria-label')}, classes: {el.get('class')}")

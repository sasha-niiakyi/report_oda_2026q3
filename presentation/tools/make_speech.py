"""Збирає speech.md з реплік (window.NOTES) і слайдів презентації.

Текст виступу живе в index.html — одна репліка на клік. Після правок там
запустіть:  python3 presentation/tools/make_speech.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'presentation' / 'index.html'
OUT = ROOT / 'speech.md'

PROJECTS = {'p0': None, 'p1': 'ПРО.ШІ', 'p3': 'ПРОЯВ', 'p4': 'Відкриті дані', 'p2': 'Програма цифрової трансформації 2027–2029'}

src = SRC.read_text(encoding='utf-8')

# репліки: рядки виду  /* N */ '…',
notes = []
block = src[src.index('window.NOTES = ['):]
block = block[:block.index('];')]
for m in re.finditer(r"/\*\s*(\d+)\s*\*/\s*'((?:\\'|[^'])*)'", block):
    notes.append(m.group(2).replace("\\'", "'"))

# слайди по порядку: id, тема, кількість кроків, заголовок
slides = []
for m in re.finditer(r'<section class="slide[^"]*" id="([^"]+)" data-theme="(p\d)"([^>]*)>(.*?)</section>', src, re.S):
    sid, theme, attrs, body = m.groups()
    builds = int(re.search(r'data-builds="(\d+)"', attrs).group(1)) if 'data-builds' in attrs else 0
    h = re.search(r'<h[12][^>]*>(.*?)</h[12]>', body, re.S)
    title = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<br\s*/?>', ' ', h.group(1)))).strip() if h else sid
    title = re.sub(r'\s+', ' ', title)
    dt = re.search(r'data-title="([^"]+)"', attrs)
    if dt:
        title = dt.group(1)
    slides.append((sid, theme, builds, title, attrs))

steps = [(s, b) for s in slides for b in range(s[2] + 1)]
assert len(steps) == len(notes), f'кроків {len(steps)}, реплік {len(notes)}'

lines = [
    '# Виступ: результати ОКР за квартал',
    '',
    '> Файл зібрано автоматично з презентації (`presentation/index.html`, масив `window.NOTES`).',
    '> Правите текст — правте там і перезапустіть `python3 presentation/tools/make_speech.py`, щоб слайди і текст не розійшлися.',
    '> `[клік N]` — одне натискання. `⟦…⟧` — місця, де ще потрібні ваші дані.',
    '',
]
cur_proj = object()
prev_slide = None
for n, ((sid, theme, builds, title, attrs), b) in enumerate(steps):
    hub = re.search(r'data-hub="(p\d)"', attrs)
    proj = PROJECTS[hub.group(1)] if hub else PROJECTS[theme] or ('Вступ' if n < 5 else 'Фінал')
    if proj != cur_proj:
        lines += ['', '---', '', f'## {proj}', '']
        cur_proj = proj
    if sid != prev_slide:
        lines += [f'### {title}', '']
        prev_slide = sid
    lines += [f'`[клік {n}]`', f'> {notes[n]}', '']

OUT.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
print('speech.md:', len(steps), 'кліків')

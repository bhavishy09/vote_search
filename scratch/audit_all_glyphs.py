import pymupdf
from fontTools.ttLib import TTFont
import io

doc = pymupdf.open('WithPhoto_GANGAPUR CITY NAGAR PARISHAD-Ward No-020-Part No-001.pdf')
f_buf = doc.extract_font(170)[3]
tt = TTFont(io.BytesIO(f_buf))
glyf = tt['glyf']
gset = tt.getGlyphSet()

cmap = None
for sub in tt['cmap'].tables:
    if sub.platformID == 3:
        cmap = sub.cmap
        break

import sys
sys.path.append('.')
from pdf_parser import GLYPH_MAP

# Also collect occurrences of each byte in the PDF stream of pages 3-10
byte_counts = {}
for pno in range(2, min(len(doc), 10)):
    page = doc[pno]
    for x in page.get_xobjects():
        s = doc.xref_stream(x[0]).decode('latin1', errors='ignore')
        for b in s.encode('latin1'):
            byte_counts[b] = byte_counts.get(b, 0) + 1

# Generate an HTML page with each glyph rendered as SVG + sample occurrences in text
html = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<style>',
        'body { font-family: sans-serif; background: #f4f5f7; padding: 20px; }',
        '.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; }',
        '.card { background: white; border-radius: 8px; padding: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }',
        '.code { font-weight: bold; font-size: 13px; color: #1a73e8; }',
        '.char { font-size: 11px; color: #666; margin-bottom: 4px; }',
        '.curr { font-size: 18px; color: #d93025; font-weight: bold; margin: 6px 0; }',
        '.svg-box { width: 80px; height: 80px; margin: 0 auto; background: #fafafa; border: 1px solid #eee; }',
        '</style></head><body>',
        '<h2>Rajasthan ECI Embedded Font (170) Glyph Audit</h2>',
        '<div class="grid">']

with open('all_glyphs.svg') as f:
    svg_content = f.read()

import re
svg_paths = {}
for m in re.finditer(r'<text[^>]*>(0x[0-9a-fA-F]+)[^<]*</text>\s*<g[^>]*><path d="([^"]*)"', svg_content):
    c = int(m.group(1), 16)
    svg_paths[c] = m.group(2)

for code in sorted(cmap.keys()):
    b = code & 0xff
    glyph_name = cmap[code]
    path = svg_paths.get(b, '')
    curr = GLYPH_MAP.get(b, '?')
    cnt = byte_counts.get(b, 0)
    ch_disp = chr(b) if 32 <= b <= 126 else f'\\x{b:02x}'
    
    html.append(f'<div class="card">')
    html.append(f'<div class="code">0x{b:02x} ({ch_disp})</div>')
    html.append(f'<div class="char">count: {cnt}</div>')
    html.append(f'<div class="svg-box"><svg width="80" height="80" viewBox="0 -1400 1600 1600"><g transform="scale(0.8, -0.8) translate(100, -1100)"><path d="{path}" fill="#222"/></g></svg></div>')
    html.append(f'<div class="curr">{curr}</div>')
    html.append(f'</div>')

html.append('</div></body></html>')

with open('scratch/glyph_audit.html', 'w') as f:
    f.write('\n'.join(html))
print('Saved scratch/glyph_audit.html')

import pymupdf
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import io

doc = pymupdf.open('WithPhoto_GANGAPUR CITY NAGAR PARISHAD-Ward No-020-Part No-001.pdf')
f_buf = doc.extract_font(170)[3]
tt = TTFont(io.BytesIO(f_buf))
glyf = tt['glyf']

# Get cmap
cmap = None
for sub in tt['cmap'].tables:
    if sub.platformID == 3:
        cmap = sub.cmap
        break

import sys
sys.path.append('.')
from pdf_parser import GLYPH_MAP

print(f"{'Code':<6} {'Chr':<4} {'Glyph':<10} {'Box':<30} {'Contours':<10} {'Current GLYPH_MAP'}")
print("-" * 80)

gset = tt.getGlyphSet()

for code in sorted(cmap.keys()):
    byte_val = code & 0xff
    glyph_name = cmap[code]
    g = gset[glyph_name]
    bp = BoundsPen(gset)
    g.draw(bp)
    bounds = bp.bounds if bp.bounds else (0, 0, 0, 0)
    box_str = f"({bounds[0]:.0f},{bounds[1]:.0f},{bounds[2]:.0f},{bounds[3]:.0f})"
    num_contours = glyf[glyph_name].numberOfContours
    
    char_disp = chr(byte_val) if 32 <= byte_val <= 126 else "?"
    curr = GLYPH_MAP.get(byte_val, "MISSING")
    
    print(f"0x{byte_val:02x}   {char_disp:<4} {glyph_name:<10} {box_str:<30} {num_contours:<10} {curr}")

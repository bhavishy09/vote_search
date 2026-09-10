import pymupdf
import re
import os
import sys

sys.path.append('.')
from transliteration import transliterate_hindi_to_english, normalize_search_query

# Character decoding map for Rajasthan State Election Commission / ECI embedded font
GLYPH_MAP = {
    0x20: "र",   0x21: "ा",   0x22: "ज्",  0x23: "य",   0x24: "ि",   0x25: "न",
    0x26: "व",   0x27: "र्",  0x28: "च",   0x29: "आ",   0x2a: "ो",   0x2b: "ग",
    0x2c: "ज",   0x2d: "स्",  0x2e: "थ",   0x2f: "प",   0x30: "ल",   0x31: "क",
    0x32: "ु",   0x33: "म",   0x34: "ी",   0x35: "ि",   0x36: "ष",   0x37: "द",
    0x38: "ं",   0x39: "स",   0x3a: "ट",   0x3b: "क्ष", 0x3c: "ण",   0x3d: "प्र",
    0x3e: "अ",   0x3f: "ह",   0x40: "त",   0x41: "ि",   0x42: "श",   0x43: "ी",
    0x44: "ड",   0x45: "ें",  0x46: "द्र", 0x47: "ख",   0x48: "ए",   0x49: "ओं",
    0x4a: "म्",  0x4b: "भ",   0x4c: "क्र", 0x4d: "रू",  0x4e: "स्त्र", 0x4f: "द्य",
    0x50: "ल्",  0x51: "ध",   0x52: "ब",   0x53: "ृ",   0x54: "िं",  0x55: "े",
    0x56: "त्र", 0x57: "ई",   0x58: "घ",   0x59: "ओ",   0x5a: "हू",  0x5b: "श्र",
    0x5c: "ै",   0x5d: "छ",   0x5e: "ड़",  0x5f: "ट्र", 0x60: "त्",  0x61: "ख्",
    0x62: "प्",  0x63: "फ",   0x64: "न्",  0x65: "त्त", 0x66: "औ",   0x67: "ू",
    0x68: "ाँ",  0x69: "कृ",  0x6a: "ठ",   0x6b: "ीं",  0x6c: "श्",  0x6d: "ष्",
    0x6e: "ट्",  0x6f: "ँ",   0x70: "।",   0x71: "ष्ठ", 0x72: "ौ",   0x73: "०",
    0x74: "ेर्", 0x75: "क्ष्", 0x76: "म्र", 0x77: "ग्र", 0x78: "उ",   0x79: "ज्ज",
    0x7a: "इ",   0x7b: "ि",   0x7c: "द्ध", 0x7d: "श्व", 0x7e: "न्न", 0x7f: "द्व",
    0x80: "प्त", 0x81: "ग्र", 0x82: "ज्ञ", 0x83: "ग्",  0x84: "ब्",  0x85: "ब्र",
    0x86: "हृ",  0x87: "िं",  0x88: "रु",  0x89: "स्त्री", 0x8a: "ीर्", 0x8b: "़",
    0x8c: "्",   0x8e: "क्क", 0x8f: "ऊ",   0x90: "धं",  0x91: "ण्",  0x92: "झ",
    0x93: "य्",  0x94: "फ़"
}

VOWEL_MATRAS = set(['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', 'ं', 'ँ', 'ः', '़'])

def apply_reph_to_chars(chars):
    idx = len(chars) - 1
    while idx >= 0 and chars[idx] in VOWEL_MATRAS:
        idx -= 1
    if idx >= 0:
        chars.insert(idx, 'र्')
    else:
        chars.insert(0, 'र्')

def decode_devanagari_token(raw_text: str) -> str:
    res = []
    i = 0
    while i < len(raw_text):
        c = ord(raw_text[i])
        if c in (0x24, 0x35, 0x41, 0x7b):
            i += 1
            if i < len(raw_text):
                next_c = ord(raw_text[i])
                base = GLYPH_MAP.get(next_c, raw_text[i])
                res.append(base)
                res.append("ि")
            i += 1
            continue
        elif c in (0x54, 0x87):
            i += 1
            if i < len(raw_text):
                next_c = ord(raw_text[i])
                base = GLYPH_MAP.get(next_c, raw_text[i])
                res.append(base)
                res.append("िं")
            i += 1
            continue
        elif c == 0x27:
            apply_reph_to_chars(res)
            i += 1
            continue
        elif c == 0x74:
            apply_reph_to_chars(res)
            res.append("े")
            i += 1
            continue
        elif c == 0x8a:
            apply_reph_to_chars(res)
            res.append("ी")
            i += 1
            continue
        
        char_mapped = GLYPH_MAP.get(c, raw_text[i])
        res.append(char_mapped)
        i += 1

    return "".join(res)

def unescape_pdf_string(s: str) -> str:
    """Unescapes PDF string backslash sequences like \\(, \\), \\\\."""
    res = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i+1]
            if nxt in ('(', ')', '\\'):
                res.append(nxt)
            elif nxt == 'n':
                res.append('\n')
            elif nxt == 'r':
                res.append('\r')
            elif nxt == 't':
                res.append('\t')
            else:
                res.append(nxt)
            i += 2
        else:
            res.append(s[i])
            i += 1
    return "".join(res)

def parse_voter_card(voter_bt: str, serial_num: int) -> dict:
    # 1. EPIC: matches 10-char alphanumeric or slashes (e.g. RJ/11/085/399175)
    epic_m = re.search(r"\(([A-Z0-9/\-]{8,25})\)\s*Tj", voter_bt)
    epic = epic_m.group(1) if epic_m else ""

    # 2. Age: ( 56) Tj or (: 56) Tj
    age_m = re.search(r"\(\s*([0-9]{1,3})\s*\)\s*Tj", voter_bt)
    age = int(age_m.group(1)) if age_m else 0

    # 3. Gender: /2M6 (पुरुष), N4 (स्त्री)
    gender = ""
    if "/2M6" in voter_bt:
        gender = "पुरुष"
    elif "N4" in voter_bt:
        gender = "स्त्री"

    # 4. House number: /a 8.95 Tf (00) Tj or (10/1) or (74)
    hn_matches = re.findall(r"/a\s+[0-9\.]+\s+Tf\s*\(([0-9\-/]+|[A-Za-z0-9\-]+)\)\s*Tj", voter_bt)
    house_no = ""
    for hn in hn_matches:
        if hn != epic and not (hn.isdigit() and int(hn) == age):
            house_no = hn
            break
    if not house_no and hn_matches:
        for hn in hn_matches:
            if hn != epic:
                house_no = hn
                break

    # 5. Relation type:
    relation_type = "Father"
    if "/$@" in voter_bt:
        relation_type = "Husband"
    elif "3!@!" in voter_bt:
        relation_type = "Mother"

    # 6. Deletion status
    is_deleted = False
    if "DELETED" in voter_bt or "(S)" in voter_bt or " S " in voter_bt:
        is_deleted = True

    # 7. Extract lines of Hindi text
    tokens = re.findall(
        r"(?:/([9aspe])\s+[0-9\.]+\s+Tf|([0-9\.\-]+)\s+([0-9\.\-]+)\s+Td|\(([^\)]*)\)\s*Tj)",
        voter_bt,
    )

    cur_font = "a"
    lines = [[]]
    for item in tokens:
        font, dx, dy, text = item
        if font:
            cur_font = font
        elif dy:
            if abs(float(dy)) > 5:
                if lines[-1]:
                    lines.append([])
        elif text is not None:
            unescaped = unescape_pdf_string(text)
            if cur_font == "9":
                dec = decode_devanagari_token(unescaped).strip()
                if dec:
                    lines[-1].append(dec)
            elif cur_font == "a" and unescaped == " ":
                lines[-1].append(" ")

    text_lines = ["".join(l).strip() for l in lines if "".join(l).strip()]
    meaningful = [
        l for l in text_lines
        if len(l) > 1 and not any(k in l for k in ["पुरूष", "पुरुष", "स्त्री", "लिंग", "नाम", "मकान", "संखया", "संख्या"])
    ]

    voter_name_hindi = meaningful[-2] if len(meaningful) >= 2 else (meaningful[-1] if meaningful else "")
    relation_name_hindi = meaningful[-1] if len(meaningful) >= 2 else ""

    # Transliterate to English
    name_english = transliterate_hindi_to_english(voter_name_hindi)
    relation_name_english = transliterate_hindi_to_english(relation_name_hindi)

    search_key = f"{normalize_search_query(name_english)} {normalize_search_query(relation_name_english)} {epic.lower()}"

    return {
        "kram_sankhya": serial_num,
        "epic": epic,
        "name_hindi": voter_name_hindi,
        "name_english": name_english,
        "relation_name_hindi": relation_name_hindi,
        "relation_name_english": relation_name_english,
        "relation_type": relation_type,
        "age": age,
        "gender": gender,
        "house_number": house_no,
        "is_deleted": is_deleted,
        "search_key": search_key,
    }

def parse_page_voters(doc, pno, bhag_sankhya):
    page = doc[pno]
    xobjs = page.get_xobjects()
    if xobjs:
        stream = doc.xref_stream(xobjs[0][0]).decode("latin1", errors="ignore")
    else:
        stream = page.read_contents().decode("latin1", errors="ignore")

    bts = re.findall(r"BT\s*(.*?)\s*ET", stream, re.DOTALL)
    
    # 1. Collect serial blocks: font /p, /s, /e with (S 104) or ( 104 )
    serial_blocks = []
    # 2. Collect voter blocks: has EPIC
    voter_blocks = []

    for bt in bts:
        tm_m = re.search(r"([0-9\.\-]+)\s+([0-9\.\-]+)\s+Tm", bt)
        if not tm_m:
            continue
        x = float(tm_m.group(1))
        y = float(tm_m.group(2))

        # Check if voter card block (contains EPIC)
        em = re.search(r"\(([A-Z0-9/\-]{8,25})\)\s*Tj", bt)
        if em:
            voter_blocks.append((x, y, bt))
            continue

        # Check if serial number block
        sm = re.search(r"/(?:[pse])\s+[0-9\.]+\s+Tf\s*\(\s*(?:S\s*)?([0-9]+)\s*\)\s*Tj", bt)
        if not sm:
            sm = re.search(r"\(\s*(?:S\s*)?([0-9]{1,4})\s*\)\s*Tj", bt)
        if sm:
            s_num = int(sm.group(1))
            serial_blocks.append((x, y, s_num, bt))

    # Match each voter block to its corresponding serial block
    # Spatial rule: voter_x ≈ serial_x + 13.75, voter_y ≈ serial_y - 53.05
    page_voters = []
    for vx, vy, vbt in voter_blocks:
        best_dist = 999999
        matched_serial = None
        has_s_mark = False

        for sx, sy, snum, sbt in serial_blocks:
            expected_vx = sx + 13.75
            expected_vy = sy - 53.05
            dist = ((vx - expected_vx)**2 + (vy - expected_vy)**2)**0.5
            if dist < best_dist and dist < 35.0: # generous threshold
                best_dist = dist
                matched_serial = snum
                if "(S)" in sbt or " S " in sbt or "S" in sbt:
                    has_s_mark = True

        if matched_serial is None:
            # Fallback: check if serial number is directly in voter BT
            sm = re.search(r"/(?:[pse])\s+[0-9\.]+\s+Tf\s*\(\s*(?:S\s*)?([0-9]+)\s*\)\s*Tj", vbt)
            if sm:
                matched_serial = int(sm.group(1))

        if matched_serial is not None:
            card = parse_voter_card(vbt, matched_serial)
            if has_s_mark:
                card["is_deleted"] = True
            card["bhag_sankhya"] = bhag_sankhya
            page_voters.append(card)

    return page_voters

# Test on Part 2 page 7 (index 6, should have 104 / Radheshyam)
doc2 = pymupdf.open('WithPhoto_GANGAPUR CITY NAGAR PARISHAD-Ward No-020-Part No-002.pdf')
p7_voters = parse_page_voters(doc2, 6, "2")
print(f'Page 7 voters extracted: {len(p7_voters)}')
for v in p7_voters[:5]:
    print(f"Kram {v['kram_sankhya']:>4}: {v['name_hindi']} ({v['name_english']}), Father: {v['relation_name_hindi']} ({v['relation_name_english']}), EPIC: {v['epic']}, Age: {v['age']}, Deleted: {v['is_deleted']}")

v104 = next((v for v in p7_voters if v['kram_sankhya'] == 104), None)
print('--- Voter 104 ---')
print(v104)

# Test on Part 2 page 4 (index 3, should have 44 / Ajay Kumar)
p4_voters = parse_page_voters(doc2, 3, "2")
v44 = next((v for v in p4_voters if v['kram_sankhya'] == 44), None)
print('--- Voter 44 ---')
print(v44)

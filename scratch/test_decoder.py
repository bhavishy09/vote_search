import pymupdf
import re
import os

# Complete and accurate GLYPH_MAP based on vector visual audit
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
    """Inserts 'र्' before the preceding base consonant cluster in chars list."""
    idx = len(chars) - 1
    while idx >= 0 and chars[idx] in VOWEL_MATRAS:
        idx -= 1
    # If base consonant is preceded by virama + half consonant (e.g. 'न्' or 'श्'),
    # reph can sit on the base or cluster
    if idx >= 0:
        chars.insert(idx, 'र्')
    else:
        chars.insert(0, 'र्')

def decode_devanagari_token(raw_text: str) -> str:
    """Decodes font 9 byte string to clean Unicode Devanagari."""
    res = []
    i = 0
    while i < len(raw_text):
        c = ord(raw_text[i])
        
        # 1. Chhoti ee matra (prefixed in legacy font: 0x24, 0x35, 0x41, 0x7b)
        if c in (0x24, 0x35, 0x41, 0x7b):
            i += 1
            if i < len(raw_text):
                next_c = ord(raw_text[i])
                base = GLYPH_MAP.get(next_c, raw_text[i])
                res.append(base)
                res.append("ि")
            i += 1
            continue
        # Chhoti ee with anusvara (0x54, 0x87)
        elif c in (0x54, 0x87):
            i += 1
            if i < len(raw_text):
                next_c = ord(raw_text[i])
                base = GLYPH_MAP.get(next_c, raw_text[i])
                res.append(base)
                res.append("िं")
            i += 1
            continue
        # 2. Reph 'र्' (0x27) typed after consonant / vowel matra
        elif c == 0x27:
            apply_reph_to_chars(res)
            i += 1
            continue
        # 3. Combined e-matra with reph (0x74: 'ेर्')
        elif c == 0x74:
            apply_reph_to_chars(res)
            res.append("े")
            i += 1
            continue
        # 4. Combined ee-matra with reph (0x8a: 'ीर्')
        elif c == 0x8a:
            apply_reph_to_chars(res)
            res.append("ी")
            i += 1
            continue
        
        char_mapped = GLYPH_MAP.get(c, raw_text[i])
        res.append(char_mapped)
        i += 1

    return "".join(res)

print('Testing decode_devanagari_token:')
print('B3!\' ->', decode_devanagari_token("B3!'"))
print('&6!\' ->', decode_devanagari_token("&6!'"))
print('&3!\' ->', decode_devanagari_token("&3!'"))
print('!QUl#!3 ->', decode_devanagari_token(" !QUl#!3"))
print('0P0g !3 ->', decode_devanagari_token("0P0g !3"))
print('&kF ->', decode_devanagari_token(" &kF"))
print('321 U B ->', decode_devanagari_token("321UB"))
print('\"#*$@ ->', decode_devanagari_token("\"#*$@"))

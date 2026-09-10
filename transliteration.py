"""
Hindi-to-Roman transliteration and phonetic normalization utilities.
Converts Devanagari names to Roman English script with Indian English phonetic conventions.
"""

import re
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

KNOWN_NAME_CORRECTIONS = {
    "soni": "Soni",
    "sharma": "Sharma",
    "varma": "Varma",
    "verma": "Verma",
    "gupta": "Gupta",
    "singh": "Singh",
    "kumar": "Kumar",
    "kumari": "Kumari",
    "devi": "Devi",
    "prasad": "Prasad",
    "ram": "Ram",
    "lal": "Lal",
    "chand": "Chand",
    "chandra": "Chandra",
    "jain": "Jain",
    "agarwal": "Agarwal",
    "agrawal": "Agrawal",
    "yadav": "Yadav",
    "mishra": "Mishra",
    "tiwari": "Tiwari",
    "pandey": "Pandey",
    "saini": "Saini",
    "meena": "Meena",
    "gurjar": "Gurjar",
    "mohan": "Mohan",
    "madan": "Madan",
    "pintu": "Pintu",
    "hema": "Hema",
    "mona": "Mona",
    "jyoti": "Jyoti",
    "ravindra": "Ravindra",
    "rajrani": "Rajrani",
    "rajkumari": "Rajkumari",
    "prabhu": "Prabhu",
    "dayal": "Dayal",
    "jagdish": "Jagdish",
    "ashok": "Ashok",
    "suresh": "Suresh",
    "ramesh": "Ramesh",
    "dinesh": "Dinesh",
    "mukesh": "Mukesh",
    "anil": "Anil",
    "sunil": "Sunil",
    "radheshyam": "Radheshyam",
    "radheyshyam": "Radheshyam",
    "radhey": "Radhey",
    "shyam": "Shyam",
    "lalluram": "Lalluram",
    "laluram": "Lalluram",
    "puran": "Puran",
    "jangid": "Jangid",
    "jatin": "Jatin",
    "ajay": "Ajay",
    "omprakash": "Omprakash",
    "omaprakash": "Omprakash",
    "kavita": "Kavita",
    "shubham": "Shubham",
    "varsha": "Varsha",
    "vimaladevi": "Vimaladevi",
    "ramashankar": "Ramashankar",
    "govind": "Govind",
    "parashar": "Parashar",
    "satish": "Satish",
    "manju": "Manju",
    "anita": "Anita",
    "poonam": "Poonam",
    "deepesh": "Deepesh",
    "dipsh": "Deepesh",
}


def transliterate_hindi_to_english(text: str) -> str:
    """
    Transliterate Devanagari Hindi text to natural Indian English Roman script.
    """
    if not text or not text.strip():
        return ""

    cleaned = re.sub(r"\s+", " ", text.strip())

    try:
        it = transliterate(cleaned, sanscript.DEVANAGARI, sanscript.ITRANS)
    except Exception:
        return cleaned

    words = it.split()
    processed = []

    for w in words:
        # Strip trailing inherent short 'a' (schwa deletion in Hindi):
        if w.endswith("a") and not w.endswith(("aa", "ya")):
            w = w[:-1]

        # Convert ITRANS long/special markers
        w = w.replace("A", "a")
        w = w.replace("I", "i")
        w = w.replace("U", "u")
        w = w.replace("ii", "i")
        w = w.replace("ee", "i")
        w = w.replace("uu", "u")
        w = w.replace("oo", "u")
        w = w.replace("M", "n")
        w = w.replace("~N", "n")
        w = w.replace("shh", "sh")
        w = w.replace("Sh", "sh")
        w = w.replace("chh", "chh")
        w = w.replace("jn", "gy")
        w = re.sub(r"[\.\^~`\|\*]", "", w)

        # Common Hindi patterns:
        if w.lower().startswith(("jaga", "raja", "nava", "kama", "omap")):
            w = re.sub(r"^([a-z]{2,3})a([b-df-hj-np-tv-z])([iueoa])", r"\1\2\3", w)

        low = w.lower()
        if low in KNOWN_NAME_CORRECTIONS:
            w = KNOWN_NAME_CORRECTIONS[low]
        else:
            w = w.capitalize()

        processed.append(w)

    return " ".join(processed)


def normalize_search_query(query: str) -> str:
    """
    Normalize English query for fuzzy/phonetic indexing and comparison.
    """
    if not query:
        return ""

    q = query.lower().strip()
    q = re.sub(r"[^\w\s]", " ", q)
    q = re.sub(r"\s+", " ", q)

    # Interchangeable letters & common variations in Indian transliteration
    q = q.replace("radheyshayam", "radheshyam")
    q = q.replace("radheyshyam", "radheshyam")
    q = q.replace("laluram", "lalluram")
    q = q.replace("omaprakash", "omprakash")
    q = q.replace("w", "v")
    q = q.replace("ee", "i")
    q = q.replace("ea", "i")
    q = q.replace("oo", "u")
    q = q.replace("ph", "f")
    # Simplify doubled consonants: e.g. 'sharmaa' -> 'sharma', 'sonii' -> 'soni'
    q = re.sub(r"([a-z])\1+", r"\1", q)

    return q.strip()

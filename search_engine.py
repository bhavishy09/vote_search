"""
High-performance Fuzzy & Phonetic Search Engine for Voter Records.
Uses RapidFuzz (C++ accelerated Levenshtein / Token Sort / Partial Ratio)
combined with phonetic normalizations to match names in English, Hindi,
relation names, Kramank (serial numbers), and EPIC voter IDs. Returns sub-50ms results.
"""

import time
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz

from database import get_all_voters
from transliteration import normalize_search_query


def compute_word_match_score(query: str, candidate: str) -> float:
    """
    Computes bipartite word-level fuzzy match score.
    Every word in the query must find a close corresponding word in the candidate.
    """
    q_words = query.lower().split()
    c_words = candidate.lower().split()
    if not q_words or not c_words:
        return 0.0

    word_scores = []
    for qw in q_words:
        best_w = max((fuzz.ratio(qw, cw) for cw in c_words), default=0.0)
        word_scores.append(best_w)

    avg_score = sum(word_scores) / len(word_scores)
    return round(avg_score, 1)


class VoterSearchEngine:
    def __init__(self):
        self._voters_cache: List[Dict[str, Any]] = []
        self._last_loaded = 0
        self.reload_cache()

    def reload_cache(self):
        """Loads all voter records into memory for ultra-fast matching."""
        self._voters_cache = get_all_voters()
        for v in self._voters_cache:
            v["_norm_name_en"] = normalize_search_query(v.get("name_english", ""))
            v["_norm_name_hi"] = v.get("name_hindi", "").strip()
            v["_norm_rel_en"] = normalize_search_query(v.get("relation_name_english", ""))
            v["_norm_rel_hi"] = v.get("relation_name_hindi", "").strip()
            v["_epic_clean"] = v.get("epic", "").upper().strip()
        self._last_loaded = time.time()

    def search(
        self,
        name_query: str,
        relation_query: Optional[str] = None,
        bhag_sankhya: Optional[str] = None,
        limit: int = 100,
        confidence_threshold: float = 65.0,
    ) -> Dict[str, Any]:
        """
        Executes fuzzy and phonetic search against voter records.
        """
        t0 = time.time()

        if not self._voters_cache:
            self.reload_cache()

        name_q = name_query.strip() if name_query else ""
        rel_q = relation_query.strip() if relation_query else ""
        norm_name_q = normalize_search_query(name_q)
        norm_rel_q = normalize_search_query(rel_q)

        # Empty search
        if not name_q and not rel_q:
            return {
                "query_name": name_q,
                "query_relation": rel_q,
                "total_results": 0,
                "is_fallback": False,
                "message": "Please enter a voter name or serial number to search.",
                "elapsed_ms": 0.0,
                "results": [],
            }

        # Filter by Part Number if specified
        candidates = self._voters_cache
        if bhag_sankhya and bhag_sankhya != "all":
            candidates = [v for v in candidates if str(v.get("bhag_sankhya")) == str(bhag_sankhya)]

        clean_upper_q = name_q.upper().replace(" ", "")

        # 1. Check if query is a Serial Number (Kram Sankhya)
        if clean_upper_q.isdigit() and int(clean_upper_q) <= 5000 and not rel_q:
            kram_val = int(clean_upper_q)
            kram_matches = [v for v in candidates if v.get("kram_sankhya") == kram_val]
            if kram_matches:
                results = []
                for v in kram_matches:
                    res = dict(v)
                    res["match_score"] = 100.0
                    res["match_label"] = f"Exact Kramank {kram_val} Match"
                    results.append(res)
                elapsed_ms = (time.time() - t0) * 1000
                return {
                    "query_name": name_q,
                    "query_relation": rel_q,
                    "total_results": len(results),
                    "is_fallback": False,
                    "message": f"Found {len(results)} exact Kramank {kram_val} match(es)",
                    "elapsed_ms": round(elapsed_ms, 2),
                    "results": results,
                }

        # 2. Check if query is an EPIC ID
        epic_matches = [
            v for v in candidates
            if clean_upper_q in v["_epic_clean"] or v["_epic_clean"].endswith(clean_upper_q)
        ]
        if epic_matches and len(clean_upper_q) >= 4:
            results = []
            for v in epic_matches:
                res = dict(v)
                res["match_score"] = 100.0
                res["match_label"] = "Exact EPIC Match"
                results.append(res)
            elapsed_ms = (time.time() - t0) * 1000
            return {
                "query_name": name_q,
                "query_relation": rel_q,
                "total_results": len(results),
                "is_fallback": False,
                "message": f"Found {len(results)} exact EPIC match(es)",
                "elapsed_ms": round(elapsed_ms, 2),
                "results": results,
            }

        # 3. Fuzzy & Phonetic Name Matching
        scored_records = []
        for v in candidates:
            # 1. Name match score: word-level bipartite matching
            score_en = compute_word_match_score(norm_name_q, v["_norm_name_en"])

            # Match against Hindi directly if query contains Devanagari
            score_hi = 0.0
            if any("\u0900" <= char <= "\u097f" for char in name_q):
                score_hi = compute_word_match_score(name_q, v["_norm_name_hi"])

            name_score = max(score_en, score_hi)

            # 2. Relation name match score (if relation query provided)
            rel_score = 0.0
            if norm_rel_q:
                rel_score_en = compute_word_match_score(norm_rel_q, v["_norm_rel_en"])
                rel_score_hi = 0.0
                if any("\u0900" <= char <= "\u097f" for char in rel_q):
                    rel_score_hi = compute_word_match_score(rel_q, v["_norm_rel_hi"])

                rel_score = max(rel_score_en, rel_score_hi)

                # Combined score: name has 65% weight, relation has 35% weight
                final_score = (name_score * 0.65) + (rel_score * 0.35)
            else:
                final_score = name_score

            if final_score >= 35.0:
                record = dict(v)
                record["match_score"] = round(final_score, 1)
                record["name_score"] = round(name_score, 1)
                record["relation_score"] = round(rel_score, 1)
                scored_records.append(record)

        # Sort by match score descending, then by serial number
        scored_records.sort(key=lambda x: (x["match_score"], -x["kram_sankhya"]), reverse=True)

        elapsed_ms = (time.time() - t0) * 1000

        # Check if confident matches exist
        confident_matches = [r for r in scored_records if r["match_score"] >= confidence_threshold]

        if confident_matches:
            final_results = confident_matches[:limit]
            return {
                "query_name": name_q,
                "query_relation": rel_q,
                "total_results": len(final_results),
                "is_fallback": False,
                "message": f"Found {len(final_results)} matching voter(s)",
                "elapsed_ms": round(elapsed_ms, 2),
                "results": final_results,
            }
        else:
            top_fallback = scored_records[:5]
            return {
                "query_name": name_q,
                "query_relation": rel_q,
                "total_results": len(top_fallback),
                "is_fallback": True,
                "message": "No exact match — showing closest results",
                "elapsed_ms": round(elapsed_ms, 2),
                "results": top_fallback,
            }


# Singleton search engine instance
search_engine = VoterSearchEngine()

#!/usr/bin/env python3
"""
CLI Ingestion Script for Voter List PDFs.
Parses PDFs, transliterates names, and stores structured voter records in SQLite database.
Run once per PDF:
    python ingest.py <pdf_path>
    python ingest.py --all
"""

import sys
import os
import glob
import time
from pdf_parser import parse_voter_pdf
from database import save_voters_batch, get_db_stats


def ingest_file(pdf_path: str) -> int:
    """Ingests a single PDF into voters.db."""
    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found: {pdf_path}")
        return 0

    print(f"\n[INGEST] Processing: {os.path.basename(pdf_path)} ...")
    t0 = time.time()
    try:
        parsed = parse_voter_pdf(pdf_path)
        file_size = os.path.getsize(pdf_path)
        saved_count = save_voters_batch(
            filename=parsed["filename"],
            bhag_sankhya=parsed["bhag_sankhya"],
            voters=parsed["voters"],
            file_size=file_size,
        )
        elapsed = time.time() - t0
        print(f"[SUCCESS] Saved {saved_count} voters (Bhag Sankhya: {parsed['bhag_sankhya']}) in {elapsed:.2f}s")
        return saved_count
    except Exception as e:
        print(f"[ERROR] Failed to ingest {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage:")
        print("  python ingest.py <path_to_pdf>")
        print("  python ingest.py --all   (ingests all PDFs in current directory)")
        return

    if sys.argv[1] == "--all":
        pdf_files = sorted(glob.glob("*.pdf"))
        if not pdf_files:
            print("[INFO] No PDF files found in current directory.")
            return

        print(f"Found {len(pdf_files)} PDF files to ingest:")
        total = 0
        for f in pdf_files:
            total += ingest_file(f)

        print("\n" + "=" * 50)
        stats = get_db_stats()
        print(f"Total voters in database: {stats['total_voters']}")
        print(f"Indexed Parts (Bhag Sankhya): {', '.join(stats['parts'])}")
        print("=" * 50)
    else:
        pdf_path = sys.argv[1]
        ingest_file(pdf_path)
        stats = get_db_stats()
        print(f"Total voters in database: {stats['total_voters']}")


if __name__ == "__main__":
    main()

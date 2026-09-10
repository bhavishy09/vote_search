#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================="
echo "   🇮🇳 Voter List Search Web Application"
echo "   Instant Bhag & Kram Sankhya Fuzzy Finder"
echo "========================================================="

# Ingest PDFs if database not populated
if [ ! -f "voters.db" ]; then
    echo "[INFO] Database not found. Ingesting existing voter PDFs..."
    python3 ingest.py --all
else
    # Check if voters table has records
    COUNT=$(python3 -c "import sqlite3; conn=sqlite3.connect('voters.db'); print(conn.execute('SELECT count(*) FROM voters').fetchone()[0])" 2>/dev/null || echo "0")
    if [ "$COUNT" -eq "0" ]; then
        echo "[INFO] Database is empty. Ingesting PDFs..."
        python3 ingest.py --all
    else
        echo "[INFO] Database active with $COUNT voters."
    fi
fi

echo ""
echo "🚀 Starting server at: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo ""

exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

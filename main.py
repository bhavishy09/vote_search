"""
FastAPI Application for Voter List Search.
Provides search API, file upload/ingestion API, stats, and serves the Web UI.
"""

import os
import shutil
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db_stats, save_voters_batch
from pdf_parser import parse_voter_pdf
from search_engine import search_engine

# Initialize database
init_db()

app = FastAPI(title="Voter List Search API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=FileResponse)
async def serve_index():
    """Serves the single page frontend."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>Voter List Search</h1><p>Frontend loading...</p>")
    return FileResponse(index_path)


@app.get("/api/search")
async def api_search(
    name: str = Query(..., description="Voter Name (English or Hindi)"),
    relation: Optional[str] = Query(None, description="Father's / Husband's Name (Optional)"),
    bhag: Optional[str] = Query(None, description="Part Number / Bhag Sankhya filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
):
    """
    Sub-second fuzzy and phonetic search across voter list.
    """
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Voter name query is required")

    result = search_engine.search(
        name_query=name,
        relation_query=relation,
        bhag_sankhya=bhag,
        limit=limit,
    )
    return JSONResponse(result)


@app.get("/api/stats")
async def api_stats():
    """Returns database statistics (voter counts, parts, files)."""
    stats = get_db_stats()
    return JSONResponse(stats)


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """
    Uploads and ingests a new voter list PDF into the database.
    Re-indexes the cache immediately so new voters are searchable.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(save_path)
        t0 = time.time()

        # Parse voter PDF
        parsed = parse_voter_pdf(save_path)
        saved_count = save_voters_batch(
            filename=parsed["filename"],
            bhag_sankhya=parsed["bhag_sankhya"],
            voters=parsed["voters"],
            file_size=file_size,
        )

        # Refresh search cache
        search_engine.reload_cache()
        elapsed = time.time() - t0

        return JSONResponse(
            {
                "status": "success",
                "filename": parsed["filename"],
                "bhag_sankhya": parsed["bhag_sankhya"],
                "total_voters": saved_count,
                "elapsed_seconds": round(elapsed, 2),
                "message": f"Successfully ingested {saved_count} voters from Bhag (Part) {parsed['bhag_sankhya']}",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

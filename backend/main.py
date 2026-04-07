import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.services.discogs import DiscogsError, DiscogsService

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")

DISCOGS_KEY    = os.getenv("DISCOGS_CONSUMER_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_CONSUMER_SECRET")

app = FastAPI()
discogs_service = DiscogsService(
    consumer_key=DISCOGS_KEY,
    consumer_secret=DISCOGS_SECRET,
)

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")

# This endpoint fetches release details from the Discogs API based on the provided release ID.
@app.get("/api/record/{release_id}")
async def get_record(release_id: int):
    try:
        data = await discogs_service.get_release(release_id)
    except DiscogsError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    # Return only the fields the frontend needs
    return {
        "id":        data.get("id"),
        "title":     data.get("title"),
        "year":      data.get("year"),
        "genres":    data.get("genres", []),
        "styles":    data.get("styles", []),
        "artists":   [a.get("name") for a in data.get("artists", [])],
        "tracklist": [
            {"position": t.get("position"), "title": t.get("title")}
            for t in data.get("tracklist", [])
            if t.get("type_") != "heading"
        ],
        "cover":     data.get("images", [{}])[0].get("uri", ""),
        "discogs_url": data.get("uri", ""),
    }

@app.get("/records/search")
async def search_records(query: str | None = None):
    query = query.strip() if query else ""

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Provide a search query to search Discogs.",
        )

    try:
        return await discogs_service.search_releases(query=query)
    except DiscogsError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

DISCOGS_KEY    = os.getenv("DISCOGS_CONSUMER_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_CONSUMER_SECRET")

# Discogs requires a descriptive User-Agent or they'll reject the request
HEADERS = {
    "Authorization": f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}",
    "User-Agent": "VinylRecordTracker/1.0",
}

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/record/{release_id}")
async def get_record(release_id: int):
    url = f"https://api.discogs.com/releases/{release_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Release not found on Discogs")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Discogs API error")

    data = response.json()

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

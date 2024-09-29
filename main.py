# main.py
import os
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routers import songRouter, playlistRouter, processSongRouter

app = FastAPI()

# Include the routers with proper prefixes and tags
app.include_router(songRouter.router, prefix="/songs", tags=["Songs"])
app.include_router(playlistRouter.router, prefix="/playlists", tags=["Playlists"])
app.include_router(processSongRouter.router, tags=["Process Song"])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to match your Next.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys from environment variables

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

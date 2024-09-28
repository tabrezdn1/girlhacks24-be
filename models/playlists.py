# models/playlist.py
from pydantic import BaseModel
from typing import List, Optional

class PlaylistBase(BaseModel):
    name: str

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None

class Playlist(PlaylistBase):
    id: str  # Changed to string
    song_ids: List[str] = []  # List of song IDs as strings

    class Config:
        from_attributes = True

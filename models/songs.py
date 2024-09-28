# models/song.py
from pydantic import BaseModel
from typing import Optional

class SongBase(BaseModel):
    name: Optional[str] = None
    artists: Optional[str] = None
    duration: Optional[str] = None
    image: Optional[str] = None
    language: Optional[str] = None
    release_year: Optional[int] = None
    play_count: Optional[int] = None
    song_url: Optional[str] = None
    genre: Optional[str] = None


class SongCreate(SongBase):
    pass

class SongUpdate(BaseModel):
    name: Optional[str] = None
    artists: Optional[str] = None
    duration: Optional[str] = None
    image: Optional[str] = None
    language:Optional[str] = None
    release_year:Optional[int] = None
    play_count:Optional[int] = None
    song_url: Optional[str] = None

class Song(SongBase):
    id: str  # Changed to string

    class Config:
        from_attributes = True


class SongRequest(BaseModel):
    input: str
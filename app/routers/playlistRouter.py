# routers/playlists.py
from fastapi import APIRouter, HTTPException
from uuid import uuid4

from database import db
from models.playlists import Playlist, PlaylistCreate, PlaylistUpdate

router = APIRouter()

@router.post("/playlist_create", response_model=Playlist)
async def create_playlist(playlist: PlaylistCreate):
    playlist_dict = playlist.dict()
    playlist_dict["_id"] = str(uuid4())
    playlist_dict["song_ids"] = []
    await db["playlists"].insert_one(playlist_dict)
    playlist_dict["id"] = playlist_dict["_id"]
    return Playlist(**playlist_dict)

@router.get("/{playlist_id}", response_model=Playlist)
async def get_playlist(playlist_id: str):
    playlist = await db["playlists"].find_one({"_id": playlist_id})
    if playlist:
        playlist["id"] = playlist["_id"]
        return Playlist(**playlist)
    raise HTTPException(status_code=404, detail="Playlist not found")

@router.put("/{playlist_id}", response_model=Playlist)
async def update_playlist(playlist_id: str, playlist: PlaylistUpdate):
    playlist_dict = {k: v for k, v in playlist.dict().items() if v is not None}
    if playlist_dict:
        result = await db["playlists"].update_one(
            {"_id": playlist_id},
            {"$set": playlist_dict}
        )
        if result.modified_count == 1:
            updated_playlist = await db["playlists"].find_one({"_id": playlist_id})
            updated_playlist["id"] = updated_playlist["_id"]
            return Playlist(**updated_playlist)
    existing_playlist = await db["playlists"].find_one({"_id": playlist_id})
    if existing_playlist:
        existing_playlist["id"] = existing_playlist["_id"]
        return Playlist(**existing_playlist)
    raise HTTPException(status_code=404, detail="Playlist not found")

@router.delete("/{playlist_id}")
async def delete_playlist(playlist_id: str):
    result = await db["playlists"].delete_one({"_id": playlist_id})
    if result.deleted_count == 1:
        return {"message": "Playlist deleted successfully"}
    raise HTTPException(status_code=404, detail="Playlist not found")

@router.post("/{playlist_id}/songs/{song_id}", response_model=Playlist)
async def add_song_to_playlist(playlist_id: str, song_id: str):
    playlist = await db["playlists"].find_one({"_id": playlist_id})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    song = await db["songs"].find_one({"_id": song_id})
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in playlist["song_ids"]:
        playlist["song_ids"].append(song_id)
        await db["playlists"].update_one(
            {"_id": playlist_id},
            {"$set": {"song_ids": playlist["song_ids"]}}
        )
    playlist["id"] = playlist["_id"]
    return Playlist(**playlist)

@router.delete("/{playlist_id}/songs/{song_id}", response_model=Playlist)
async def remove_song_from_playlist(playlist_id: str, song_id: str):
    playlist = await db["playlists"].find_one({"_id": playlist_id})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if song_id in playlist["song_ids"]:
        playlist["song_ids"].remove(song_id)
        await db["playlists"].update_one(
            {"_id": playlist_id},
            {"$set": {"song_ids": playlist["song_ids"]}}
        )
    playlist["id"] = playlist["_id"]
    return Playlist(**playlist)

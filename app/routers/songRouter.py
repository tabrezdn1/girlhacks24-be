# routers/songs.py
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Request
from uuid import uuid4

from database import db
from models.songs import Song, SongCreate, SongUpdate

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all types of logs

# Create handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('songs.log')
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

router = APIRouter()


@router.get("/all_songs")
async def get_all_songs(limit: int = 100):
    logger.debug("Received request to get all songs with a limit of {limit}")
    try:
        # Fetch limited number of songs from the database
        songs_cursor = db["songs"].find().limit(limit)
        all_songs = await songs_cursor.to_list(length=limit)

        # Log the number of songs retrieved
        logger.info(f"Retrieved {len(all_songs)} songs from database")

        # Use list comprehension to process songs and convert ObjectId to string
        detailed_songs = [Song(**{**song, "id": str(song["_id"])}) for song in all_songs]

        logger.debug(f"Returning {len(detailed_songs)} songs")
        return detailed_songs

    except Exception as e:
        logger.error(f"Error retrieving all songs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve songs")


@router.post("/create_song", response_model=Song)
async def create_song(song: SongCreate):
    logger.debug(f"Received request to create song: {song}")
    try:
        song_dict = song.dict()
        song_id = str(uuid4())
        song_dict["_id"] = song_id
        logger.debug(f"Generated song ID: {song_id}")

        await db["songs"].insert_one(song_dict)
        logger.info(f"Inserted song into database with ID: {song_id}")

        song_dict["id"] = song_id
        created_song = Song(**song_dict)
        logger.debug(f"Created Song object: {created_song}")
        return created_song
    except Exception as e:
        logger.error(f"Error creating song: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{song_id}", response_model=Song)
async def get_song(song_id: str):
    logger.debug(f"Received request to get song with ID: {song_id}")
    try:
        song = await db["songs"].find_one({"_id": song_id})
        if song:
            song["id"] = song["_id"]
            retrieved_song = Song(**song)
            logger.info(f"Retrieved song: {retrieved_song}")
            return retrieved_song
        logger.warning(f"Song with ID {song_id} not found")
        raise HTTPException(status_code=404, detail="Song not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving song with ID {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/test")
async def test_route():
    return {"message": "Test route working"}



@router.put("/{song_id}", response_model=Song)
async def update_song(song_id: str, song: SongUpdate):
    logger.debug(f"Received request to update song with ID: {song_id} with data: {song}")
    try:
        song_dict = {k: v for k, v in song.dict().items() if v is not None}
        logger.debug(f"Filtered update data: {song_dict}")

        if song_dict:
            result = await db["songs"].update_one(
                {"_id": song_id},
                {"$set": song_dict}
            )
            logger.info(f"Update operation result for song ID {song_id}: {result.raw_result}")

            if result.modified_count == 1:
                updated_song = await db["songs"].find_one({"_id": song_id})
                if updated_song:
                    updated_song["id"] = updated_song["_id"]
                    updated_song_obj = Song(**updated_song)
                    logger.debug(f"Updated Song object: {updated_song_obj}")
                    return updated_song_obj

        existing_song = await db["songs"].find_one({"_id": song_id})
        if existing_song:
            existing_song["id"] = existing_song["_id"]
            existing_song_obj = Song(**existing_song)
            logger.info(f"No changes made to song with ID {song_id}, returning existing song")
            return existing_song_obj

        logger.warning(f"Song with ID {song_id} not found for update")
        raise HTTPException(status_code=404, detail="Song not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating song with ID {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/{song_id}")
async def delete_song(song_id: str):
    logger.debug(f"Received request to delete song with ID: {song_id}")
    try:
        result = await db["songs"].delete_one({"_id": song_id})
        logger.info(f"Delete operation result for song ID {song_id}: {result.raw_result}")

        if result.deleted_count == 1:
            logger.info(f"Song with ID {song_id} deleted successfully")
            return {"message": "Song deleted successfully"}

        logger.warning(f"Song with ID {song_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Song not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting song with ID {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

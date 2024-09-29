import os
import json
import logging

from fastapi import APIRouter, HTTPException
from langchain.globals import set_debug
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Enable LangChain debugging
set_debug(True)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("No OPENAI_API_KEY provided. Set the OPENAI_API_KEY environment variable.")

if not TAVILY_API_KEY:
    raise ValueError("No TAVILY_API_KEY provided. Set the TAVILY_API_KEY environment variable.")

# Initialize the OpenAI Chat model
openai_chat_model = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY, temperature=1.0)

# Initialize FastAPI router
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture all types of logs

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler('songs.log')
file_handler.setLevel(logging.DEBUG)

# Define log format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger if not already present
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def tavily_search(song_title: str, artist_name: str) -> dict:
    """
    Finds YouTube and Spotify links for a given song title and artist using Tavily.

    :param song_title: Title of the song to search for.
    :param artist_name: Name of the artist.
    :return: Dictionary containing YouTube and Spotify links.
    """
    # Initialize the TavilySearchResults tool
    try:
        tavily_search_tool = TavilySearchResults(max_results=15, api_key=TAVILY_API_KEY)
        logger.debug("Initialized TavilySearchResults tool successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize TavilySearchResults tool: {e}")
        return {"youtube_link": None, "spotify_link": None}

    # Construct the search queries with specific keywords to target YouTube and Spotify
    youtube_query = f'"{song_title}" "{artist_name}" official music video site:youtube.com'
    spotify_query = f'"{song_title}" "{artist_name}" site:spotify.com'

    logger.debug(f"Constructed YouTube query: {youtube_query}")
    logger.debug(f"Constructed Spotify query: {spotify_query}")

    try:
        # Execute the YouTube search
        youtube_results = tavily_search_tool.run(youtube_query)
        logger.debug(f"YouTube search results: {youtube_results}")

        # Execute the Spotify search
        spotify_results = tavily_search_tool.run(spotify_query)
        logger.debug(f"Spotify search results: {spotify_results}")
    except Exception as e:
        logger.error(f"Error during search execution: {e}")
        return {"youtube_link": None, "spotify_link": None}

    # Helper function to extract valid URL
    def extract_valid_url(results, platform):
        if results and isinstance(results, list):
            for result in results:
                url = result.get('url')
                if url:
                    if platform == 'youtube' and 'youtube.com/watch' in url:
                        logger.debug(f"Valid YouTube URL found: {url}")
                        return url
                    elif platform == 'spotify' and 'spotify.com/track' in url:
                        logger.debug(f"Valid Spotify URL found: {url}")
                        return url
            logger.warning(f"No valid {platform.capitalize()} URL found in the results.")
        else:
            logger.warning(f"No results returned for {platform.capitalize()} search.")
        return None

    # Extract YouTube link
    youtube_link = extract_valid_url(youtube_results, 'youtube')

    # Extract Spotify link
    spotify_link = extract_valid_url(spotify_results, 'spotify')

    logger.info(f"Final YouTube link: {youtube_link}")
    logger.info(f"Final Spotify link: {spotify_link}")

    return {
        "youtube_link": youtube_link,
        "spotify_link": spotify_link
    }
def enrich_song_links(songs: list) -> list:
    """
    Enriches each song in the list with YouTube and Spotify links.

    :param songs: List of songs with 'song_name' and 'artist' fields.
    :return: List of songs updated with 'youtube_link' and 'spotify_link'.
    """
    updated_songs = []
    for song in songs:
        links = tavily_search(song['song_name'], song['artist'])

        # Check if both YouTube and Spotify links are available
        if links.get('youtube_link') and links.get('spotify_link'):
            song.update(links)
            updated_songs.append(song)
            logger.debug(f"Added song: {song['song_name']} by {song['artist']}")
        else:
            logger.info(f"Skipping song '{song['song_name']}' by '{song['artist']}' due to missing links.")

    return updated_songs

# Define the song recommendation prompt
song_recommendation_prompt = ChatPromptTemplate.from_template("""
Generate a list of 3 songs that would suit a person in the following mood: {input}

Return only a JSON array of objects, each with 'song_name', 'artist', and 'mood_match' fields. The 'mood_match' field should briefly explain why the song fits the given mood. Do not include any additional text, explanations, or formatting such as code blocks.
""")
def parse_llm_response(response: str) -> dict:
    """
    Parses the response from the language model.

    :param response: JSON string response from the LLM.
    :return: Parsed JSON as a dictionary.
    """
    try:
        logging.info(f"Response from LLM: {response}")
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {response}")
        return {"error": "Failed to generate song list"}

def fetch_song_info(songs: list) -> list:
    """
    Fetches YouTube and Spotify links for each song in the list.

    :param songs: List of songs with 'song_name' and 'artist' fields.
    :return: List of songs enriched with 'youtube_link' and 'spotify_link'.
    """
    return enrich_song_links(songs)

# Define the song recommendation chain
song_recommendation_chain = (
    RunnablePassthrough().assign(
        songs=(
            song_recommendation_prompt
            | openai_chat_model
            | StrOutputParser()
            | parse_llm_response
            | fetch_song_info
        )
    )
)

# Define the message formatting prompt
format_message_prompt = ChatPromptTemplate.from_template("""
You are a helpful  music assistant.
Given the user input and the list of songs with links, create a friendly response.
For each song, use the song name and artist to add extra information such as album, language, release year, and genre.

User input: {input}
Songs: {songs}

Format your response as a JSON object with 'greeting' and 'recommendations' fields.
Each recommendation should include the following fields:
- song_name
- artist
- youtube_link
- spotify_link
- album
- language
- release_year

**Return only the JSON object without any additional text, explanations, or formatting such as code blocks.**
""")

# Define the message formatting chain
format_message_chain = (
    format_message_prompt
    | openai_chat_model
    | StrOutputParser()
    | parse_llm_response
)

format_message_chain = (
    format_message_prompt
    | openai_chat_model
    | StrOutputParser()
    | parse_llm_response
)

# Combine the recommendation and formatting chains
combined_chain = song_recommendation_chain | format_message_chain

# Define the request model
class SongRequest(BaseModel):
    input: str

@router.post("/process-song")
async def process_song(request: SongRequest):
    """
    Endpoint to process song recommendations based on user input.

    :param request: SongRequest containing the user's mood input.
    :return: JSON object with a greeting and song recommendations.
    """
    try:
        # Prepare the input for the combined chain
        chain_input = {"input": request.input}

        # Run the combined chain asynchronously
        result = await combined_chain.ainvoke(chain_input)

        # Log the response
        logger.info(f"Chain Response: {result}")

        # Check for errors in the response
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

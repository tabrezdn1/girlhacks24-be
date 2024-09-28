import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain.globals import set_debug
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
from langchain.schema.output_parser import StrOutputParser
import json
import logging
set_debug=True
# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("No OPENAI_API_KEY provided. Set the OPENAI_API_KEY environment variable.")

if not TAVILY_API_KEY:
    raise ValueError("No TAVILY_API_KEY provided. Set the TAVILY_API_KEY environment variable.")

# Initialize the OpenAI Chat model
llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY)
router = APIRouter()
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

def tavily_search(song_name: str, artist: str) -> dict:
    """Find YouTube and Spotify links for songs given a song name and artist."""
    # Initialize the TavilySearchResults tool
    tavily_tool = TavilySearchResults(max_results=1, api_key=TAVILY_API_KEY)

    # Construct the queries
    query = f"{song_name} {artist} youtube"
    query2 = f"{song_name} {artist} spotify"

    # Use the Tavily tool
    results = tavily_tool.run(query)
    spotify_results = tavily_tool.run(query2)

    # Process the results to extract YouTube and Spotify links
    youtube_link = None
    spotify_link = None
    if results and isinstance(results, list) and len(results) > 0:
        first_result = results[0]
        youtube_link = first_result.get('url')

    if spotify_results and isinstance(spotify_results, list) and len(spotify_results) > 0:
        first_spotify_result = spotify_results[0]
        spotify_link = first_spotify_result.get('url')

    return {
        "youtube_link": youtube_link,
        "spotify_link": spotify_link
    }
# Initialize OpenAI client


# Song recommendation chain
song_recommendation_prompt = ChatPromptTemplate.from_template("""
Based on the user's input: {input}
Generate a list of 3 disco songs. Return only a JSON array of objects, each with 'song_name' and 'artist' fields. Do not include any additional text, explanations, or formatting such as code blocks.
""")
def parse_llm_response(response):
    try:
        logging.info(f" response from first chain{response}")

        return json.loads(response)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {response}")
        return {"error": "Failed to generate song list"}


def fetch_song_info(songs):
    updated_songs = []
    for song in songs:
        info = tavily_search(song['song_name'], song['artist'])

        # Check if at least one link is available
        if info.get('youtube_link') or info.get('spotify_link'):
            song.update(info)
            updated_songs.append(song)
            logger.debug(f"Added song: {song['song_name']} by {song['artist']}")
        else:
            logger.info(f"Skipping song '{song['song_name']}' by '{song['artist']}' due to missing links.")

    return updated_songs

song_recommendation_chain = (
    RunnablePassthrough().assign(
        songs=(
            song_recommendation_prompt 
            | llm 
            | StrOutputParser() 
            | parse_llm_response
            | fetch_song_info
        )
    )
)

# Message formatting chain
format_message_prompt = ChatPromptTemplate.from_template("""
You are a helpful disco music assistant. 
Given the user input and the list of songs with links, create a friendly response.
User input: {input}
Songs: {songs}
Format your response as a JSON object with 'greeting' and 'recommendations' fields.
**Return only the JSON object without any additional text, explanations, or formatting such as code blocks.**
""")

format_message_chain = format_message_prompt | llm | StrOutputParser() | parse_llm_response

# Combine the chains
combined_chain = song_recommendation_chain | format_message_chain

class SongRequest(BaseModel):
    input: str

@router.post("/process-song")
async def process_song(request: SongRequest):
    try:
        # Prepare the input for the combined chain
        chain_input = {"input": request.input}

        # Run the combined chain
        result = await combined_chain.ainvoke(chain_input)

        # Log the response
        logger.info(f"Chain Response: {result}")

        # Check if there was an error in song generation
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")
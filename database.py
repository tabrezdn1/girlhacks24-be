# database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables

# Retrieve environment variables
MONGODB_USER = os.getenv("MONGODB_USER")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_CLUSTER = os.getenv("MONGODB_CLUSTER")
MONGODB_DB = os.getenv("MONGODB_DB")

# Construct the MongoDB connection string
MONGODB_URL = (
    f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/"
    f"{MONGODB_DB}?retryWrites=true&w=majority"
)

# Initialize the MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URL)
db = client[MONGODB_DB]

# database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

from setting import config

# Load environment variables

# Retrieve environment variables
MONGODB_USER = config.MONGODB_USER
MONGODB_PASSWORD = config.MONGODB_PASSWORD
MONGODB_CLUSTER = config.MONGODB_CLUSTER
MONGODB_DB = config.MONGODB_DB

# Construct the MongoDB connection string
MONGODB_URL = (
    f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/"
    f"{MONGODB_DB}?retryWrites=true&w=majority"
)

# Initialize the MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URL)
db = client[MONGODB_DB]

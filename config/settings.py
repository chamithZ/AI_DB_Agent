from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")  # MongoDB connection string
DB_NAME = "mydatabase"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]  # Select database
collection = db["users"]  # Select collection (table)

def get_collection():
    """Returns the MongoDB collection"""
    return collection

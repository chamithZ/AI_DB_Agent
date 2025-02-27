from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("Missing MongoDB configuration in environment variables")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]  # Database instance

def get_db():
    """Returns the MongoDB database instance"""
    return db

def get_all_collections():
    """Returns a list of all collection names in the database"""
    return db.list_collection_names()

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = "mongodb+srv://skillSpanAdmin:16820@cluster0.dxw50go.mongodb.net/SkillSpanDB?retryWrites=true&w=majority "  # MongoDB connection string
DB_NAME = "SkillSpanDB"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]  # Select database
collection = db["users"]  # Select collection (table)


users = list(collection.find())  # Get all documents


def get_collection():
    """Returns the MongoDB collection"""
    return collection

#mongodb+srv://skillSpanAdmin:16820@cluster0.dxw50go.mongodb.net/SkillSpanDB?retryWrites=true&w=majority 
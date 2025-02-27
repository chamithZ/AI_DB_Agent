from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from bson import ObjectId  # Make sure you have this import to work with ObjectId
from agent import DBAgent

# Initialize FastAPI app
app = FastAPI()

# Instantiate DBAgent
agent = DBAgent()

# Define the request body model
class QueryRequest(BaseModel):
    query: str  # The query from the user

# Helper function to convert ObjectId to string
def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

@app.post("/query")
async def query_database(request: QueryRequest):
    # Extract user input
    user_input = request.query
    
    # Query the database through the agent
    response = agent.query_database(user_input)
    
    # Convert all ObjectIds to strings
    response = convert_objectid_to_str(response)
    
    # Return raw output directly as the response
    return {"result": response}

# Run the agent close method when the application shuts down
@app.on_event("shutdown")
def shutdown_event():
    agent.close()

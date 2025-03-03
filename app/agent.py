import os
import requests
import json
import logging
import re
from db import get_db, get_all_collections, client  # Import DB connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DBAgent:
    def __init__(self, max_retries=3, timeout=10):
        self.api_url = os.getenv("LLM_API_URL")
        self.api_key = os.getenv("GROQ_API_KEY")  # Securely load API key
        if not self.api_key:
            raise ValueError("Missing GROQ API key in environment variables")

        self.max_retries = max_retries
        self.timeout = timeout
        self.db = get_db()
        self.client = client
        self.conversation_history = []
        self.available_collections = get_all_collections()
        self.collection_fields = self._get_collection_fields()

    def _get_collection_fields(self):
        collection_fields = {}
        for collection_name in self.available_collections:
            sample_doc = self.db[collection_name].find_one()
            if sample_doc:
                collection_fields[collection_name] = list(sample_doc.keys())
        logging.info(f"Collection fields: {collection_fields}")
        return collection_fields

    def query_database(self, user_prompt):
        system_prompt = (
            "You are an AI database assistant. Generate MongoDB queries in JSON format "
            "with keys 'collection', 'operation', and 'filter'. "
            "For insert/update, include 'data'. Ensure the collection exists. "
            f"Available collections: {self.available_collections}. "
            "Supported operations: 'find' (GET), 'insert' (POST), 'update' (PUT), 'delete' (DELETE). "
            "Do not include explanations."
        )

        payload = {
            "model": os.getenv("MODEL_NAME"),
            "messages": [
                {"role": "system", "content": system_prompt},
                *self.conversation_history,
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 800,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    query_dict = self._extract_query(data["choices"][0]["message"]["content"])
                    if query_dict:
                        return self.execute_query(query_dict)
                logging.error(f"API error: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed (Attempt {attempt}/{self.max_retries}): {e}")
        return {"error": "Max retries reached. No response from LLM."}

    def _extract_query(self, response):
        clean_response = re.sub(r'<think>|</think>', '', response)
        match = re.search(r'```json\n(.*?)\n```', clean_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logging.error("Failed to parse JSON from response.")
        return None

    def execute_query(self, query_dict):
        try:
            collection_name = query_dict.get("collection")
            operation = query_dict.get("operation")
            query_filter = query_dict.get("filter", {})
            data = query_dict.get("data", {})

            if collection_name not in self.available_collections:
                return {"error": f"Collection '{collection_name}' does not exist."}
            
            collection = self.db[collection_name]
            
            if operation == "find":
                return list(collection.find(query_filter))
            elif operation == "insert":
                if isinstance(data, list):
                    collection.insert_many(data)
                else:
                    collection.insert_one(data)
                return {"success": "Data inserted successfully."}
            elif operation == "update":
                result = collection.update_many(query_filter, {"$set": data})
                return {"success": f"{result.modified_count} documents updated."}
            elif operation == "delete":
                result = collection.delete_many(query_filter)
                return {"success": f"{result.deleted_count} documents deleted."}
            else:
                return {"error": "Unsupported operation."}
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return {"error": str(e)}

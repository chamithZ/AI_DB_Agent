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
        """Retrieve all collections and their field names."""
        collection_fields = {}
        for collection_name in self.available_collections:
            sample_doc = self.db[collection_name].find_one()
            if sample_doc:
                collection_fields[collection_name] = list(sample_doc.keys())
        logging.info(f"Collection fields: {collection_fields}")
        return collection_fields

    def _match_collection(self, user_prompt):
        """Finds the best matching collection and relevant fields based on user input."""
        matched_collection = None
        max_matches = 0
        best_fields = []

        for collection, fields in self.collection_fields.items():
            found_fields = [field for field in fields if field.lower() in user_prompt.lower()]
            if found_fields:
                matched_collection = collection
                best_fields = found_fields
                break  # Stop once we find a match (you can extend this logic to more matches if needed)

        if matched_collection:
            logging.info(f"Matched collection: {matched_collection} with fields {best_fields}")
        else:
            logging.warning("No matching collection found. Trying more general matching...")

            # If no match is found, use general matching with collection names.
            for collection in self.collection_fields.keys():
                if collection.lower() in user_prompt.lower():
                    matched_collection = collection
                    best_fields = self.collection_fields[collection]
                    logging.info(f"General match found for collection: {matched_collection}")
                    break

        return matched_collection, best_fields

    def query_database(self, user_prompt):
        """Generates and executes a MongoDB query based on the user input."""
        collection_name, matched_fields = self._match_collection(user_prompt)

        if not collection_name:
            return {"error": "No matching collection found for the given parameters."}

        system_prompt = (
            "You are an AI database assistant. Generate MongoDB queries in JSON format "
            "with keys 'collection' and 'filter'. Ensure that the collection name exists in the database. "
            f"Available collections: {self.available_collections}. "
            f"Use only these fields for '{collection_name}': {self.collection_fields[collection_name]}. "
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
                    llm_response = data["choices"][0]["message"]["content"]
                    logging.info(f"Raw LLM Response: {llm_response}")

                    query_dict = self._extract_query(llm_response)
                    if query_dict:
                        result = self.execute_query(query_dict)
                        return result
                    else:
                        return {"error": "Invalid query format received from LLM."}
                else:
                    logging.error(f"API error: {response.status_code} - {response.text}")
                    return {"error": response.text}

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed (Attempt {attempt}/{self.max_retries}): {e}")

        return {"error": "Max retries reached. No response from LLM."}

    def _extract_query(self, response):
        """Extracts the MongoDB query JSON from the response."""
        clean_response = re.sub(r'<think>|</think>', '', response)
        match = re.search(r'```json\n(.*?)\n```', clean_response, re.DOTALL)

        if match:
            try:
                query_string = match.group(1)
                query_dict = json.loads(query_string)
                logging.info(f"Parsed query: {query_dict}")
                return query_dict if isinstance(query_dict.get("filter"), dict) else None
            except json.JSONDecodeError:
                logging.error("Failed to parse JSON from response.")
                return None
        return None

    def execute_query(self, query_dict):
        """Executes MongoDB queries and returns results."""
        try:
            collection_name = query_dict.get("collection", "")
            query_filter = query_dict.get("filter", {})

            if not collection_name:
                return {"error": "Collection name is required in query."}

            if collection_name not in self.available_collections:
                return {"error": f"Collection '{collection_name}' does not exist."}

            if isinstance(query_filter, str):
                try:
                    query_filter = json.loads(query_filter)
                except json.JSONDecodeError:
                    return {"error": "Filter is not a valid JSON object."}

            if not isinstance(query_filter, dict):
                return {"error": "Filter is not a valid dictionary."}

            # Ensure the filter only contains valid fields
            allowed_fields = self.collection_fields.get(collection_name, [])
            filtered_query = {k: v for k, v in query_filter.items() if k in allowed_fields}

            collection = self.db[collection_name]
            results = list(collection.find(filtered_query))
            return results

        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return {"error": f"Error executing query: {str(e)}"}

    def close(self):
        """Closes database connection properly."""
        self.client.close()

# Setting up logging
logging.basicConfig(level=logging.INFO)

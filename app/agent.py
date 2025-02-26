import requests
import json
import logging
import re
from db import get_collection, client  # Import DB connection

class DBAgent:
    def __init__(self, max_retries=3, timeout=10):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = "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"  
        self.max_retries = max_retries
        self.timeout = timeout
        self.db = get_collection()
        self.client = client  # MongoDB client
        self.conversation_history = []
         
  

    def query_database(self, user_prompt):
        """Generates a query for the database using LLM and executes it."""
        system_prompt = (
            "You are an AI database assistant. Generate MongoDB queries in JSON format "
            "with keys 'collection' and 'filter'. Do not include explanations."
        )
        
        payload = {
            "model": "deepseek-r1-distill-llama-70b",
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
                    print("Raw LLM Response:", llm_response)

                    query_dict = self._extract_query(llm_response)
                    if query_dict:
                        logging.info(f"Extracted query filter: {query_dict.get('filter')} (Type: {type(query_dict.get('filter'))})")
                        result = self.execute_query(query_dict)
                        return result
                    else:
                        return {"error": "Invalid query format received from LLM."}
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    return {"error": response.text}
            
            except requests.exceptions.RequestException as e:
                print(f"Request failed (Attempt {attempt}/{self.max_retries}): {e}")
        
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
                if isinstance(query_dict.get("filter"), dict):
                    return query_dict
                else:
                    return None
            except json.JSONDecodeError:
                return None
        return None

    def execute_query(self, query_dict):
        """Executes MongoDB queries and returns results."""
        try:
            collection_name = query_dict.get("collection", "")
            query_filter = query_dict.get("filter", {})

            if not collection_name:
                return {"error": "Collection name is required in query."}

            if isinstance(query_filter, str):
                try:
                    query_filter = json.loads(query_filter)
                except json.JSONDecodeError:
                    return {"error": "Filter is not a valid JSON object."}

            if not isinstance(query_filter, dict):
                return {"error": "Filter is not a valid dictionary."}

            # Execute MongoDB query
            collection = self.db  # `self.db` already holds the collection
            results = list(collection.find(query_filter))
            return results

        except Exception as e:
            return {"error": f"Error executing query: {str(e)}"}

    def close(self):
        """Closes database connection properly."""
        self.client.close()

# Setting up logging
logging.basicConfig(level=logging.INFO)

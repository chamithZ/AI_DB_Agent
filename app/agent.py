import requests
import json
from db import get_collection

class DBAgent:
    def __init__(self, max_retries=3, timeout=10):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = "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"
        self.max_retries = max_retries
        self.timeout = timeout
        self.conversation_history = []  # Store conversation history

    def query_database(self, user_prompt):
        """Generates a query for the database using LLM and executes it."""
        system_prompt = "You are an AI database assistant. Generate MongoDB queries based on user requests."
        
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
                    
                    # Store conversation history
                    self._update_conversation_history(user_prompt, llm_response)
                    
                    # Execute MongoDB query
                    result = self.execute_query(llm_response)
                    return result
                
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    return {"error": response.text}
            
            except requests.exceptions.RequestException as e:
                print(f"Request failed (Attempt {attempt}/{self.max_retries}): {e}")
        
        return {"error": "Max retries reached. No response from LLM."}

    def execute_query(self, query_string):
        """Executes MongoDB queries and returns results."""
        try:
            query_dict = json.loads(query_string)
            collection_name = query_dict.get("collection", "")
            query_filter = query_dict.get("filter", {})

            if not collection_name:
                return {"error": "Collection name is required in query."}

            collection = get_collection(collection_name)  # Get the correct collection
            results = list(collection.find(query_filter, {"_id": 0}))  # Exclude `_id`
            return results
        
        except json.JSONDecodeError:
            return {"error": "Invalid query format received from LLM."}

    def _update_conversation_history(self, user_message, assistant_response):
        """Maintains chat history for better context in queries."""
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_response}
        )

        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def close(self):
        """Closes database connection."""
        client.close()

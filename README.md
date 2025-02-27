AI_DB_Agent 🚀
An intelligent database query agent that understands natural language and retrieves structured results from MongoDB.

Overview
AI_DB_Agent is an AI-powered database query system designed to process natural language queries and convert them into structured database queries. It supports multiple databases (starting with MongoDB) and returns raw query results without modification.

Features
✅ Natural Language Processing: Converts user input into structured MongoDB queries.
✅ FastAPI Integration: Exposes a REST API for easy interaction.
✅ Multi-Database Support: Designed to extend beyond MongoDB.
✅ Raw Query Results: Returns data exactly as retrieved from the database.
✅ Modular & Extensible: Built with flexibility in mind for future database integrations.

Architecture
1️⃣ Client → Sends queries via API.
2️⃣ API Gateway (FastAPI) → Handles HTTP requests and forwards them to the agent.
3️⃣ DBAgent →

Parses natural language queries.
Converts them into structured MongoDB queries.
Fetches results from the database.
4️⃣ Database (MongoDB) → Stores and retrieves requested data.

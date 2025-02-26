from fastapi import FastAPI
from app.agent import query_mongo_with_llm

app = FastAPI()

@app.get("/query/")
def query_db(nl_query: str):
    result = query_mongo_with_llm(nl_query)
    return {"results": result}

from fastapi import FastAPI
from server.rag_chain import build_rag
from server.agent import rag_agent

app = FastAPI()
qa = build_rag()

@app.post("/query")
def query_rag(query: str):
    return rag_agent(query, qa)

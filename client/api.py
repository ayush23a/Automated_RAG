from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from server.rag_chain import build_rag
from server.agent import rag_agent
from server.ingestion import ingest_docs
import shutil
import os

app = FastAPI()

retriever = build_rag()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def query_rag(req: QueryRequest):
    return rag_agent(req.query, retriever)

UPLOAD_DIR = "data/docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ingest_docs(UPLOAD_DIR)

    return {
        "status": "success",
        "filename": file.filename
    }

from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from server.agent import rag_agent
from server.ingestion import ingest_docs
import shutil
import os
import chromadb

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

@app.post("/query")
def query_rag(req: QueryRequest):
    return rag_agent(req.query, req.session_id)

BASE_UPLOAD_DIR = "data/docs"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form("default")
):
    session_dir = os.path.join(BASE_UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_path = os.path.join(session_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    docs_ingested = ingest_docs(session_dir, session_id)

    return {
        "status": "success",
        "filename": file.filename,
        "docs_ingested": docs_ingested,
        "session_id": session_id
    }

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    # Delete uploaded files
    session_dir = os.path.join(BASE_UPLOAD_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        
    # Delete Chroma collection if possible
    try:
        chroma_client = chromadb.PersistentClient(path="data/vectordb")
        collection_name = f"session_{session_id}"
        collection_name = "".join(c if c.isalnum() else "_" for c in collection_name)
        chroma_client.delete_collection(name=collection_name)
    except Exception as e:
        # Collection might not exist or error deleting
        print(f"Error deleting collection: {e}")

    return {"status": "success", "message": f"Session {session_id} deleted."}

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.server.agent import rag_agent
from backend.server.ingestion import ingest_docs
import shutil
import os
import chromadb
import requests
import urllib.parse

load_dotenv()

app = FastAPI()

# CORS — allow the Streamlit frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Config ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


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


@app.get("/login")
def login_with_google():
    redirect_uri = f"{BACKEND_URL}/auth/callback"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online"
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@app.get("/auth/callback")
def auth_callback(code: str):
    redirect_uri = f"{BACKEND_URL}/auth/callback"

    # Exchange code for token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    )
    res_json = token_response.json()
    id_token = res_json.get("id_token")

    if id_token:
        return RedirectResponse(url=f"{FRONTEND_URL}/?token={id_token}")
    else:
        return {"error": "Authentication failed", "details": res_json}


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
        print(f"Error deleting collection: {e}")

    return {"status": "success", "message": f"Session {session_id} deleted."}

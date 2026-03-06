# Kriyamān AI

A stateful, Agentic Retrieval-Augmented Generation (RAG) system built with **LangGraph**. It acts as a hierarchical decision-making AI that intelligently switches between local knowledge, document-specific retrieval, and real-time web search based on user intent.

## Core Features

- **Agentic Routing (LangGraph)**: The system analyzes queries to detect one of 5 intents (`casual`, `fact_check`, `doc_query`, `deep_research`, `mixed`) and routes execution dynamically to the best subsystem.
- **Session-Scoped Document Isolation**: Uploaded PDFs and generated vector embeddings (`Chroma`) are strictly isolated via `session_id`. Documents do not bleed context into other sessions, and users can cleanly erase their session's memory at any time.
- **Web-Grounded Fact Checking**: Integrates **SerpAPI** for time-sensitive or external queries, bypassing the local vector DB entirely to provide real, structurally cited data. 
- **Robust LLM Fallbacks**: Built with fault-tolerance. If the primary cloud LLM (`gemini-2.5-flash`) exhausts its API rate-limit quota, the LangGraph final synthesizer seamlessly falls back to **Groq** (`llama-3.3-70b-versatile`) to guarantee a fast, high-quality response.
- **Document Ingestion**: Upload and process PDF files securely using LangChain's `PyPDFLoader` coupled with semantic aware overlapping chunks.
- **Web UI & API Engine**: Fast and slick interactive interface built with Streamlit, powered by a robust Python FastAPI backend server.

## Architecture Nodes

- **Frontend**: 
  - [ui.py](frontend/ui.py): Streamlit app featuring session management and chat tracking.
- **Backend API**:
  - [api.py](backend/api.py): FastAPI endpoints handling multi-part file payloads and LangGraph invokations.
- **Backend LangGraph Server**:
  - [state.py](backend/server/state.py): Defines the `TypedDict` Graph state memory object passed across all nodes.
  - [nodes.py](backend/server/nodes.py): Houses individual node logics: `Intent Classifier`, `Strategy Router`, `Doc RAG`, `Web Search`, `Final Synthesizer`.
  - [agent.py](backend/server/agent.py): Compiles the entire LangGraph workflow.
  - [ingestion.py](backend/server/ingestion.py): Handles scoped local ingestion for documents.

## Prerequisites

- Python 3.8+
- (Optional but recommended) Google API key for **Gemini**.
- **Groq API key** for the fallback AI model (`llama-3.3-70b-versatile`).
- (Optional but recommended) **SerpAPI API key** for handling `fact_check` live requests.

## Setup

1. Clone the repository and initialize the virtual environment:
   ```sh
   git clone <repository-url>
   cd Automated_RAG
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   SERPAPI_API_KEY=your_serpapi_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

## Usage

You must run both the API backend and the Streamlit UI simultaneously in separate terminals:

1. **Start the backend:**
   ```sh
   source venv/bin/activate
   uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```

2. **Start the UI:**
   ```sh
   source venv/bin/activate
   streamlit run frontend/ui.py
   ```

3. Navigate your browser to `http://localhost:8501`. 
4. Upload documents to bind them specifically to your active Session ID.
5. Hit **"🗑️ Clear Session & Start Fresh"** anytime to physically delete the vector files and uploaded docs from the server dynamically.

## Project Structure

```text
.
├── backend/
│   ├── api.py              # FastAPI endpoints
│   ├── requirements.txt
│   └── server/
│       ├── agent.py        # LangGraph agent compilation
│       ├── ingestion.py    # Document ingest logic
│       ├── llm.py          # LLM configurations (Gemini/Groq/Ollama)
│       ├── nodes.py        # Graph nodes (Intent, RAG, Web Search)
│       ├── rag_chain.py    # Vector DB setup & retriever
│       └── state.py        # TypedDict state structure
├── frontend/
│   ├── ui.py               # Streamlit chat interface
│   └── requirements.txt
├── data/
│   ├── docs/               # Uploaded session PDFs
│   └── vectordb/           # Chroma vector database storage
├── venv/                   # Python virtual environment
├── README.md               # This file
├── render.yaml             # Render deployment configuration
└── .env                    # Secret API keys
```

# Automated RAG

A stateful, Agentic Retrieval-Augmented Generation (RAG) system built with **LangGraph**. It acts as a hierarchical decision-making AI that intelligently switches between local knowledge, document-specific retrieval, and real-time web search based on user intent.

## Core Features

- **Agentic Routing (LangGraph)**: The system analyzes queries to detect one of 5 intents (`casual`, `fact_check`, `doc_query`, `deep_research`, `mixed`) and routes execution dynamically to the best subsystem.
- **Session-Scoped Document Isolation**: Uploaded PDFs and generated vector embeddings (`Chroma`) are strictly isolated via `session_id`. Documents do not bleed context into other sessions, and users can cleanly erase their session's memory at any time.
- **Web-Grounded Fact Checking**: Integrates **SerpAPI** for time-sensitive or external queries, bypassing the local vector DB entirely to provide real, structurally cited data. 
- **Robust LLM Fallbacks**: Built with fault-tolerance. If a primary cloud LLM like `gemini-3-flash-preview` exhausts its API rate-limit quota, the LangGraph final synthesizer flawlessly falls back to a locally hosted `llama3.2:1b` model through Ollama to guarantee a response.
- **Document Ingestion**: Upload and process PDF files securely using LangChain's `PyPDFLoader` coupled with semantic aware overlapping chunks.
- **Web UI & API Engine**: Fast and slick interactive interface built with Streamlit, powered by a robust Python FastAPI backend server.

## Architecture Nodes

- **Client**: 
  - [ui.py](client/ui.py): Streamlit app featuring session management and chat tracking.
  - [api.py](client/api.py): FastAPI endpoints handling multi-part file payloads and LangGraph invokations.
- **LangGraph Server**:
  - [state.py](server/state.py): Defines the `TypedDict` Graph state memory object passed across all nodes.
  - [nodes.py](server/nodes.py): Houses individual node logics: `Intent Classifier`, `Strategy Router`, `Doc RAG`, `Web Search`, `Final Synthesizer`.
  - [agent.py](server/agent.py): Compiles the entire LangGraph workflow.
  - [ingestion.py](server/ingestion.py): Handles scoped local ingestion for documents.

## Prerequisites

- Python 3.8+
- Ollama installed and running locally with the `llama3.2:1b` model pulled.
- (Optional but recommended) Google API key for **Gemini 3.0**.
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
   ```

4. Run Ollama (ensure `llama3.2:1b` is pulled as the core fallback):
   ```sh
   ollama serve
   ```

## Usage

You must run both the API backend and the Streamlit UI simultaneously in separate terminals:

1. **Start the backend:**
   ```sh
   source venv/bin/activate
   uvicorn client.api:app --host 0.0.0.0 --port 8000
   ```

2. **Start the UI:**
   ```sh
   source venv/bin/activate
   streamlit run client/ui.py
   ```

3. Navigate your browser to `http://localhost:8501`. 
4. Upload documents to bind them specifically to your active Session ID.
5. Hit **"🗑️ Clear Session & Start Fresh"** anytime to physically delete the vector files and uploaded docs from the server dynamically.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

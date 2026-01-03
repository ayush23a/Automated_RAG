# Automated RAG

A Retrieval-Augmented Generation (RAG) system that allows users to upload PDF documents, index them into a vector database, and query for answers using large language models (LLMs).

## Features

- **Document Ingestion**: Upload and process PDF files using [PyPDFLoader](https://python.langchain.com/docs/modules/data_connection/document_loaders/pdf) from LangChain.
- **Vector Database**: Store document chunks in [Chroma](https://www.trychroma.com/) vector database with [OllamaEmbeddings](https://python.langchain.com/docs/integrations/llms/ollama).
- **Query Answering**: Retrieve relevant documents and generate answers using [OllamaLLM](https://python.langchain.com/docs/integrations/llms/ollama) or [ChatGoogleGenerativeAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai).
- **Web UI**: Interactive interface built with Streamlit for uploading documents and querying.
- **API Backend**: FastAPI server handling uploads and queries.

## Architecture

- **Client**: 
  - [ui.py](client/ui.py): Streamlit app for user interaction.
  - [api.py](client/api.py): FastAPI endpoints for `/query` and `/upload`.
- **Server**:
  - [agent.py](server/agent.py): RAG agent logic using [`rag_agent`](server/agent.py) function.
  - [ingestion.py](server/ingestion.py): Document ingestion pipeline with [`ingest_docs`](server/ingestion.py).
  - [llm.py](server/llm.py): LLM configurations for Ollama and Gemini.
  - [rag_chain.py](server/rag_chain.py): Vector database setup with [`build_rag`](server/rag_chain.py).

## Prerequisites

- Python 3.8+
- Ollama installed and running (with `llama3.2:1b` model)
- (Optional) Google API key for Gemini

## Setup

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd Automated_RAG
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```
   GOOGLE_API_KEY=your_google_api_key  # Optional
   ```

4. Run Ollama (ensure `llama3.2:1b` is pulled):
   ```sh
   ollama serve
   ```

## Usage

1. Start the backend:
   ```sh
   uvicorn client.api:app --host 0.0.0.0 --port 8000
   ```

2. Start the UI:
   ```sh
   streamlit run client/ui.py
   ```

3. Open the Streamlit app in your browser (usually at `http://localhost:8501`).

4. Upload PDF documents via the sidebar.

5. Ask questions in the text input and click "Ask" to get answers with sources.

## Project Structure

```
.
├── client/
│   ├── api.py          # FastAPI backend
│   └── ui.py           # Streamlit UI
├── server/
│   ├── agent.py        # RAG agent
│   ├── ingestion.py    # Document ingestion
│   ├── llm.py          # LLM configurations
│   └── rag_chain.py    # Vector DB setup
├── data/
│   └── docs/           # Uploaded documents
│   └── vectordb/       # Chroma vector database
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os

def ingest_docs(folder="data/docs", session_id: str = "default"):
    documents = []

    if not os.path.exists(folder):
        return 0

    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(folder, file))
            # Tag each doc with source info explicitly
            loaded_docs = loader.load()
            for doc in loaded_docs:
                doc.metadata["source"] = file
            documents.extend(loaded_docs)

    if not documents:
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model="llama3.2:1b")

    collection_name = f"session_{session_id}"
    # Replace anything but alphanumeric and underscores to ensure valid collection names
    collection_name = "".join(c if c.isalnum() else "_" for c in collection_name)

    vectordb = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=collection_name,
        persist_directory="data/vectordb"
    )

    return len(documents)

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

def build_rag(session_id: str = "default"):
    embeddings = OllamaEmbeddings(model="llama3.2:1b")
    
    collection_name = f"session_{session_id}"
    collection_name = "".join(c if c.isalnum() else "_" for c in collection_name)

    vectordb = Chroma(
        collection_name=collection_name,
        persist_directory="data/vectordb",
        embedding_function=embeddings
    )

    # Re-ranking can be applied after this, but first we retrieve a higher number (k=8)
    retriever = vectordb.as_retriever(search_kwargs={"k": 8})

    return retriever

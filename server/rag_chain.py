from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

def build_rag():
    embeddings = OllamaEmbeddings(model="llama3.2:1b")

    vectordb = Chroma(
        persist_directory="data/vectordb",
        embedding_function=embeddings
    )

    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    return retriever

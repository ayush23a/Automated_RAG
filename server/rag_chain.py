from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from llm import get_ollama
from langchain_community.embeddings import OllamaEmbeddings

def build_rag():
    embeddings = OllamaEmbeddings(model="llama3.2:1b")
    vectordb = Chroma(
        persist_directory="data/vectordb",
        embedding_function=embeddings
    )

    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    qa = RetrievalQA.from_chain_type(
        llm=get_ollama(),
        retriever=retriever,
        return_source_documents=True
    )

    return qa

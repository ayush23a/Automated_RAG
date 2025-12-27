from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

def ingest_docs(path="data/docs"):
    loader = PyPDFLoader(path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model="llama3.2:1b")
    vectordb = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory="data/vectordb"
    )
    vectordb.persist()

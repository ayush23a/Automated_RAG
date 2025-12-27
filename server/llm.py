from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI

def get_ollama():
    return Ollama(model="llama3.2:1b")

def get_gemini():
    return ChatGoogleGenerativeAI(model="gemini-pro")

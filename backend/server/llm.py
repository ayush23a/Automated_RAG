import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

def get_ollama():
    return OllamaLLM(
        model="llama3.2:1b",
        temperature=0.2
    )

def get_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.4
    )

def get_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=api_key,
        temperature=0.3,
        top_p=0.9,
        max_tokens=2048
    )
    
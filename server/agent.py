from server.llm import get_gemini

def rag_agent(query, retriever):
    docs = retriever.invoke(query)

    if not docs:
        return {
            "answer": "No relevant information found in the documents.",
            "sources": []
        }

    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
You are a helpful assistant.
Answer the question using ONLY the context below.
If the answer is not present, say so clearly.

Context:
{context}

Question:
{query}
"""

    gemini = get_gemini()
    if gemini is None:
        return {
            "answer": "Gemini API key not configured.",
            "sources": []
        }

    response = gemini.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    return {
        "answer": answer,
        "sources": [
            doc.metadata.get("source", "")
            for doc in docs
        ]
    }

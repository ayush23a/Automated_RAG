def rag_agent(query, qa_chain):
    if "summarize" in query.lower():
        query = f"Summarize using evidence only: {query}"

    response = qa_chain(query)

    return {
        "answer": response["result"],
        "sources": [
            doc.metadata.get("source", "")
            for doc in response["source_documents"]
        ]
    }

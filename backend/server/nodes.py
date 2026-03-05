from typing import Dict, Literal, cast
from pydantic import BaseModel, Field
from server.state import RAGState
from server.llm import get_gemini, get_ollama, get_groq
from server.rag_chain import build_rag

class IntentClassification(BaseModel):
    intent: Literal["casual", "fact_check", "doc_query", "deep_research", "mixed"] = Field(
        description="Classify the user query into one of the following intents."
    )

def intent_classifier_node(state: RAGState) -> Dict:
    query = state["query"]
    
    def use_groq():
        llm = get_groq()
        # Ensure we have the fallback model available
        if not llm:
            return {"intent": "casual"}
            
        prompt = f"""Classify the following query into one of these categories:
- casual: simple conversation, greetings, general knowledge.
- fact_check: requires real-time factual checking (news, stats).
- doc_query: asking about an uploaded document.
- deep_research: asking for deep insights, analysis, or trends.
- mixed: both document and external trends.

Query: "{query}"

Output ONLY the category name.
"""
        try:
            response = llm.invoke(prompt)
            intent_text = response.content.strip().lower() if hasattr(response, "content") else str(response).strip().lower()
            
            for valid_intent in ["casual", "fact_check", "doc_query", "deep_research", "mixed"]:
                if valid_intent in intent_text:
                    return {"intent": valid_intent}
        except Exception:
            pass
        return {"intent": "casual"}

    llm = get_gemini()
    if llm is None:
        return use_groq()

    structured_llm = llm.with_structured_output(IntentClassification)
    
    prompt = f"""Analyze the following query and determine its intent based on these rules:
1. 'casual': Normal conversation, greetings, generic knowledge. No documents or web searches needed.
2. 'doc_query': Explicitly mentions "in the document", "from my upload", or asks about specific arbitrary things that are likely in their uploaded file.
3. 'deep_research': Asks for industry perspectives, deep explanations, latest trends, or extensive analysis.
4. 'fact_check': Time-sensitive, news-related, statistical, or requires current real-world data.
5. 'mixed': Needs both the uploaded document context AND external insights.

Query: "{query}"
"""
    
    try:
        result = cast(IntentClassification, structured_llm.invoke(prompt))
        return {"intent": result.intent}
    except Exception as e:
        print(f"Gemini Intent Error: {e}")
        return use_groq()

def strategy_router(state: RAGState) -> Literal["doc_rag_node", "web_search_node", "final_synthesizer_node"]:
    intent = state.get("intent", "casual")
    
    if intent in ["doc_query", "mixed", "deep_research"]:
        return "doc_rag_node"
    elif intent == "fact_check":
        return "web_search_node"
    else:
        return "final_synthesizer_node"

def doc_rag_node(state: RAGState) -> Dict:
    query = state["query"]
    session_id = state.get("session_id", "default")
    
    retriever = build_rag(session_id)
    
    # Simple query for now, could be enhanced with query rewriting before retrieval
    docs = retriever.invoke(query)
    
    # Keep top 5 after potential reranking
    docs = docs[:5]
    
    sources = state.get("sources", [])
    if sources is None:
        sources = []
        
    for d in docs:
        src = d.metadata.get("source", "Unknown Document")
        page = d.metadata.get("page", "")
        if page:
            src += f" (Page {page})"
        if src not in sources:
            sources.append(src)
            
    return {"documents": docs, "sources": sources}

def web_search_node(state: RAGState) -> Dict:
    query = state["query"]
    
    # Using SerpAPI for web search
    try:
        from langchain_community.utilities import SerpAPIWrapper
        search = SerpAPIWrapper()
        res = search.results(query)
        results = res.get("organic_results", [])[:5]
    except Exception as e:
        print(f"SerpAPI Error: {e}")
        results = []
    
    web_results = state.get("web_results", [])
    if web_results is None:
        web_results = []
        
    sources = state.get("sources", [])
    if sources is None:
        sources = []
    
    if results:
        for r in results:
            web_results.append({
                "title": r.get("title", ""),
                "body": r.get("snippet", ""),
                "href": r.get("link", "")
            })
            if r.get("link", "") not in sources:
                sources.append(r.get("link", ""))
            
    return {"web_results": web_results, "sources": sources}

def merge_node(state: RAGState) -> Dict:
    # This node can be used to route from doc_rag_node to web_search_node if intent is mixed or deep_research
    # For simplicity, we can do that routing inside the graph edges.
    pass

def final_synthesizer_node(state: RAGState) -> Dict:
    query = state["query"]
    docs = state.get("documents", [])
    web_results = state.get("web_results", [])
    
    context_parts = []
    
    if docs:
        doc_texts = []
        for d in docs:
            src = d.metadata.get("source", "Unknown")
            page = d.metadata.get("page", "")
            doc_texts.append(f"Source: {src} (Page {page})\nContent: {d.page_content}")
        context_parts.append("--- DOCUMENT EVIDENCE ---\n" + "\n\n".join(doc_texts))
        
    if web_results:
        web_texts = []
        for w in web_results:
            web_texts.append(f"Source: {w['href']}\nTitle: {w['title']}\nContent: {w['body']}")
        context_parts.append("--- WEB EVIDENCE ---\n" + "\n\n".join(web_texts))
        
    if context_parts:
        context_str = "\n\n".join(context_parts)
        prompt = f"""You are a helpful, expert AI assistant.
Answer the user's query using ONLY the evidence provided below.
If you use information from the evidence, provide a clear citation in your answer (e.g. "According to [Document Name, Page X]...").
Do not hallucinate URLs, facts, or page numbers. Make sure to separate insights from documents vs. web sources if both are present.
If the evidence does not contain the answer, explicitly state that you don't have enough information from the provided sources.

{context_str}

User Query: {query}
"""
    else:
        prompt = f"""You are a helpful AI assistant.
Respond to the following user query casually and naturally. Do not mention searching for documents or the web unless asked.

User Query: {query}
"""
    
    llm = get_gemini()
    response = None
    if llm:
        try:
            response = llm.invoke(prompt)
        except Exception as e:
            print(f"Gemini Synthesizer Error: {e}")
            llm = None  # Fallback to groq
            
    if not llm:
        llm = get_groq()
        if llm:
            try:
                response = llm.invoke(prompt)
            except Exception as e:
                print(f"Groq Synthesizer Error: {e}")
                response = "Error generating response from fallback model."
        else:
            response = "Error generating response and fallback model is missing API key."
            
    if response and hasattr(response, "content"):
        if isinstance(response.content, list):
            text_blocks = []
            for block in response.content:
                if isinstance(block, dict) and "text" in block:
                    text_blocks.append(block["text"])
                elif isinstance(block, str):
                    text_blocks.append(block)
                else:
                    text_blocks.append(str(block))
            answer = " ".join(text_blocks)
        else:
            answer = str(response.content)
    else:
        answer = str(response)
    
    return {"final_answer": answer}

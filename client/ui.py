import streamlit as st
import requests
import uuid

# Initialize session state for session ID and chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Project Kriyamān", page_icon="📄")

st.title("📄 Kriyamān AI")
st.text(f"Session ID: {st.session_state.session_id}")

# Health check
try:
    requests.get("http://localhost:8000/docs", timeout=10)
except requests.exceptions.ConnectionError:
    st.error("Backend is not running on port 8000")
    st.stop()

st.sidebar.header("Session Management")
if st.sidebar.button("🗑️ Clear Session & Start Fresh", use_container_width=True):
    # Call backend to delete session data
    try:
        requests.delete(f"http://localhost:8000/session/{st.session_state.session_id}")
    except:
        pass
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.rerun()

st.sidebar.header("Upload Documents")

# Document upload forms
with st.sidebar.form("upload_form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Upload a PDF to current session", type=["pdf"])
    submitted = st.form_submit_button("Upload")

    if submitted and uploaded_file is not None:
        with st.spinner("Uploading and indexing..."):
            response = requests.post(
                "http://localhost:8000/upload",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                data={"session_id": st.session_state.session_id}
            )

        if response.status_code == 200:
            res_data = response.json()
            st.success(f"Uploaded! {res_data.get('docs_ingested', 0)} chunks indexed.")
        else:
            st.error("Failed to upload document.")

st.markdown("---")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander("View Sources"):
                for src in msg["sources"]:
                    st.write(f"- {src}")
        if msg["role"] == "assistant" and "intent" in msg:
            st.caption(f"Intent detected: {msg['intent']}")

# Chat input
if query := st.chat_input("Ask a question..."):
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    with st.chat_message("user"):
        st.write(query)
        
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    "http://localhost:8000/query",
                    json={"query": query, "session_id": st.session_state.session_id},
                    timeout=120
                )
                
                if resp.status_code == 200:
                    res = resp.json()
                    answer = res.get("answer", "No answer returned.")
                    sources = res.get("sources", [])
                    intent = res.get("intent", "unknown")
                    
                    st.write(answer)
                    if sources:
                        with st.expander("View Sources"):
                            for src in sources:
                                st.write(f"- {src}")
                    st.caption(f"Intent detected: {intent}")
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources,
                        "intent": intent
                    })
                else:
                    st.error(f"Backend error: {resp.text}")
            except Exception as e:
                st.error(f"Failed to query backend: {e}")
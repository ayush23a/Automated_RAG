import streamlit as st
import requests
import uuid
import os

# Backend API URL — configurable for deployment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize session state for session ID and chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Project Kriyamān", page_icon="📄")

st.title("📄 Kriyamān AI")

# Check for authentication token in query params
if "token" in st.query_params:
    token = st.query_params["token"]
    try:
        # Validate the token using Google's tokeninfo endpoint
        resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}", timeout=5)
        if resp.status_code == 200:
            idinfo = resp.json()
            email = idinfo.get("email")
            st.session_state.session_id = str(uuid.uuid4()) + "_" + email.split("@")[0]
            st.session_state.user_email = email
            # Clean up URL parameter to avoid resubmitting
            st.query_params.clear()
        else:
            st.error("Invalid token.")
    except Exception as e:
        st.error(f"Error parsing token: {e}")

if not st.session_state.session_id:
    st.info("Please login to continue.")
    # Show login button
    st.markdown(f'<a href="{API_URL}/login" target="_self"><button style="background-color: #4285F4; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">Login with Google</button></a>', unsafe_allow_html=True)
    st.stop()

# Top bar with profile icon in the right corner
top_left, top_right = st.columns([9, 1])
with top_right:
    with st.popover("👤"):
        st.markdown(f"**{st.session_state.get('user_email', 'User')}**")
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all auth state
            try:
                requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
            except:
                pass
            st.session_state.session_id = None
            st.session_state.chat_history = []
            if "user_email" in st.session_state:
                del st.session_state.user_email
            st.rerun()

# Health check
try:
    requests.get(f"{API_URL}/docs", timeout=10)
except requests.exceptions.ConnectionError:
    st.error("Backend is not running. Check API_URL configuration.")
    st.stop()

st.sidebar.header("Session Management")
if st.sidebar.button("🗑️ Clear Session & Start Fresh", use_container_width=True):
    # Call backend to delete session data
    try:
        requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
    except:
        pass
    # Keep user logged in but reset session data
    email = st.session_state.get("user_email", "")
    st.session_state.session_id = str(uuid.uuid4()) + "_" + email.split("@")[0] if email else str(uuid.uuid4())
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
                f"{API_URL}/upload",
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
                    f"{API_URL}/query",
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
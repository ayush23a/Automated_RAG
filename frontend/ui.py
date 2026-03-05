import streamlit as st
import requests
import uuid
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# extract current date 
current_date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A, %d %B %Y")
current_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%I:%M %p")

# Backend API URL — configurable for deployment
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize session state for session ID and chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Project Kriyamān", page_icon="📄")

st.title("📄 Kriyamān AI")
if not st.session_state.session_id:
    st.info("You can explore the interface. Login is required to send messages.")

# Check for authentication token in query params
if "token" in st.query_params and not st.session_state.session_id:
    token = st.query_params.get("token")

    if isinstance(token, list):
        token = token[0]
    try:
        # Validate the token using Google's tokeninfo endpoint
        resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}", timeout=5)
        if resp.status_code == 200:
            idinfo = resp.json()

            email = idinfo.get("email")
            name = idinfo.get("name")

            st.session_state.session_id = str(uuid.uuid4()) + "_" + email.split("@")[0]
            st.session_state.user_email = email
            st.session_state.user_name = name
            # Clean up URL parameter to avoid resubmitting
            st.query_params.clear()
            st.rerun()

        else:
            st.error("Invalid token.")
    except Exception as e:
        st.error(f"Error parsing token: {e}")


# Health check
try:
    requests.get(f"{API_URL}/health", timeout=10)
except requests.exceptions.RequestException:
    st.error("Backend is not running. Check API_URL configuration.")
    st.stop()

if st.session_state.session_id:
    st.sidebar.header(f"{st.session_state.user_name}")
    st.sidebar.caption(f"{current_date}")
    st.sidebar.caption(f"{current_time}")
else:
    st.sidebar.header("Guest")
    st.sidebar.caption(f"{current_date}")
    st.sidebar.caption(f"{current_time} IST ")

# LOGIN BUTTON (only if not logged in)
if not st.session_state.session_id:
    st.sidebar.markdown(
        f'<a href="{API_URL}/login" target="_self">'
        '<button style="background-color:#4285F4;color:white;padding:10px 20px;border:none;border-radius:4px;width:100%;">'
        'Login with Google</button></a>',
        unsafe_allow_html=True
    )

st.sidebar.divider()

st.sidebar.header("Session Management")

if st.session_state.session_id:
    if st.sidebar.button("🗑️ Clear Session & Start Fresh", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
        except:
            pass

        email = st.session_state.get("user_email", "")
        st.session_state.session_id = str(uuid.uuid4()) + "_" + email.split("@")[0]
        st.session_state.chat_history = []
        st.rerun()

# Document upload forms
if st.session_state.session_id:
    st.sidebar.header("Upload Documents")

    with st.sidebar.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload a PDF to current session", type=["pdf"])
        submitted = st.form_submit_button("Upload")

        if submitted:

            if uploaded_file is None:
                st.warning("Please select a PDF file.")
            else:
                with st.spinner("Uploading and indexing..."):

                    try:
                        response = requests.post(
                            f"{API_URL}/upload",
                            files={
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    "application/pdf",
                                )
                            },
                            data={"session_id": st.session_state.session_id},
                            timeout=120,
                        )

                        if response.status_code == 200:
                            res_data = response.json()
                            st.success(
                                f"Uploaded! {res_data.get('docs_ingested', 0)} chunks indexed."
                            )
                        else:
                            st.error("Failed to upload document.")

                    except Exception as e:
                        st.error(f"Upload failed: {e}")

    st.sidebar.divider()

    # Profile Section
    with st.sidebar.popover("👤 Profile"):

        st.markdown(f"**Name:** {st.session_state.get('user_name', 'Unknown')}")
        st.markdown(f"**Email:** {st.session_state.get('user_email','Unknown')}")
        st.markdown(f"**Session ID:** `{st.session_state.session_id}`")

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):

            try:
                requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
            except:
                pass

            # clear session safely
            for key in ["session_id", "chat_history", "user_email", "user_name"]:
                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()

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
query = st.chat_input("How would you like to proceed today?")

if query:

    # If user not logged in → redirect to login
    if not st.session_state.session_id:
        st.warning("Please login to start chatting.")
        st.markdown(
            f'<a href="{API_URL}/login" target="_self">'
            '<button style="background-color:#4285F4;color:white;padding:10px 20px;border:none;border-radius:4px;">'
            'Login with Google</button></a>',
            unsafe_allow_html=True
        )
        st.stop()
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
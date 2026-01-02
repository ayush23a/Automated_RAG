import streamlit as st
import requests

st.title("📄 RAG Agent MVP")

# Health check
try:
    requests.get("http://localhost:8000/docs", timeout=5)
except requests.exceptions.ConnectionError:
    st.error("Backend is not running on port 8000")
    st.stop()

st.sidebar.header("Upload Documents")

uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file is not None:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": uploaded_file}
    )

    if response.status_code == 200:
        st.sidebar.success("Document uploaded & indexed!")
    else:
        st.sidebar.error(response.text)

query = st.text_input("Ask a question")

if st.button("Ask"):
    resp = requests.post(
        "http://localhost:8000/query",
        json={"query": query},
        timeout=60
    )

    if resp.status_code != 200:
        st.error("Backend error")
        st.text(resp.text)
        st.stop()

    try:
        res = resp.json()
    except Exception:
        st.error("Backend did not return JSON")
        st.text(resp.text)
        st.stop()

    st.markdown("### Answer")
    st.write(res.get("answer", "No answer returned"))

    st.markdown("### Sources")
    for src in res.get("sources", []):
        st.write(src)
    st.write("Raw response:", resp.text)
import streamlit as st
import requests

st.title("RAG Agent MVP")

query = st.text_input("Ask a question")

if st.button("Ask"):
    res = requests.post(
        "http://localhost:8000/query",
        params={"query": query}
    ).json()

    st.markdown("### Answer")
    st.write(res["answer"])

    st.markdown("### Sources")
    for src in res["sources"]:
        st.write(src)

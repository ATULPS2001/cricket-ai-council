"""Streamlit UI for Cricket AI Council."""
import streamlit as st
import requests
import os

# ─── Config ───────────────────────────────────────────────────────────────────

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Cricket AI Council",
    page_icon="🏏",
    layout="wide",
)

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("🏏 Cricket AI Council")
st.markdown("**Ask strategic questions. Get data-driven answers**.")

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    
    role = st.selectbox(
        "Select Agent Role",
        ["tactical", "data", "evaluator"],
        format_func=lambda x: x.title(),
    )
    
    st.info("""
    **Tactical Agent**: Game plans and tactics  
    **Data Agent**: Statistics and trends  
    **Evaluator Agent**: Risk assessment and strategy
    """)
    
    st.divider()
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ─── Chat History ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "citations" in msg and msg["citations"]:
            with st.expander("📚 Citations"):
                for cite in msg["citations"]:
                    st.write(f"- {cite}")

# ─── Chat Input ───────────────────────────────────────────────────────────────

if prompt := st.chat_input("Ask the council (e.g., 'Playing CSK at Chepauk, what's the plan?')"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": prompt, "role": role},
                    timeout=30,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.write(data["response"])
                    
                    if data.get("citations"):
                        with st.expander("📚 Citations"):
                            for cite in data["citations"]:
                                st.write(f"- {cite}")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["response"],
                        "citations": data.get("citations", []),
                    })
                else:
                    st.error(f"API error: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Is the backend running?")
                st.info(f"Expected API URL: {API_URL}")
            except Exception as e:
                st.error(f"Error: {e}")

# ─── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.caption("Built with LangGraph + Chroma + FastAPI + Streamlit")

"""Streamlit UI for Cricket AI Council."""
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import CricketWorkflow
from config import validate_config

st.set_page_config(
    page_title="Cricket AI Council",
    page_icon="🏏",
    layout="wide"
)

if not validate_config():
    st.error("⚠️ GOOGLE_API_KEY not set. Set it via: `export GOOGLE_API_KEY='your-key'`")
    st.stop()

st.title("🏏 Cricket AI Council")
st.markdown("""
**Multi-agent AI system for cricket analytics.**
Select a role and ask your question!
""")

st.sidebar.header("Select Agent Role")
role = st.sidebar.radio(
    "Choose your advisor:",
    ["tactical", "data", "evaluator"],
    format_func=lambda x: {
        "tactical": "🎯 Tactical (Head Coach)",
        "data": "📊 Data (Analyst)",
        "evaluator": "🧠 Evaluator (Chief Strategist)"
    }[x]
)

role_descriptions = {
    "tactical": """
    **Head Coach** - Provides actionable game plans and tactical advice.
    - Powerplay strategy
    - Middle overs approach
    - Death over execution
    - Player matchups
    """,
    "data": """
    **Data Analyst** - Presents numbers, trends, and statistical insights.
    - Win percentages
    - Run rates
    - Historical patterns
    - Comparisons
    """,
    "evaluator": """
    **Chief Strategist** - Assesses options, weighs risks, recommends actions.
    - Toss decisions
    - Venue advantages
    - Opponent tendencies
    - Confidence levels
    """
}

st.sidebar.info(role_descriptions[role])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask the council... (e.g., 'Playing CSK at Chepauk, what's our strategy?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                workflow = CricketWorkflow()
                response = workflow.run(prompt, role)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {str(e)}"})

st.markdown("---")
st.caption("Built with LangGraph + Gemini + FastAPI + Streamlit")

"""Streamlit UI for Cricket AI Council."""
import streamlit as st
import sys
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import API_HOST, API_PORT

st.set_page_config(
    page_title="Cricket AI Council",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Cricket AI Council")
st.markdown("""
**Multi-agent AI system for cricket analytics.**
Select an agent and ask your question!
""")

st.sidebar.header("Select Agent")
role = st.sidebar.radio(
    "Choose your advisor:",
    ["stats", "form", "formulator"],
    format_func=lambda x: {
        "stats": "📊 Stats Agent (Career & Historical Stats)",
        "form": "📈 Form Agent (Recent Form & Momentum)",
        "formulator": "🧠 Formulator (Fuses Stats + Form)"
    }[x]
)

role_descriptions = {
    "stats": """
    **Stats Agent** - Analyzes career statistics and historical records.
    - Career batting averages
    - Bowling economy rates
    - Head-to-head records
    - Venue-based win percentages
    """,
    "form": """
    **Form Agent** - Evaluates recent form and momentum.
    - Last 5 matches: win%, batting run rate, death-over bowling economy
    - Recent H2H record (last 5 meetings)
    - Form differential between two teams
    """,
    "formulator": """
    **Formulator Agent** - Fuses predictions from Stats and Form agents.
    - Weighted ensemble: 80% Stats + 20% Form
    - Balances long-term stats with recent momentum
    - More robust than either agent alone
    """
}

st.sidebar.info(role_descriptions[role])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask the council... (e.g., 'CSK vs MI at Wankhede, who wins?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call FastAPI backend
                response = httpx.post(
                    f"http://{API_HOST}:{API_PORT}/query",
                    json={"query": prompt, "role": role},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                # Format response
                answer = f"**Prediction:** {result.get('prediction', 'N/A')}\n\n"
                answer += f"**Confidence:** {result.get('confidence', 0) * 100:.1f}%\n\n"
                answer += f"**Reasoning:** {result.get('reasoning', 'N/A')}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except httpx.HTTPError as e:
                error_msg = f"⚠️ API Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown("---")
st.caption("Built with Stats/Form/Formulator agents + FastAPI + Streamlit")

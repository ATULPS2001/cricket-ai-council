"""Streamlit UI for Cricket AI Council."""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.stats_agent import StatsAgent
from agents.form_agent import FormAgent
from agents.formulator_agent import FormulatorAgent
from config import DATA_DIR

st.set_page_config(
    page_title="Cricket AI Council",
    page_icon="🏏",
    layout="wide"
)

# Load data once at startup
@st.cache_resource
def load_data():
    matches_df = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries_df = pd.read_csv(DATA_DIR / "deliveries.csv")
    return matches_df, deliveries_df

matches_df, deliveries_df = load_data()

# Initialize agents
stats_agent = StatsAgent(matches_df, deliveries_df)
form_agent = FormAgent(matches_df, deliveries_df)
formulator_agent = FormulatorAgent(matches_df, deliveries_df)

st.title("🏏 Cricket AI Council")
st.markdown("""
**Multi-agent AI system for cricket match predictions and analytics.**
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
                # Build structured question for agents
                question = {
                    "type": "toss_bat_gamble" if "toss" in prompt.lower() or "bat" in prompt.lower() else "form_check",
                    "teams": [],
                    "venue": None,
                }
                
                # Select agent
                if role == "stats":
                    verdict = stats_agent.analyze(question)
                elif role == "form":
                    verdict = form_agent.analyze(question)
                elif role == "formulator":
                    verdict = formulator_agent.analyze(question)
                else:
                    raise ValueError(f"Unknown role: {role}")
                
                # Format response
                answer = f"**Prediction:** {verdict.prediction}\n\n"
                answer += f"**Confidence:** {verdict.confidence * 100:.1f}%\n\n"
                answer += f"**Reasoning:** {verdict.reasoning}"
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown("---")
st.caption("Built with Stats/Form/Formulator agents + Streamlit")

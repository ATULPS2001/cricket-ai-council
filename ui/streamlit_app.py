"""Streamlit UI for Cricket AI Council."""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.stats_agent import StatsAgent
from agents.form_agent import FormAgent
from agents.formulator_agent import FormulatorAgent
from agents.viz_agent import VizAgent
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
viz_agent = VizAgent(matches_df, deliveries_df)

st.title("🏏 Cricket AI Council")
st.markdown("**Multi-agent AI system for cricket match predictions and analytics.**")

# Sidebar
st.sidebar.header("🎯 Select Agent")
role = st.sidebar.radio(
    "Choose your advisor:",
    ["stats", "form", "formulator", "viz"],
    format_func=lambda x: {
        "stats": "📊 Stats Agent",
        "form": "📈 Form Agent",
        "formulator": "🧠 Formulator",
        "viz": "📉 Viz Agent"
    }[x]
)

role_descriptions = {
    "stats": "Career stats, H2H records, venue win%",
    "form": "Recent form, last 5 matches, momentum",
    "formulator": "Fuses Stats + Form (80/20 weights)",
    "viz": "Charts: win%, H2H, form trends"
}

st.sidebar.info(f"**What it does:** {role_descriptions[role]}")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Helper to extract teams from query
def extract_teams(prompt: str) -> tuple:
    """Extract two team names from user query."""
    patterns = [
        r'([A-Z][a-zA-Z\s]+?)\s+(?:vs|&|against)\s+([A-Z][a-zA-Z\s]+)',
        r'([A-Z][a-zA-Z\s]+?)\s+([A-Z][a-zA-Z\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    
    return None, None

# Chat input
if prompt := st.chat_input("Ask... (e.g., 'CSK vs MI at Chepauk, who wins?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Extract teams and venue from prompt
                team1, team2 = extract_teams(prompt)
                venue_match = re.search(r'at\s+([A-Za-z\s]+?)(?:,|\.|$)', prompt, re.IGNORECASE)
                venue = venue_match.group(1).strip() if venue_match else None
                
                # Build question
                question = {
                    "type": "toss_bat_gamble",
                    "teams": [team1, team2] if team1 and team2 else [],
                    "venue": venue,
                }
                
                # Get prediction
                if role == "stats":
                    verdict = stats_agent.analyze(question)
                    answer = f"**📊 Prediction:** {verdict.prediction}\n\n"
                    answer += f"**Confidence:** {verdict.confidence * 100:.1f}%\n\n"
                    answer += f"**Reasoning:** {verdict.reasoning}"
                    
                elif role == "form":
                    verdict = form_agent.analyze(question)
                    answer = f"**📈 Prediction:** {verdict.prediction}\n\n"
                    answer += f"**Confidence:** {verdict.confidence * 100:.1f}%\n\n"
                    answer += f"**Reasoning:** {verdict.reasoning}"
                    
                elif role == "formulator":
                    verdict = formulator_agent.analyze(question)
                    answer = f"**🧠 Prediction:** {verdict.prediction}\n\n"
                    answer += f"**Confidence:** {verdict.confidence * 100:.1f}%\n\n"
                    answer += f"**Reasoning:** {verdict.reasoning}"
                    
                elif role == "viz":
                    if not team1 or not team2:
                        answer = "⚠️ Please specify two teams (e.g., 'CSK vs MI at Chepauk')"
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        st.stop()
                    
                    # Show charts
                    st.markdown(f"**📊 Visual Analysis: {team1} vs {team2}**")
                    
                    # Venue comparison
                    st.subheader("📍 Venue Win%")
                    venue_chart = viz_agent.create_venue_comparison_chart(team1, team2, venue)
                    st.altair_chart(venue_chart, use_container_width=True)
                    
                    # H2H
                    st.subheader("⚔️ Head-to-Head")
                    h2h_chart = viz_agent.create_h2h_chart(team1, team2)
                    st.altair_chart(h2h_chart, use_container_width=True)
                    
                    # Form charts
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"📈 {team1} Form")
                        form1_chart = viz_agent.create_form_chart(team1)
                        st.altair_chart(form1_chart, use_container_width=True)
                    
                    with col2:
                        st.subheader(f"📈 {team2} Form")
                        form2_chart = viz_agent.create_form_chart(team2)
                        st.altair_chart(form2_chart, use_container_width=True)
                    
                    answer = f"Charts generated for **{team1} vs {team2}** at **{venue or 'all venues'}**"
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.stop()
                else:
                    raise ValueError(f"Unknown role: {role}")
                
                # Show prediction and charts
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Show supporting charts for predictions
                if team1 and team2 and role in ["stats", "form", "formulator"]:
                    st.markdown("---")
                    st.subheader("📊 Supporting Data")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        venue_chart = viz_agent.create_venue_comparison_chart(team1, team2, venue)
                        st.altair_chart(venue_chart, use_container_width=True)
                    
                    with col2:
                        h2h_chart = viz_agent.create_h2h_chart(team1, team2)
                        st.altair_chart(h2h_chart, use_container_width=True)
                    
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown("---")
st.caption("Built with Stats/Form/Formulator/Viz agents + Streamlit")

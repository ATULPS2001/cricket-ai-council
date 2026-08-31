"""LangGraph workflow for Cricket AI Council."""
from __future__ import annotations

import os
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from mcp_server import CricketMCPClient
from rag.retrieve import retrieve_docs

# ─── State ────────────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    """Workflow state."""
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    role: str  # "tactical", "data", "evaluator"
    retrieved_stats: dict
    retrieved_docs: list[str]
    citations: list[str]
    final_response: str


# ─── Nodes ────────────────────────────────────────────────────────────────────


def research_node(state: AgentState) -> dict:
    """Query MCP tools for relevant stats."""
    mcp = CricketMCPClient()
    query = state["query"]
    role = state["role"]

    stats = {
        "team_stats": None,
        "venue_stats": None,
        "h2h": None,
    }

    # Extract team/venue from query (simple keyword parsing for MVP)
    # In production, use LLM for entity extraction
    teams = ["Mumbai Indians", "Chennai Super Kings", "Kolkata Knight Riders", 
             "Royal Challengers Bangalore", "Sunrisers Hyderabad", "Delhi Capitals", 
             "Rajasthan Royals", "Punjab Kings", "Gujarat Titans", "Lucknow Super Giants"]
    
    detected_teams = [t for t in teams if t.lower() in query.lower()]
    venue_keywords = ["Chepauk", "Wankhede", "Eden Gardens", "Chinnaswamy", "Jaipur"]
    detected_venue = next((v for v in venue_keywords if v.lower() in query.lower()), None)

    if len(detected_teams) >= 1:
        stats["team_stats"] = mcp.get_team_stats(detected_teams[0], phase="death")
    
    if len(detected_teams) >= 2:
        stats["h2h"] = mcp.get_h2h(detected_teams[0], detected_teams[1])
    
    if detected_venue and len(detected_teams) >= 1:
        stats["venue_stats"] = mcp.get_venue_record(detected_teams[0], detected_venue)

    return {"retrieved_stats": stats}


def strategy_node(state: AgentState) -> dict:
    """Generate strategic response using stats + RAG docs."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)
    
    stats = state["retrieved_stats"]
    docs = state.get("retrieved_docs", [])
    role = state["role"]
    query = state["query"]

    # Build prompt with role context
    role_prompts = {
        "tactical": "You are the Head Coach. Provide actionable game plans and tactical advice.",
        "data": "You are the Data Analyst. Provide statistics, trends, and historical comparisons.",
        "evaluator": "You are the Chief Strategist. Assess risks, provide confidence scores, and suggest alternatives.",
    }

    system_prompt = f"""{role_prompts.get(role, role_prompts['tactical'])}

Use the following data to inform your response:

STATS:
{stats}

RETRIEVED DOCUMENTS:
{chr(10).join(docs) if docs else 'No documents retrieved.'}

Be concise, specific, and cite sources where applicable.
"""

    messages = [
        HumanMessage(content=system_prompt),
        HumanMessage(content=query),
    ]

    response = llm.invoke(messages)
    return {"messages": [response], "final_response": response.content}


def critic_node(state: AgentState) -> dict:
    """Validate response, add citations, flag hallucinations."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)
    
    response = state["final_response"]
    stats = state["retrieved_stats"]
    docs = state.get("retrieved_docs", [])

    # Critic prompt
    critic_prompt = f"""Review this response for accuracy and citations:

RESPONSE:
{response}

SOURCE DATA:
{stats}

RETRIEVED DOCS:
{chr(10).join(docs) if docs else 'None'}

Tasks:
1. Flag any claims not supported by the data (potential hallucinations)
2. Add citations [source: doc_name] where applicable
3. If confidence is low (<70%), add a disclaimer

Output the revised response with citations.
"""

    messages = [HumanMessage(content=critic_prompt)]
    revised = llm.invoke(messages)

    # Extract citations (simple regex for MVP)
    import re
    citations = re.findall(r'\[source: ([^\]]+)\]', revised.content)

    return {
        "messages": [AIMessage(content=revised.content)],
        "final_response": revised.content,
        "citations": citations,
    }


# ─── Build Graph ──────────────────────────────────────────────────────────────


def build_workflow() -> StateGraph:
    """Construct the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("research", research_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("critic", critic_node)

    # Define edges
    workflow.add_edge(START, "research")
    workflow.add_edge("research", "strategy")
    workflow.add_edge("strategy", "critic")
    workflow.add_edge("critic", END)

    # Add memory for persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# ─── Run ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # Test workflow
    app = build_workflow()
    
    test_state = {
        "messages": [],
        "query": "We're playing CSK at Chepauk, what's the plan?",
        "role": "tactical",
        "retrieved_stats": {},
        "retrieved_docs": [],
        "citations": [],
        "final_response": "",
    }
    
    result = app.invoke(test_state)
    print("Final Response:")
    print(result["final_response"])
    print("\nCitations:", result["citations"])

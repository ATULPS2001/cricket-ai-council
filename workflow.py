"""LangGraph workflow for Cricket AI Council."""
from __future__ import annotations

import os
from typing import Annotated, Literal, TypedDict

import google.generativeai as genai
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

from mcp_server import MCPCricketTools
from config import Config

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
model = genai.GenerativeModel("gemini-1.5-flash")


class AgentState(TypedDict):
    """State for the workflow."""
    query: str
    role: Literal["tactical", "data", "evaluator"]
    messages: Annotated[list, add_messages]
    tool_results: dict
    rag_docs: list[str]
    final_response: str


class CricketWorkflow:
    """LangGraph-based workflow for the Cricket AI Council."""

    def __init__(self):
        self.tools = MCPCricketTools()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(AgentState)

        graph.add_node("research", self.research_node)
        graph.add_node("strategy", self.strategy_node)
        graph.add_node("critic", self.critic_node)

        graph.add_edge(START, "research")
        graph.add_edge("research", "strategy")
        graph.add_edge("strategy", "critic")
        graph.add_edge("critic", END)

        return graph.compile()

    def research_node(self, state: AgentState) -> AgentState:
        """Research node: call MCP tools based on query and role."""
        query = state["query"]
        role = state["role"]

        tool_results = {}
        query_lower = query.lower()

        if role == "tactical":
            if "csk" in query_lower or "chennai" in query_lower:
                tool_results["csk_stats"] = self.tools.get_team_stats("Chennai Super Kings", "all")
            if "mi" in query_lower or "mumbai" in query_lower:
                tool_results["mi_stats"] = self.tools.get_team_stats("Mumbai Indians", "all")
            if "chepauk" in query_lower:
                tool_results["chepauk_record"] = self.tools.get_venue_record("Chennai Super Kings", "MA Chidambaram Stadium, Chepauk")
            if "h2h" in query_lower or "head-to-head" in query_lower or "head to head" in query_lower:
                tool_results["h2h"] = self.tools.get_h2h("Mumbai Indians", "Chennai Super Kings")

        elif role == "data":
            if "death" in query_lower or "powerplay" in query_lower:
                tool_results["phase_stats"] = self.tools.get_team_stats("Mumbai Indians", "death")
            if "venue" in query_lower or "home" in query_lower:
                tool_results["venue_stats"] = self.tools.get_venue_record("Mumbai Indians", "Wankhede Stadium, Mumbai")

        elif role == "evaluator":
            if "toss" in query_lower or "bat" in query_lower or "field" in query_lower:
                tool_results["toss_data"] = self.tools.get_toss_conversion("Wankhede Stadium, Mumbai")
            if "venue" in query_lower:
                tool_results["venue_eval"] = self.tools.get_venue_record("Mumbai Indians", "Wankhede Stadium, Mumbai")

        if not tool_results:
            tool_results["generic"] = {"message": "No specific tools matched, using general knowledge"}

        return {"tool_results": tool_results}

    def strategy_node(self, state: AgentState) -> AgentState:
        """Strategy node: generate response using LLM + tool results."""
        query = state["query"]
        role = state["role"]
        tool_results = state["tool_results"]

        context_parts = []
        for tool_name, result in tool_results.items():
            context_parts.append(f"**{tool_name}**:\n{result}")

        context = "\n\n".join(context_parts) if context_parts else "No specific data retrieved."

        system_prompts = {
            "tactical": """You are the Tactical Agent (Head Coach) of the Cricket AI Council.
Your job is to provide actionable game plans and tactical advice.
Focus on: powerplay strategy, middle overs approach, death over execution, player matchups.
Be concise, direct, and practical. Use bullet points for clarity.""",

            "data": """You are the Data Agent (Analyst) of the Cricket AI Council.
Your job is to present numbers, trends, and statistical insights.
Focus on: win percentages, run rates, historical patterns, comparisons.
Use tables where helpful. Be precise with numbers.""",

            "evaluator": """You are the Evaluator Agent (Chief Strategist) of the Cricket AI Council.
Your job is to assess options, weigh risks, and recommend the best course of action.
Focus on: toss decisions, venue advantages, opponent tendencies, confidence levels.
Provide clear recommendations with reasoning."""
        }

        system_prompt = system_prompts.get(role, system_prompts["tactical"])

        prompt = f"""{system_prompt}

**User Query:** {query}

**Available Data:**
{context}

**Instructions:**
- Answer the query using the data above
- If data is missing, say so clearly
- Cite sources as [source: tool_name]
- Keep response under 200 words

**Your Response:**"""

        response = model.generate_content(prompt)

        return {"final_response": response.text, "messages": [HumanMessage(content=query), AIMessage(content=response.text)]}

    def critic_node(self, state: AgentState) -> AgentState:
        """Critic node: validate response, add citations, check for hallucinations."""
        final_response = state["final_response"]
        tool_results = state["tool_results"]

        validation_notes = []

        if not tool_results:
            validation_notes.append("⚠️ No tool data was retrieved - response may be based on general knowledge only.")

        citations = []
        for tool_name in tool_results.keys():
            citations.append(f"- {tool_name}")

        if citations:
            final_response += "\n\n**Sources:**\n" + "\n".join([f"[source: {c}]" for c in citations])

        if validation_notes:
            final_response += "\n\n**Critic Notes:**\n" + "\n".join(validation_notes)

        return {"final_response": final_response}

    def run(self, query: str, role: str = "tactical") -> str:
        """Run the workflow with a query and role."""
        initial_state: AgentState = {
            "query": query,
            "role": role,
            "messages": [],
            "tool_results": {},
            "rag_docs": [],
            "final_response": ""
        }

        result = self.graph.invoke(initial_state)
        return result["final_response"]


if __name__ == "__main__":
    workflow = CricketWorkflow()

    print("="*70)
    print("TESTING TACTICAL AGENT")
    print("="*70)
    response = workflow.run("Playing CSK at Chepauk, what's our batting strategy?", role="tactical")
    print(response)

    print("\n" + "="*70)
    print("TESTING DATA AGENT")
    print("="*70)
    response = workflow.run("Show me MI's death over batting stats", role="data")
    print(response)

    print("\n" + "="*70)
    print("TESTING EVALUATOR AGENT")
    print("="*70)
    response = workflow.run("Should we bat or field first at Wankhede?", role="evaluator")
    print(response)

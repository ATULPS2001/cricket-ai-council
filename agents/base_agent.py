"""Shared interface for all council agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentVerdict:
    agent_name: str
    prediction: Any
    confidence: float  # 0.0 - 1.0
    reasoning: str


class BaseAgent(ABC):
    """All council agents (Stats, Form, Conditions, Momentum) implement this."""

    name: str = "base"

    @abstractmethod
    def analyze(self, question: dict) -> AgentVerdict:
        """Given a structured question/context dict, return this agent's verdict."""
        raise NotImplementedError

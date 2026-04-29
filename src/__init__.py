"""
Multi-Agent Collaborative Auto-Programming System
多智能体协同自动编程系统
"""

__version__ = "1.0.0"
__author__ = "MiniMax Agent"

from .core.agent import Agent, AgentRole, AgentStatus
from .core.message import Message, MessageType
from .scheduler import TaskScheduler
from .executor import CodeExecutor, CodeLanguage
from .agents.coder_agent import CoderAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.debugger_agent import DebuggerAgent
from .agents.architect_agent import ArchitectAgent

__all__ = [
    "Agent",
    "AgentRole",
    "AgentStatus",
    "Message",
    "MessageType",
    "TaskScheduler",
    "CodeExecutor",
    "CodeLanguage",
    "CoderAgent",
    "ReviewerAgent",
    "DebuggerAgent",
    "ArchitectAgent",
]

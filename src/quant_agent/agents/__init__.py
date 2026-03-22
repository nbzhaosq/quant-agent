"""Sub-agents for specialized analysis roles."""

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult
from quant_agent.agents.technical import TechnicalAnalystAgent
from quant_agent.agents.fundamental import FundamentalAnalystAgent
from quant_agent.agents.sentiment import SentimentAnalystAgent
from quant_agent.agents.risk import RiskAssessorAgent
from quant_agent.agents.report_generator import ReportGeneratorAgent

__all__ = [
    "SubAgentBase",
    "AgentRole",
    "AnalysisResult",
    "TechnicalAnalystAgent",
    "FundamentalAnalystAgent",
    "SentimentAnalystAgent",
    "RiskAssessorAgent",
    "ReportGeneratorAgent",
]

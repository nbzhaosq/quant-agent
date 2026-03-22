"""Test for multi-agent architecture."""

import pytest
from quant_agent.agents.base import AgentRole,from quant_agent.agents.technical import TechnicalAnalystAgent
from quant_agent.agents.fundamental import FundamentalAnalystAgent


class TestAgentRoles:
    def test_agent_role_values(self):
        assert AgentRole.TECHNICAL.value == "technical"
        assert AgentRole.FUNDAMENTAL.value == "fundamental"


class TestAgentInitialization:
    def test_technical_agent_init(self):
        agent = TechnicalAnalystAgent()
        assert agent.role == AgentRole.TECHNICAL

    def test_fundamental_agent_init(self):
        agent = FundamentalAnalystAgent()
        assert agent.role == AgentRole.FUNDAMENTAL

"""Sub-agent base classes and specialized analysis roles."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
from pydantic import BaseModel

from quant_agent.tools.mcp_tools import create_quant_mcp_server
from quant_agent.core.config import Settings, get_settings


class AgentRole(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    REPORT = "report"


class AnalysisResult(BaseModel):
    agent_role: AgentRole
    stock_code: str
    summary: str
    details: dict[str, Any] = {}
    confidence: float = 0.5
    errors: list[str] = []
    created_at: datetime | None = None
    raw_response: str = ""

    def __init__(self, **data: Any) -> None:
        if data.get("created_at") is None:
            data["created_at"] = datetime.now()
        super().__init__(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_role": self.agent_role.value,
            "stock_code": self.stock_code,
            "summary": self.summary,
            "details": self.details,
            "confidence": self.confidence,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "raw_response": self.raw_response,
        }


class SubAgentBase(ABC):
    role: AgentRole
    description: str
    system_prompt: str
    _progress_callback: Callable[[str, dict[str, Any]], None] | None = None

    def __init__(self) -> None:
        self._settings = get_settings()
        self._mcp_server = create_quant_mcp_server()
        self._client: ClaudeSDKClient | None = None

    def set_progress_callback(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        self._progress_callback = callback

    def _emit(self, event: str, data: dict[str, Any]) -> None:
        if self._progress_callback:
            self._progress_callback(event, data)

    def _get_client(self) -> ClaudeSDKClient:
        if self._client is None:
            model = self._settings.anthropic_model or "claude-sonnet-4-20250514"
            env_vars: dict[str, str] = {}
            if self._settings.anthropic_base_url:
                env_vars["ANTHROPIC_BASE_URL"] = self._settings.anthropic_base_url
            if self._settings.anthropic_api_key:
                env_vars["ANTHROPIC_API_KEY"] = self._settings.anthropic_api_key
            options = ClaudeAgentOptions(
                system_prompt=self.system_prompt,
                mcp_servers={"quant": self._mcp_server},
                permission_mode="bypassPermissions",
                model=model,
                env=env_vars if env_vars else None,
            )
            self._client = ClaudeSDKClient(options=options)
        return self._client

    @abstractmethod
    def _build_query(self, stock_code: str) -> str:
        pass

    @abstractmethod
    def _parse_response(self, stock_code: str, response: str) -> AnalysisResult:
        pass

    async def analyze(self, stock_code: str) -> AnalysisResult:
        self._emit("agent_start", {"role": self.role.value})
        query = self._build_query(stock_code)
        self._emit("agent_query", {"role": self.role.value, "query": query[:100]})

        client = self._get_client()
        response_text = ""

        async with client:
            await client.query(query)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text

        self._emit("agent_response", {"role": self.role.value, "length": len(response_text)})
        result = self._parse_response(stock_code, response_text)
        result.raw_response = response_text
        return result

"""Core Agent implementation using Claude Agent SDK."""

import asyncio
from typing import Any

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)
from rich.console import Console

from quant_agent.tools.mcp_tools import create_quant_mcp_server
from quant_agent.core.config import get_settings

console = Console()

SYSTEM_PROMPT = """你是一个专业的量化投资分析助手。你的职责是：

1. **数据分析**：通过 Tushare 获取 A 股市场数据，包括行情、财务、资金流等
2. **技术分析**：计算和解读技术指标（MA、MACD、RSI、KDJ 等）
3. **基本面分析**：分析财务报表、估值指标、行业地位
4. **情绪分析**：解读市场新闻和舆情
5. **综合判断**：多维度整合信息，给出投资参考

**重要原则**：
- 所有分析仅供参考，不构成投资建议
- 明确标注数据来源和分析依据
- 对不确定性保持诚实
- 用清晰易懂的语言解释专业概念

**工具使用**：
- 使用 tushare_* 工具获取数据
- 使用 calculate_* 工具进行技术分析

请始终以专业、客观的态度进行分析。"""


class QuantAgent:
    """AI-powered quantitative analysis agent using Claude Agent SDK."""

    def __init__(self) -> None:
        self._client: ClaudeSDKClient | None = None
        self._mcp_server = create_quant_mcp_server()
        self._response_buffer: str = ""
        self._settings = get_settings()

    def _get_client(self) -> ClaudeSDKClient:
        if self._client is None:
            settings = self._settings
            model = settings.anthropic_model or "claude-sonnet-4-20250514"
            env_vars: dict[str, str] = {}
            if settings.anthropic_base_url:
                env_vars["ANTHROPIC_BASE_URL"] = settings.anthropic_base_url
            if settings.anthropic_api_key:
                env_vars["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
            options = ClaudeAgentOptions(
                system_prompt=SYSTEM_PROMPT,
                mcp_servers={"quant": self._mcp_server},
                permission_mode="bypassPermissions",
                model=model,
                env=env_vars if env_vars else None,
            )
            self._client = ClaudeSDKClient(options=options)
        return self._client

    def chat(self, user_message: str) -> str:
        return asyncio.run(self._chat_async(user_message))

    async def _chat_async(self, user_message: str) -> str:
        client = self._get_client()

        async with client:
            await client.query(user_message)

            response_text = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text

            return response_text

    async def chat_stream(self, user_message: str) -> Any:
        client = self._get_client()

        async with client:
            await client.query(user_message)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield block.text

    def reset(self) -> None:
        self._client = None

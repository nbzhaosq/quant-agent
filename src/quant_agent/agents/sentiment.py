"""Sentiment Analyst Agent - 新闻舆情/市场情绪分析专家."""

from datetime import datetime
from typing import Any

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult
from quant_agent.tools.mcp_tools import create_quant_mcp_server


SENTIMENT_SYSTEM_PROMPT = """你是一位专业的情绪分析师,专注于市场情绪和新闻舆情分析。

你的职责:
1. **舆情分析**: 分析相关新闻的情感倾向(正面/中性/负面)
2. **市场情绪**: 分析资金流向、换手率等市场情绪指标
3. **热点追踪**: 识别市场热点和关注焦点
4. **风险提示**: 标注情绪风险和过度反应
5. **投资建议**: 基于情绪面给出操作建议

请使用中文输出,保持简洁明了。"""


class SentimentAnalystAgent(SubAgentBase):
    """Sentiment Analyst Agent - 新闻舆情/市场情绪分析专家."""

    role = AgentRole.SENTIMENT
    description = "情绪分析师 - 新闻舆情/市场情绪分析"
    system_prompt = SENTIMENT_SYSTEM_PROMPT
    _mcp_server = create_quant_mcp_server()

    def _build_query(self, stock_code: str) -> str:
        return f"""请对股票 {stock_code} 进行情绪分析:

分析步骤:
1. 使用 tushare_search 搜索股票获取基本信息
2. 使用 tushare_moneyflow 获取资金流向数据
3. 分析市场情绪指标:
   - 资金净流入/流出
   - 主力资金动向
   - 换手率变化
4. 评估整体市场情绪
5. 给出情绪面投资建议

请使用中文输出,包含:
- 资金流向分析
- 市场情绪判断
- 情绪风险提示
- 投资建议
"""

    def _parse_response(self, stock_code: str, response: str) -> AnalysisResult:
        details: dict[str, Any] = {}
        errors: list[str] = []
        confidence = 0.5
        summary_lines: list[str] = []

        lines = response.strip().split("\n")
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Collect summary lines
            if line_stripped.startswith("##") or line_stripped.startswith("**"):
                summary_lines.append(line_stripped)
                continue

            # Parse key fields
            lower_line = line_stripped.lower()
            if "资金" in lower_line and ("流入" in lower_line or "流出" in lower_line):
                details["money_flow"] = line_stripped
            elif "情绪" in lower_line:
                details["sentiment"] = line_stripped
                if "乐观" in line_stripped or "积极" in line_stripped:
                    details["sentiment_score"] = 0.7
                elif "悲观" in line_stripped or "消极" in line_stripped:
                    details["sentiment_score"] = 0.3
            elif "风险" in lower_line:
                details["risk_warning"] = line_stripped
            elif "建议" in lower_line:
                parts = line_stripped.split(":", 1)
                if len(parts) > 1:
                    details["recommendation"] = parts[1].strip()

        summary = "\n".join(summary_lines) if summary_lines else response[:500]

        # Adjust confidence based on sentiment clarity
        if details.get("sentiment_score"):
            confidence = 0.6 + (details["sentiment_score"] - 0.5) * 0.4

        return AnalysisResult(
            agent_role=self.role,
            stock_code=stock_code,
            summary=summary,
            details=details,
            confidence=confidence,
            errors=errors,
            created_at=datetime.now(),
        )

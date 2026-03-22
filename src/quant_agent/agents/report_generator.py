"""Report Generator Agent - 综合报告生成专家."""

from datetime import datetime
from typing import Any

from claude_agent_sdk import AssistantMessage, TextBlock

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult
from quant_agent.tools.mcp_tools import create_quant_mcp_server


REPORT_SYSTEM_PROMPT = """你是一位专业的投资报告撰写专家，负责整合多个分析师的意见并生成综合报告。

你的职责:
1. **信息整合**: 整合技术面、基本面、情绪面、风险评估的分析结果
2. **逻辑分析**: 分析各维度的一致性和矛盾点
3. **综合判断**: 给出综合性的投资建议
4. **风险提示**: 汇总各维度风险并给出总体风险评估
5. **报告撰写**: 生成结构清晰、逻辑严谨的投资报告

请使用中文输出，报告应专业、客观、全面。"""


class ReportGeneratorAgent(SubAgentBase):
    """Report Generator Agent - 综合报告生成专家."""

    role = AgentRole.REPORT
    description = "报告生成器 - 综合报告生成专家"
    system_prompt = REPORT_SYSTEM_PROMPT
    _mcp_server = create_quant_mcp_server()

    def _build_query(
        self, stock_code: str, analysis_results: list[dict[str, Any]] | None = None
    ) -> str:
        results_summary = ""
        if analysis_results:
            for result in analysis_results:
                role = result.get("agent_role", "unknown")
                summary = result.get("summary", "")[:200]
                confidence = result.get("confidence", 0)
                results_summary += f"\n### {role}\n{summary}\n置信度: {confidence:.0%}\n"

        return f"""请为股票 {stock_code} 生成综合投资分析报告。

以下是从各专业分析师获取的分析结果:
{results_summary}

报告结构:
1. **股票概览**: 基本信息、行业归属
2. **技术面分析**: 趋势、动量、波动性总结
3. **基本面分析**: 财务健康度、估值水平
4. **情绪面分析**: 市场情绪、资金动向
5. **风险评估**: 综合风险等级
6. **投资建议**: 明确的买入/卖出/观望建议及理由
7. **风险提示**: 需要关注的风险因素

请确保报告:
- 结构清晰，使用标题分隔各部分
- 观点明确，给出明确的投资建议
- 风险提示充分
- 语言专业、客观"""

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

            if line_stripped.startswith("##") or line_stripped.startswith("**"):
                summary_lines.append(line_stripped)
                continue

            lower_line = line_stripped.lower()
            if "买入" in lower_line and "建议" in lower_line:
                details["recommendation"] = "买入"
                confidence = 0.8
            elif "卖出" in lower_line and "建议" in lower_line:
                details["recommendation"] = "卖出"
                confidence = 0.6
            elif "观望" in lower_line and "建议" in lower_line:
                details["recommendation"] = "观望"
                confidence = 0.5

            if "风险等级" in lower_line or "综合风险" in lower_line:
                if "高" in line_stripped:
                    details["risk_level"] = "高"
                elif "中" in line_stripped:
                    details["risk_level"] = "中"
                elif "低" in line_stripped:
                    details["risk_level"] = "低"

        summary = "\n".join(summary_lines) if summary_lines else response[:800]

        return AnalysisResult(
            agent_role=self.role,
            stock_code=stock_code,
            summary=summary,
            details=details,
            confidence=confidence,
            errors=errors,
            created_at=datetime.now(),
        )

    async def analyze(
        self,
        stock_code: str,
        analysis_results: list[dict[str, Any]] | None = None,
    ) -> AnalysisResult:
        """Generate comprehensive report from analysis results.

        Args:
            stock_code: Stock code to analyze
            analysis_results: Optional list of analysis results from other agents
        """
        self._emit("agent_start", {"role": self.role.value})
        query = self._build_query(stock_code, analysis_results)
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

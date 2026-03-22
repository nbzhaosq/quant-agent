"""Fundamental Analyst Agent - 财务报表/估值/行业分析专家."""

from datetime import datetime
from typing import Any

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult
from quant_agent.tools.mcp_tools import create_quant_mcp_server


FUNDAMENTAL_SYSTEM_PROMPT = """你是一位专业的基本面分析师，专注于公司的财务报表和估值分析。

你的职责:
1. **财务分析**: 使用 tushare_financial 获取利润表、现金流量表
2. **估值分析**: 分析 PE、PB、ROE、DCF等估值指标
3. **行业分析**: 分析所在行业的竞争格局和增长前景
4. **风险提示**: 标注财务风险和预警信号
5. **投资建议**: 基于基本面给出投资建议

请使用中文输出,保持简洁明了。"""


class FundamentalAnalystAgent(SubAgentBase):
    """Fundamental Analyst Agent - 财务报表/估值分析专家."""

    role = AgentRole.FUNDAMENTAL
    description = "基本面分析师 - 财务报表/估值/行业分析"
    system_prompt = FUNDAMENTAL_SYSTEM_PROMPT
    _mcp_server = create_quant_mcp_server()

    def _build_query(self, stock_code: str) -> str:
        return f"""请对股票 {stock_code} 进行基本面分析:

分析步骤:
1. 使用 tushare_search 搜索股票(如果需要)
2. 使用 tushare_financial 获取最近4期的财务数据(利润表、资产负债表、现金流量表)
3. 计算关键指标:
   - 营收增长率
   - 净利润增长率
   - ROE (Return on Equity)
   - PE/PB 比率
4. 分析行业地位和竞争格局
5. 给出投资建议(买入/卖出/观望)

请使用中文输出,包含:
- 核心财务指标分析
- 估值水平评估
- 行业对比分析
- 风险提示
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

            if line_stripped.startswith("##") or line_stripped.startswith("**"):
                summary_lines.append(line_stripped)
                continue

            if ":" in line_stripped:
                parts = line_stripped.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()

                    if "pe" in key or "市盈率" in key:
                        try:
                            details["pe_ratio"] = float(value.replace("%", "").strip())
                        except ValueError:
                            pass
                    elif "pb" in key or "市净率" in key:
                        try:
                            details["pb_ratio"] = float(value.replace("%", "").strip())
                        except ValueError:
                            pass
                    elif "roe" in key:
                        try:
                            details["roe"] = float(value.replace("%", "").strip())
                        except ValueError:
                            pass
                    elif "营收" in key and "增长" in key:
                        details["revenue_growth"] = value
                    elif "净利" in key and "增长" in key:
                        details["profit_growth"] = value
                    elif "建议" in key or "投资建议" in key:
                        details["recommendation"] = value
                    elif "风险" in key:
                        details["risk_warning"] = value

        summary = "\n".join(summary_lines) if summary_lines else response[:500]

        if details.get("recommendation"):
            confidence = 0.7
        if details.get("pe_ratio") and details.get("roe"):
            confidence = min(confidence + 0.1, 0.9)

        return AnalysisResult(
            agent_role=self.role,
            stock_code=stock_code,
            summary=summary,
            details=details,
            confidence=confidence,
            errors=errors,
            created_at=datetime.now(),
        )

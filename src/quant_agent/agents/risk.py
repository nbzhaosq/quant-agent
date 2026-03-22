"""Risk Assessor Agent - 风险评估专家."""

from datetime import datetime
from typing import Any

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult
from quant_agent.tools.mcp_tools import create_quant_mcp_server


RISK_SYSTEM_PROMPT = """你是一位专业的风险评估师，专注于投资风险识别和评估。

你的职责:
1. **风险评估**: 分析价格波动率,市场风险
2. **VaR计算**: 计算风险价值
3. **风险提示**: 标注风险等级(低/中/高)
4. **投资建议**: 给出风险控制建议

请使用中文输出,保持简洁明了。"""


class RiskAssessorAgent(SubAgentBase):
    """Risk Assessor Agent - 风险评估专家."""

    role = AgentRole.RISK
    description = "风险评估师 - 风险评估专家"
    system_prompt = RISK_SYSTEM_PROMPT
    _mcp_server = create_quant_mcp_server()

    def _build_query(self, stock_code: str) -> str:
        return f"""请对股票 {stock_code} 进行风险评估:

分析步骤:
1. 使用 tushare_daily 获取最近60个交易日的行情数据
2. 使用 calculate_volatility 讌算波动率和ATR
3. 分析最大回撤幅度
4. 评估整体风险
5. 给出投资建议

请使用中文输出,包含:
- 波动率水平
- 最大回撤
- 风险等级(低/中/高)
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

            # Parse specific fields
            lower_line = line_stripped.lower()
            if "波动率" in lower_line or "volatility" in lower_line:
                # Try to extract numeric value
                import re

                match = re.search(r"(\d+\.?\d*)", line_stripped)
                if match:
                    try:
                        details["volatility"] = float(match.group(1))
                    except ValueError:
                        errors.append(f"无法解析波动率: {line_stripped}")

            elif "回撤" in lower_line or "drawdown" in lower_line:
                import re

                match = re.search(r"(\d+\.?\d*)%?", line_stripped)
                if match:
                    try:
                        details["max_drawdown"] = float(match.group(1))
                    except ValueError:
                        errors.append(f"无法解析最大回撤: {line_stripped}")

            elif "风险等级" in lower_line:
                if "低" in line_stripped:
                    details["risk_level"] = "低"
                elif "中" in line_stripped:
                    details["risk_level"] = "中"
                elif "高" in line_stripped:
                    details["risk_level"] = "高"
                else:
                    details["risk_level"] = line_stripped

            elif "建议" in lower_line or "投资建议" in lower_line:
                parts = line_stripped.split(":", 1)
                if len(parts) > 1:
                    details["recommendation"] = parts[1].strip()

        summary = "\n".join(summary_lines) if summary_lines else response[:500]

        # Adjust confidence based on risk level
        if details.get("risk_level") == "低":
            confidence = 0.8
        elif details.get("risk_level") == "高":
            confidence = 0.4

        return AnalysisResult(
            agent_role=self.role,
            stock_code=stock_code,
            summary=summary,
            details=details,
            confidence=confidence,
            errors=errors,
            created_at=datetime.now(),
        )

"""Technical Analyst Agent - MA/MACD/RSI/KDJ/布林带分析专家."""

from datetime import datetime
from typing import Any

from quant_agent.agents.base import SubAgentBase, AgentRole, AnalysisResult


TECHNICAL_SYSTEM_PROMPT = """你是一位专业的技术分析师，专注于股票的技术指标分析。

你的职责:
1. **趋势分析**: 分析均线系统(MA5, MA10, MA20, MA60)判断趋势方向
2. **动量判断**: 分析MACD、KDJ、RSI指标判断买卖时机
3. **波动分析**: 计算ATR、波动率指标
4. **形态识别**: 识别技术形态(头肩顶、双底等)
5. **风险提示**: 标注技术风险级别
6. **投资建议**: 基于技术面给出操作建议

**工具使用**:
- 使用 tushare_daily 获取日线行情数据
- 使用 calculate_ma 计算移动平均线
- 使用 calculate_macd 计算 MACD 指标
- 使用 calculate_rsi 计算 RSI 指标
- 使用 calculate_volatility 计算波动率

请使用中文输出，保持简洁明了。"""


class TechnicalAnalystAgent(SubAgentBase):
    role = AgentRole.TECHNICAL
    description = "技术指标分析专家 - MA/MACD/RSI/KDJ/布林带"
    system_prompt = TECHNICAL_SYSTEM_PROMPT

    def _build_query(self, stock_code: str) -> str:
        return f"""请对股票 {stock_code} 进行技术分析:

分析步骤:
1. 使用 tushare_daily 获取最近60个交易日的行情数据
2. 使用 calculate_ma 计算 MA5, MA10, MA20, MA60
3. 使用 calculate_macd 计算 MACD 指标
4. 使用 calculate_rsi 计算 RSI 指标
5. 使用 calculate_volatility 计算波动率和 ATR

综合以上指标，给出技术面分析和投资建议。

请使用中文输出，包含:
- 当前价格与各均线关系
- MACD状态和信号判断
- RSI超买超卖判断
- 波动率水平
- 技术形态总结
- 风险等级
- 操作建议(买入/卖出/观望)"""

    def _parse_response(self, stock_code: str, response: str) -> AnalysisResult:
        details: dict[str, Any] = {"indicators": {}}
        errors: list[str] = []
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
                    if key in ["ma趋势", "ma", "均线"]:
                        details["indicators"]["ma_trend"] = value
                    elif key in ["macd", "dif", "dea"]:
                        details["indicators"]["macd"] = value
                    elif key in ["rsi"]:
                        try:
                            details["indicators"]["rsi"] = float(value)
                        except ValueError:
                            details["indicators"]["rsi"] = value
                    elif key in ["波动率", "volatility"]:
                        details["indicators"]["volatility"] = value
                    elif key in ["建议", "操作", "recommendation"]:
                        details["recommendation"] = value
                    elif key in ["风险", "level"]:
                        details["risk_level"] = value

        summary = " ".join(summary_lines) if summary_lines else response[:500]

        confidence = 0.5
        if "买入" in summary or "金叉" in summary:
            confidence = 0.8
        elif "卖出" in summary or "死叉" in summary:
            confidence = 0.6

        return AnalysisResult(
            agent_role=self.role,
            stock_code=stock_code,
            summary=summary,
            details=details,
            confidence=confidence,
            errors=errors,
            created_at=datetime.now(),
        )

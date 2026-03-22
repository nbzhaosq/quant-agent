"""QuantCoordinator - Multi-agent coordinator with GraphRAG support."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from quant_agent.tools.mcp_tools import create_quant_mcp_server
from quant_agent.agents import (
    AgentRole,
    AnalysisResult,
    SubAgentBase,
    TechnicalAnalystAgent,
    FundamentalAnalystAgent,
    SentimentAnalystAgent,
    RiskAssessorAgent,
    ReportGeneratorAgent,
)
from quant_agent.knowledge import GraphitiClient, VectorStore
from quant_agent.core.config import get_settings
from quant_agent.ui.status import AnalysisStage

logger = logging.getLogger(__name__)


COORDINATOR_SYSTEM_PROMPT = """你是一个量化投资研究团队的协调者，负责统筹多 agent 协作完成股票分析任务。

## 团队成员
- **技术分析师** (TechnicalAnalystAgent): 技术指标分析
- **基本面分析师** (FundamentalAnalystAgent): 财务报表和估值分析
- **情绪分析师** (SentimentAnalystAgent): 新闻舆情分析
- **风险评估师** (RiskAssessorAgent): 风险评估
- **报告生成器** (ReportGeneratorAgent): 综合报告生成

## 工作流程
1. 接收分析请求
2. 查询 GraphRAG 获取历史上下文
3. 并行调用 4 个专业 agent
4. 汇总分析结果
5. 生成综合报告
6. 将结果存储到知识图谱
"""


class QuantCoordinator:
    role = "coordinator"
    description = "投研团队协调者"
    system_prompt = COORDINATOR_SYSTEM_PROMPT

    def __init__(self, days: int = 120) -> None:
        self._settings = get_settings()
        self._graphiti: GraphitiClient | None = None
        self._vector_store: VectorStore | None = None
        self._agents: dict[AgentRole, SubAgentBase] = {}
        self._mcp_server = create_quant_mcp_server()
        self._progress_callback: Callable[[str, dict[str, Any]], None] | None = None
        self._days = days
        self._init_agents()

    def set_progress_callback(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        self._progress_callback = callback

    def _emit(self, event: str, data: dict[str, Any]) -> None:
        if self._progress_callback:
            self._progress_callback(event, data)
        logger.info(f"[{event}] {data}")

    def _init_agents(self) -> None:
        self._agents = {
            AgentRole.TECHNICAL: TechnicalAnalystAgent(),
            AgentRole.FUNDAMENTAL: FundamentalAnalystAgent(),
            AgentRole.SENTIMENT: SentimentAnalystAgent(),
            AgentRole.RISK: RiskAssessorAgent(),
            AgentRole.REPORT: ReportGeneratorAgent(),
        }

    async def initialize(self) -> None:
        self._emit("stage", {"stage": AnalysisStage.INIT.value, "message": "初始化协调器"})
        if self._graphiti is None:
            self._graphiti = GraphitiClient()
            await self._graphiti.initialize()

        if self._vector_store is None:
            self._vector_store = VectorStore()
            self._vector_store.initialize()

    def _parse_stock_code(self, user_input: str) -> str:
        import re

        patterns = [
            r"\d{6}\.(SH|SZ)",
            r"[A-Z]{2,4}\d{4,6}",
            r"[\u4e00-\u9fa5]{2,4}",
        ]
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group()
        return user_input.strip()[:10]

    def _build_analysis_prompt(self, user_input: str, stock_code: str) -> str:
        return f"""请对股票 {stock_code} 进行全面的投资分析。

用户原始需求: {user_input}

请从以下维度进行分析:
1. 技术面分析: MA、MACD、RSI、KDJ、布林带等指标
2. 基本面分析: 财务报表、估值指标、行业地位
3. 情绪面分析: 市场情绪、资金流向、新闻舆情
4. 风险评估: 波动率、最大回撤、风险等级

最后给出综合投资建议。"""

    async def analyze_with_progress(
        self,
        user_input: str,
        progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        if progress_callback:
            self.set_progress_callback(progress_callback)

        return await self.analyze(user_input)

    async def analyze(self, user_input: str) -> dict[str, Any]:
        if not user_input:
            raise ValueError("user_input is required")

        self._emit("stage", {"stage": AnalysisStage.PARSING.value, "message": "解析用户请求"})
        await asyncio.sleep(0.1)

        stock_code = self._parse_stock_code(user_input)
        analysis_prompt = self._build_analysis_prompt(user_input, stock_code)

        self._emit(
            "parsed",
            {
                "stock_code": stock_code,
                "prompt": analysis_prompt,
                "original_input": user_input,
            },
        )

        await self.initialize()

        self._emit("stage", {"stage": AnalysisStage.GRAPH_RAG.value, "message": "查询历史分析记录"})
        context = await self._get_graphrag_context(stock_code)
        self._emit("context", {"stock_code": stock_code, "has_context": bool(context)})

        # Fetch price data for chart display (silent, no stage emission)
        price_data = await self._get_price_data(stock_code)

        agent_roles = [
            (AgentRole.TECHNICAL, AnalysisStage.TECHNICAL),
            (AgentRole.FUNDAMENTAL, AnalysisStage.FUNDAMENTAL),
            (AgentRole.SENTIMENT, AnalysisStage.SENTIMENT),
            (AgentRole.RISK, AnalysisStage.RISK),
        ]

        async def run_agent_with_progress(
            role: AgentRole, stage: AnalysisStage, stock: str
        ) -> AnalysisResult | Exception:
            agent = self._agents[role]
            role_name = role.value
            self._emit("agent_start", {"role": role_name, "stage": stage.value})
            self._emit("stage", {"stage": stage.value, "message": f"{agent.description} 正在分析"})

            try:
                self._emit(
                    "agent_progress", {"role": role_name, "progress": 30, "message": "获取数据"}
                )
                await asyncio.sleep(0.2)

                self._emit(
                    "agent_progress", {"role": role_name, "progress": 60, "message": "分析中"}
                )
                result = await agent.analyze(stock)

                self._emit(
                    "agent_progress", {"role": role_name, "progress": 90, "message": "生成结论"}
                )
                await asyncio.sleep(0.1)

                self._emit(
                    "agent_complete",
                    {
                        "role": role_name,
                        "confidence": result.confidence,
                        "summary": result.summary[:100] if result.summary else "",
                    },
                )
                return result
            except Exception as e:
                self._emit("agent_error", {"role": role_name, "error": str(e)})
                return e

        results = await asyncio.gather(
            *[run_agent_with_progress(role, stage, stock_code) for role, stage in agent_roles],
            return_exceptions=True,
        )

        successful_results = [r for r in results if isinstance(r, AnalysisResult)]

        if len(successful_results) < 2:
            return {
                "error": "所有 agent 分析都失败",
                "results": [],
            }

        formatted_results = [r.to_dict() for r in successful_results]

        self._emit("stage", {"stage": AnalysisStage.REPORT.value, "message": "生成综合报告"})
        report_agent = self._agents[AgentRole.REPORT]
        assert isinstance(report_agent, ReportGeneratorAgent)
        final_report = await report_agent.analyze(stock_code, formatted_results)

        self._emit("stage", {"stage": AnalysisStage.STORING.value, "message": "存储到知识图谱"})
        if self._graphiti and final_report:
            try:
                await self._graphiti.add_analysis_episode(
                    ts_code=stock_code,
                    analysis_type="comprehensive",
                    summary=final_report.summary,
                    recommendation=final_report.details.get("recommendation", "综合分析"),
                    confidence=final_report.confidence,
                )
            except Exception as e:
                import traceback

                self._emit(
                    "warning", {"message": f"存储失败: {e}", "traceback": traceback.format_exc()}
                )

        self._emit("stage", {"stage": AnalysisStage.DONE.value, "message": "分析完成"})

        return {
            "stock_code": stock_code,
            "user_input": user_input,
            "analysis_prompt": analysis_prompt,
            "context": context,
            "price_data": price_data,
            "results": formatted_results,
            "final_report": final_report.to_dict() if final_report else None,
            "timestamp": datetime.now().isoformat(),
        }

    async def _get_graphrag_context(self, stock_code: str) -> dict[str, Any]:
        if not self._graphiti:
            return {}
        try:
            context = await self._graphiti.get_stock_context(stock_code)
            return context
        except Exception as e:
            self._emit("warning", {"message": f"GraphRAG 查询失败: {e}"})
            return {}

    async def _get_price_data(self, stock_code: str) -> list[dict[str, Any]]:
        """Fetch historical price data for chart display."""
        try:
            from quant_agent.data.tushare_client import TushareClient

            client = TushareClient()
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=self._days * 2)).strftime("%Y%m%d")

            df = client.get_daily(stock_code, start_date, end_date)

            if df.empty:
                return []

            # Sort by date ascending for chart
            df = df.sort_values("trade_date", ascending=True)
            df = df.tail(self._days)  # Limit to requested days

            # Convert to lightweight-charts format
            price_data = []
            for _, row in df.iterrows():
                date_str = str(row["trade_date"])

                price_data.append({
                    "time": date_str,  # YYYYMMDD format for lightweight-charts
                    "open": float(row["open"]) if row.get("open") else None,
                    "high": float(row["high"]) if row.get("high") else None,
                    "low": float(row["low"]) if row.get("low") else None,
                    "close": float(row["close"]) if row.get("close") else None,
                    "volume": float(row["vol"]) if row.get("vol") else None,
                })

            return price_data
        except Exception as e:
            logger.warning(f"获取价格数据失败: {e}")
            return []

    def get_agent(self, role: AgentRole) -> SubAgentBase | None:
        return self._agents.get(role)

    def list_agents(self) -> list[str]:
        return [agent.description for agent in self._agents.values()]

    async def close(self) -> None:
        if self._graphiti:
            await self._graphiti.close()
        if self._vector_store:
            self._vector_store.close()

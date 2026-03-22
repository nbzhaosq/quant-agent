"""Graphiti client for quant research knowledge graph."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from quant_agent.core.config import get_settings

logger = logging.getLogger(__name__)


class GraphitiClient:
    def __init__(self) -> None:
        self._graphiti = None
        self._settings = get_settings()
        self._initialized = False
        self._llm_client = None
        self._available: bool | None = None  # None = not checked yet

    def is_configured(self) -> bool:
        """Check if Graphiti LLM is properly configured."""
        settings = self._settings
        return bool(
            settings.graphiti_llm_model
            and settings.graphiti_llm_base_url
            and settings.neo4j_password
        )

    @property
    def is_available(self) -> bool:
        """Check if Graphiti is available (cached result)."""
        if self._available is None:
            self._available = self.is_configured()
        return self._available

    async def initialize(self) -> None:
        if not self.is_configured():
            logger.warning(
                "Graphiti not configured (requires graphiti_llm_model, "
                "graphiti_llm_base_url, and neo4j_password). Skipping knowledge graph storage."
            )
            return

        if self._initialized:
            return

        self._llm_client = self._create_llm_client()
        embedder = self._create_embedder()
        cross_encoder = self._create_cross_encoder()

        Graphiti = await self._import_graphiti()
        self._graphiti = Graphiti(
            uri=self._settings.neo4j_uri,
            user=self._settings.neo4j_user,
            password=self._settings.neo4j_password,
            llm_client=self._llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        await self._graphiti.build_indices_and_constraints()
        self._initialized = True

    def _create_llm_client(self):
        from graphiti_core.llm_client.config import LLMConfig

        from quant_agent.knowledge.glm_llm_client import GLMClient

        settings = self._settings
        api_key = settings.graphiti_llm_api_key or "ollama"
        config = LLMConfig(
            api_key=api_key,
            model=settings.graphiti_llm_model,
            base_url=settings.graphiti_llm_base_url,
        )
        # Use GLMClient which handles reasoning_content format
        return GLMClient(config=config)

    def _create_embedder(self):
        from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

        settings = self._settings
        config = OpenAIEmbedderConfig(
            api_key=settings.embedding_api_key or "ollama",
            base_url=f"{settings.embedding_base_url}",
            embedding_model=settings.embedding_model,
            embedding_dim=settings.embedding_dimension,
        )
        return OpenAIEmbedder(config=config)

    def _create_cross_encoder(self):
        from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
        from graphiti_core.llm_client.config import LLMConfig

        settings = self._settings
        config = LLMConfig(
            api_key="ollama",
            model=settings.graphiti_llm_model,
            base_url=settings.graphiti_llm_base_url,
        )
        return OpenAIRerankerClient(client=self._llm_client, config=config)

    async def _import_graphiti(self) -> Any:
        try:
            from graphiti_core import Graphiti

            return Graphiti
        except ImportError as e:
            raise ImportError(
                f"graphiti-core is required. Install with: pip install graphiti-core\n{e}"
            ) from e

    async def add_stock_episode(
        self,
        ts_code: str,
        name: str,
        industry: str | None = None,
        sector: str | None = None,
        market_cap: float | None = None,
        pe_ratio: float | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> str | None:
        if not self.is_available:
            return None

        if not self._initialized:
            await self.initialize()

        if not self._initialized:
            return None

        EpisodeType = await self._get_episode_type()

        # Flatten nested structures to avoid list/dict parsing issues
        flat_additional = {}
        if additional_data:
            for key, value in additional_data.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        flat_additional[f"{key}_{k}"] = v
                elif isinstance(value, list):
                    flat_additional[key] = ", ".join(str(v) for v in value)
                else:
                    flat_additional[key] = value

        stock_data = {
            "ts_code": ts_code,
            "name": name,
            "industry": industry,
            "sector": sector,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            **flat_additional,
        }

        result = await self._graphiti.add_episode(
            name=f"股票数据_{ts_code}",
            episode_body=json.dumps(stock_data, ensure_ascii=False),
            source=EpisodeType.json,
            source_description="A股股票基础数据",
            reference_time=datetime.now(timezone.utc),
            group_id="stock_research",
        )

        return result

    async def add_news_episode(
        self,
        title: str,
        content: str,
        category: str,
        related_stocks: list[str],
        sentiment: str | None = None,
        source: str | None = None,
    ) -> str | None:
        if not self.is_available:
            return None

        if not self._initialized:
            await self.initialize()

        if not self._initialized:
            return None

        EpisodeType = await self._get_episode_type()

        # Flatten list to avoid parsing issues
        news_data = {
            "title": title,
            "content": content,
            "category": category,
            "related_stocks": ", ".join(related_stocks),
            "sentiment": sentiment,
            "source": source,
        }

        result = await self._graphiti.add_episode(
            name=f"新闻_{title[:30]}",
            episode_body=json.dumps(news_data, ensure_ascii=False),
            source=EpisodeType.json,
            source_description=f"{category}新闻",
            reference_time=datetime.now(timezone.utc),
            group_id="stock_research",
        )

        return result

    async def add_analysis_episode(
        self,
        ts_code: str,
        analysis_type: str,
        summary: str,
        recommendation: str,
        confidence: float,
        details: dict[str, Any] | None = None,
    ) -> str | None:
        if not self.is_available:
            return None

        if not self._initialized:
            await self.initialize()

        if not self._initialized:
            return None

        EpisodeType = await self._get_episode_type()

        # Flatten details to avoid nested structures that may cause parsing issues
        flat_details = {}
        if details:
            for key, value in details.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        flat_details[f"{key}_{k}"] = v
                elif isinstance(value, list):
                    flat_details[key] = ", ".join(str(v) for v in value)
                else:
                    flat_details[key] = value

        analysis_data = {
            "ts_code": ts_code,
            "analysis_type": analysis_type,
            "summary": summary,
            "recommendation": recommendation,
            "confidence": confidence,
            "analyst": "quant_agent",
            **flat_details,
        }

        try:
            logger.debug(f"Calling Graphiti add_episode for {ts_code}_{analysis_type}")
            logger.debug(f"Episode data: {json.dumps(analysis_data, ensure_ascii=False)}")
            result = await self._graphiti.add_episode(
                name=f"分析报告_{ts_code}_{analysis_type}",
                episode_body=json.dumps(analysis_data, ensure_ascii=False),
                source=EpisodeType.json,
                source_description=f"{analysis_type}分析",
                reference_time=datetime.now(timezone.utc),
                group_id="stock_research",
            )
            logger.debug(f"Graphiti add_episode succeeded: {result}")
            return result
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            logger.warning(f"Graphiti 存储失败 (将跳过知识图谱存储): {e}")
            logger.debug(f"详细错误: {tb}")
            return None  # Return None instead of raising to allow analysis to continue

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.is_available:
            return []

        if not self._initialized:
            await self.initialize()

        if not self._initialized or not self._graphiti:
            return []

        results = await self._graphiti.search(query, num_results=num_results)

        return [
            {
                "fact": edge.fact,
                "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
                "invalid_at": edge.invalid_at.isoformat() if edge.invalid_at else None,
                "source_node": edge.source_node_uuid,
                "target_node": edge.target_node_uuid,
            }
            for edge in results
        ]

    async def get_stock_context(self, ts_code: str) -> dict[str, Any]:
        if not self.is_available:
            return {"ts_code": ts_code, "facts": [], "fact_count": 0}

        if not self._initialized:
            await self.initialize()

        if not self._initialized:
            return {"ts_code": ts_code, "facts": [], "fact_count": 0}

        results = await self.search(
            f"{ts_code} 财务 业绩 行业 新闻 分析",
            num_results=15,
        )

        return {
            "ts_code": ts_code,
            "facts": results,
            "fact_count": len(results),
        }

    async def close(self) -> None:
        if self._graphiti:
            await self._graphiti.close()
            self._initialized = False

    async def _get_episode_type(self) -> Any:
        from graphiti_core.nodes import EpisodeType

        return EpisodeType

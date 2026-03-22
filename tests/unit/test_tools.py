"""Tests for MCP tools."""

import asyncio
import json

import pytest

from quant_agent.tools.mcp_tools import (
    calculate_ma,
    calculate_macd,
    calculate_rsi,
    create_quant_mcp_server,
)


class TestCalculateMATool:
    @pytest.mark.asyncio
    async def test_ma_calculation(self):
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        result = await calculate_ma.handler({"prices": prices})

        assert "content" in result
        assert len(result["content"]) == 1
        content = json.loads(result["content"][0]["text"])
        assert "MA5" in content

    @pytest.mark.asyncio
    async def test_ma_with_custom_periods(self):
        prices = list(range(1, 101))  # 100 days of data
        result = await calculate_ma.handler({"prices": prices, "periods": [5, 10, 20]})

        content = json.loads(result["content"][0]["text"])
        assert "MA5" in content
        assert "MA10" in content
        assert "MA20" in content


class TestCalculateMACDTool:
    @pytest.mark.asyncio
    async def test_macd_calculation(self):
        prices = list(range(100, 150))  # 50 days of uptrend
        result = await calculate_macd.handler({"prices": prices})

        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert "DIF" in content
        assert "DEA" in content

    @pytest.mark.asyncio
    async def test_macd_insufficient_data(self):
        prices = [100, 101, 102]  # Only 3 days
        result = await calculate_macd.handler({"prices": prices})

        assert result.get("is_error") is True


class TestCalculateRSITool:
    @pytest.mark.asyncio
    async def test_rsi_calculation(self):
        prices = [100 + i * (1 if i % 2 == 0 else -1) for i in range(30)]
        result = await calculate_rsi.handler({"prices": prices})

        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert "RSI" in content
        assert "level" in content


class TestMCPServerCreation:
    def test_create_mcp_server(self):
        server = create_quant_mcp_server()
        assert server is not None
        assert server["type"] == "sdk"
        assert server["name"] == "quant"

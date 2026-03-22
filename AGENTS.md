# AGENTS.md

Coding agent instructions for the quant-agent project.

## Project Overview

AI-powered quantitative investment analysis agent for A-share (Chinese) stocks.

**Tech Stack**:
- Claude Agent SDK - LLM orchestration
- Tushare API - A-share market data
- Neo4j + Graphiti - Knowledge graph (GraphRAG)
- SQLite + sqlite-vec - Vector storage

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run quant-agent chat                        # Interactive chat (single agent)
uv run quant-agent analyze 600519.SH           # Analyze specific stock
uv run quant-agent search 茅台                  # Search stocks
uv run quant-agent team-analyze 600519.SH      # Multi-agent team analysis
uv run quant-agent mcp "茅台相关新闻" -c 新闻    # Semantic search

# Testing
uv run pytest                              # Run all tests
uv run pytest tests/unit/test_tools.py -v  # Single test file
uv run pytest -k "test_ma" -v              # Run tests matching pattern

# Linting & Type Checking
uv run ruff check .              # Check for lint errors
uv run ruff check . --fix        # Auto-fix lint errors
uv run mypy src/                 # Type check

# Format
uv run ruff format .             # Format code
```

## Architecture

```
src/quant_agent/
├── core/
│   ├── coordinator.py    # QuantCoordinator - 多 agent 协调器
│   ├── agent.py          # QuantAgent - 单 agent 模式
│   └── config.py         # Settings via pydantic-settings
├── knowledge/
│   ├── graphiti_client.py  # Graphiti 知识图谱客户端
│   ├── vector_store.py     # SQLite + sqlite-vec 向量存储
│   └── entities.py         # 自定义实体类型
├── agents/
│   ├── base.py             # SubAgentBase 基类
│   ├── technical.py        # 技术指标分析专家
│   ├── fundamental.py      # 基本面分析专家
│   ├── sentiment.py        # 情绪分析专家
│   ├── risk.py             # 风险评估专家
│   └── report_generator.py # 综合报告生成专家
├── tools/
│   └── mcp_tools.py        # MCP 工具定义
├── data/
│   └── tushare_client.py   # Tushare API 客户端
└── cli.py                  # Typer CLI 入口
```

## Multi-Agent Architecture

```
QuantCoordinator (协调者)
├── TechnicalAnalystAgent (技术分析)
│   └── MA, MACD, RSI, KDJ, 布林带, 波动率
├── FundamentalAnalystAgent (基本面分析)
│   └── 财务报表, 估值指标, 行业分析
├── SentimentAnalystAgent (情绪分析)
│   └── 新闻舆情, 市场情绪, 资金流向
├── RiskAssessorAgent (风险评估)
│   └── 波动率, VaR, 风险等级
└── ReportGeneratorAgent (报告生成)
    └── 综合分析报告
```

**工作流程**:
1. 协调者接收分析请求
2. 查询 GraphRAG 获取历史上下文
3. 并行调用 4 个专业 agent
4. 汇总分析结果
5. 生成综合报告
6. 存储结果到知识图谱

## Data Layer

```
┌── Tushare API (行情/财务数据)
├── Neo4j + Graphiti (知识图谱)
└── SQLite + sqlite-vec (向量存储)
```

## Adding MCP Tools

在 `src/quant_agent/tools/mcp_tools.py` 中使用 `@tool` 装饰器：

```python
from claude_agent_sdk import tool

@tool(
    "my_tool",
    "工具描述",
    {"param1": str, "param2": int | None},
)
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    result = do_something(args["param1"])
    return {
        "content": [{"type": "text", "text": result}]
    }
```

然后在 `create_quant_mcp_server()` 中注册

## Required Environment Variables

```bash
# Tushare (required)
TUSHARE_TOKEN=your_tushare_token

# Neo4j (required for GraphRAG)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# OpenAI (required for Graphiti)
OPENAI_API_KEY=your_openai_key
```

## Code Style

### Python Version
- Requires Python 3.12+
- Use modern syntax: `list[str]` instead of `List[str]`, `str | None` instead of `Optional[str]`

### Imports
```python
"""Module docstring."""

# Stdlib imports (alphabetical)
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

# Third-party imports (alphabetical)
import numpy as np
import pandas as pd
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local imports
from quant_agent.core.config import get_settings
```

### Naming Conventions
- **Classes**: PascalCase (`QuantAgent`, `TushareClient`)
- **Functions/Methods**: snake_case (`calculate_ma`, `get_daily`)
- **Private methods**: Leading underscore (`_get_client`, `_chat_async`)
- **Constants**: UPPER_SNAKE_CASE (`SYSTEM_PROMPT`)

### Type Annotations
- All functions must have complete type annotations (mypy strict mode)
- Use union syntax: `str | None` not `Optional[str]`
- Use generic syntax: `list[str]`, `dict[str, Any]` not `List[str]`, `Dict[str, Any]`

### Line Length
- Maximum 100 characters

### Error Handling
- Use specific exception types
- Return error dict with `is_error: True` for tool handlers
- Never use bare `except:` or empty `except Exception:` blocks

## Testing

### Test Structure
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Fixtures in `tests/conftest.py`

### Test Naming
- Test classes: `Test<ComponentName>`
- Test methods: `test_<action>_<condition>`

## Important Notes

- 所有分析仅供参考，不构成投资建议
- 中文注释/messages 可 acceptable for user-facing strings
- 使用 `ensure_ascii=False` 当 JSON-encoding Chinese text
- PyPI mirror: `https://mirrors.aliyun.com/pypi/simple/`

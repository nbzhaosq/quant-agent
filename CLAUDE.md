# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered quantitative investment analysis agent for A-share (Chinese) stocks, built with Claude Agent SDK and Tushare data API. Features multi-agent collaboration with GraphRAG knowledge graph support.

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run quant-agent chat                        # Interactive chat
uv run quant-agent analyze 600519.SH           # Single agent analysis
uv run quant-agent team-analyze 600519.SH      # Multi-agent team analysis (recommended)
uv run quant-agent search 茅台                  # Search stocks
uv run quant-agent mcp "茅台相关新闻" --category 新闻  # Semantic search

# Testing
uv run pytest
uv run pytest tests/unit/test_tools.py -v  # Single test file

# Linting & Type Checking
uv run ruff check .
uv run ruff check . --fix  # Auto-fix
uv run ruff format .       # Format
uv run mypy src/
```

## Architecture

```
src/quant_agent/
├── core/
│   ├── agent.py        # QuantAgent - single agent mode
│   ├── coordinator.py  # QuantCoordinator - multi-agent orchestration
│   └── config.py       # Settings via pydantic-settings
├── agents/
│   ├── base.py              # SubAgentBase - base class for sub-agents
│   ├── technical.py         # Technical analysis expert
│   ├── fundamental.py       # Fundamental analysis expert
│   ├── sentiment.py         # Sentiment analysis expert
│   ├── risk.py              # Risk assessment expert
│   └── report_generator.py  # Report synthesis expert
├── knowledge/
│   ├── graphiti_client.py   # Graphiti knowledge graph client
│   ├── glm_llm_client.py    # GLM LLM client for Graphiti
│   ├── vector_store.py      # SQLite + sqlite-vec vector store
│   └── entities.py          # Custom entity types
├── tools/
│   └── mcp_tools.py         # MCP tools using @tool decorator
├── data/
│   └── tushare_client.py    # Tushare API wrapper
├── utils/
│   ├── logging_config.py    # Logging setup
│   ├── helpers.py           # Utility functions
│   └── report.py            # Report formatting
└── cli.py                   # Typer CLI entry point
```

## Key Technologies

- **Claude Agent SDK** (`claude-agent-sdk`) - Uses Claude Code auth, no API key needed
- **Multi-Agent System** - 5 specialized agents (technical, fundamental, sentiment, risk, report)
- **GraphRAG** - Graphiti + Neo4j for knowledge graph
- **Vector Search** - sqlite-vec for semantic search
- **LLM Flexibility** - Supports GLM, OpenAI, and other OpenAI-compatible APIs

## Adding Tools

Use `@tool` decorator in `mcp_tools.py`:

```python
from claude_agent_sdk import tool

@tool("tool_name", "description", {"param": str, "optional": int | None})
async def tool_handler(args: dict) -> dict:
    result = process(args["param"])
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
```

## Environment Variables

### Required
- `TUSHARE_TOKEN` - Tushare Pro API token (https://tushare.pro)

### For Claude Agent (QuantAgent)
- `ANTHROPIC_BASE_URL` - API base URL (supports OpenAI-compatible APIs)
- `ANTHROPIC_API_KEY` - API key
- `ANTHROPIC_MODEL` - Model name (e.g., `claude-sonnet-4-20250514`, `glm-5`)

### For Graphiti (Knowledge Graph)
- `NEO4J_URI` - Neo4j connection (default: `bolt://localhost:7687`)
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password
- `GRAPHITI_LLM_MODEL` - LLM model for entity extraction
- `GRAPHITI_LLM_BASE_URL` - LLM API base URL
- `EMBEDDING_MODEL` - Embedding model name
- `EMBEDDING_BASE_URL` - Embedding API base URL
- `EMBEDDING_DIMENSION` - Embedding dimension

> Note: Claude Agent SDK uses Claude Code's authentication automatically - no ANTHROPIC_API_KEY needed for the agent itself.

## GLM LLM Client

The `glm_llm_client.py` handles GLM-specific response formats:
- Extracts content from `reasoning_content` when main content is empty
- Handles markdown code blocks in JSON responses
- Normalizes field names for entity/edge extraction
- Converts list responses to expected dict format

## Workflow

1. **Request** → Coordinator receives analysis request
2. **Context** → Query GraphRAG for historical context
3. **Parallel Analysis** → 4 agents analyze simultaneously (technical, fundamental, sentiment, risk)
4. **Aggregation** → Collect all agent results
5. **Report** → ReportGenerator creates comprehensive report
6. **Storage** → Save results to knowledge graph

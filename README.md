# Quant Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://docs.astral.sh/ruff/)

AI-powered quantitative investment analysis agent for Chinese A-share markets, built with Claude Agent SDK, multi-agent collaboration, and GraphRAG.

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Features

#### Core Capabilities
- **Data Acquisition**: A-share market data via Tushare (quotes, financials, capital flows)
- **Technical Analysis**: MA, MACD, RSI, KDJ, volatility indicators
- **Fundamental Analysis**: Financial statements, valuation metrics, industry analysis
- **Sentiment Analysis**: News sentiment, market mood monitoring
- **Risk Assessment**: Volatility, VaR, risk level evaluation

#### Advanced Features
- **Multi-Agent Collaboration**: 5 specialized agents working in parallel
- **GraphRAG**: Knowledge graph enhanced retrieval with Graphiti
- **Vector Search**: Semantic search with sqlite-vec
- **Knowledge Accumulation**: Persistent storage of analysis results
- **Flexible LLM**: Supports GLM, OpenAI, and other OpenAI-compatible APIs

### Quick Start

#### 1. Install Dependencies

```bash
uv sync
```

#### 2. Start Neo4j (required for Graphiti)

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

#### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

| Variable | Description | Required |
|----------|-------------|----------|
| `TUSHARE_TOKEN` | Tushare API Token | ✅ |
| `ANTHROPIC_BASE_URL` | LLM API URL | ✅ |
| `ANTHROPIC_API_KEY` | LLM API Key | ✅ |
| `ANTHROPIC_MODEL` | Model name (e.g., `glm-5`, `claude-sonnet-4-20250514`) | ✅ |
| `NEO4J_URI` | Neo4j connection | GraphRAG |
| `NEO4J_PASSWORD` | Neo4j password | GraphRAG |

#### 4. Run

```bash
# Interactive chat
uv run quant-agent chat

# Analyze specific stock
uv run quant-agent analyze 600519.SH

# Multi-agent team analysis (recommended)
uv run quant-agent team-analyze 600519.SH

# Search stocks
uv run quant-agent search 茅台

# Debug mode
uv run quant-agent team-analyze 600519.SH --log-level DEBUG
```

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  CLI Layer (cli.py)                  │
├─────────────────────────────────────────────────────┤
│            Coordinator (QuantCoordinator)            │
├─────────────────────────────────────────────────────┤
│                  Sub-Agent Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  Technical  │ │ Fundamental │ │  Sentiment  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐                    │
│  │    Risk     │ │   Report    │                    │
│  └─────────────┘ └─────────────┘                    │
├─────────────────────────────────────────────────────┤
│              Tool Layer (MCP Tools)                  │
├─────────────────────────────────────────────────────┤
│                   Data Layer                         │
│  Tushare API | Neo4j + Graphiti | SQLite + sqlite-vec│
└─────────────────────────────────────────────────────┘
```

### Development

```bash
# Run tests
uv run pytest

# Linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/
```

### Disclaimer

⚠️ **All analysis is for reference only and does not constitute investment advice.**

---

<a name="中文"></a>
## 中文

### 功能特性

#### 核心功能
- **数据获取**：通过 Tushare 获取 A 股行情、财务、资金流数据
- **技术分析**：MA、MACD、RSI、KDJ、波动率等技术指标
- **基本面分析**：财务报表、估值指标、行业分析
- **情绪分析**：新闻舆情、市场情绪监测
- **风险评估**：波动率、VaR、风险等级评估

#### 高级特性
- **多 Agent 协作**：5 个专业分析 Agent 并行工作
- **GraphRAG**：基于 Graphiti 的知识图谱增强检索
- **向量搜索**：sqlite-vec 语义搜索
- **知识积累**：分析结果持久化存储
- **灵活 LLM**：支持 GLM、OpenAI 等多种 API

### 快速开始

#### 1. 安装依赖

```bash
uv sync
```

#### 2. 启动 Neo4j (Graphiti 需要)

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

#### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

| 变量 | 说明 | 必需 |
|------|------|------|
| `TUSHARE_TOKEN` | Tushare API Token | ✅ |
| `ANTHROPIC_BASE_URL` | LLM API 地址 | ✅ |
| `ANTHROPIC_API_KEY` | LLM API Key | ✅ |
| `ANTHROPIC_MODEL` | 模型名称 (如 `glm-5`, `claude-sonnet-4-20250514`) | ✅ |
| `NEO4J_URI` | Neo4j 连接地址 | GraphRAG 需要 |
| `NEO4J_PASSWORD` | Neo4j 密码 | GraphRAG 需要 |

> **提示**：Tushare Token 在 https://tushare.pro 注册获取

#### 4. 运行

```bash
# 交互式对话
uv run quant-agent chat

# 分析指定股票
uv run quant-agent analyze 600519.SH

# 多 Agent 团队分析 (推荐)
uv run quant-agent team-analyze 600519.SH

# 搜索股票
uv run quant-agent search 茅台

# 调试模式
uv run quant-agent team-analyze 600519.SH --log-level DEBUG
```

### 架构

```
┌─────────────────────────────────────────────────────┐
│                  CLI Layer (cli.py)                  │
├─────────────────────────────────────────────────────┤
│            Coordinator (QuantCoordinator)            │
│  - 任务分解  - Agent 调度  - 结果聚合                │
├─────────────────────────────────────────────────────┤
│                  Sub-Agent Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  Technical  │ │ Fundamental │ │  Sentiment  │   │
│  │  Analyst    │ │   Analyst   │ │   Analyst   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐                    │
│  │    Risk     │ │   Report    │                    │
│  │  Assessor   │ │  Generator  │                    │
│  └─────────────┘ └─────────────┘                    │
├─────────────────────────────────────────────────────┤
│              Tool Layer (MCP Tools)                  │
│  - tushare_* 工具  - calculate_* 工具                │
├─────────────────────────────────────────────────────┤
│                   Data Layer                         │
│  Tushare API | Neo4j + Graphiti | SQLite + sqlite-vec│
└─────────────────────────────────────────────────────┘
```

### 开发

```bash
# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run ruff format .

# 类型检查
uv run mypy src/
```

### 注意事项

- ⚠️ **所有分析仅供参考，不构成投资建议**
- Tushare 部分接口需要积分，可在官网获取
- Neo4j 需要独立运行（Docker 或本地安装）
- 确保 `.env` 文件不被提交到版本控制

## License

MIT

# Quant Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://docs.astral.sh/ruff/)

AI 驱动的 A 股量化投资分析助手，基于 Claude Agent SDK，支持多 Agent 协作和 GraphRAG。

[English](#english) | [中文](#中文)

## 功能特性

### 核心功能
- **数据获取**：通过 Tushare 获取 A 股行情、财务、资金流数据
- **技术分析**：MA、MACD、RSI、KDJ、波动率等技术指标
- **基本面分析**：财务报表、估值指标、行业分析
- **情绪分析**：新闻舆情、市场情绪监测
- **风险评估**：波动率、VaR、风险等级评估

### 高级特性
- **多 Agent 协作**：5 个专业分析 Agent 并行工作
- **GraphRAG**：基于 Graphiti 的知识图谱增强检索
- **向量搜索**：sqlite-vec 语义搜索
- **知识积累**：分析结果持久化存储
- **灵活 LLM**：支持 GLM、OpenAI 等多种 API

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 启动 Neo4j (Graphiti 需要)

```bash
# 使用 Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### 3. 配置环境变量

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
| `NEO4J_USER` | Neo4j 用户名 | GraphRAG 需要 |
| `NEO4J_PASSWORD` | Neo4j 密码 | GraphRAG 需要 |
| `GRAPHITI_LLM_MODEL` | Graphiti 使用的 LLM 模型 | GraphRAG 需要 |
| `GRAPHITI_LLM_BASE_URL` | Graphiti LLM API 地址 | GraphRAG 需要 |
| `EMBEDDING_MODEL` | Embedding 模型 | GraphRAG 需要 |
| `EMBEDDING_BASE_URL` | Embedding API 地址 | GraphRAG 需要 |
| `EMBEDDING_DIMENSION` | Embedding 维度 | GraphRAG 需要 |

> **提示**：
> - Tushare Token 在 https://tushare.pro 注册获取
> - 支持 GLM、DeepSeek 等 OpenAI 兼容 API
> - Graphiti 需要独立的 LLM 和 Embedding API（可使用 OpenAI）

### 4. 运行

```bash
# 单 Agent 模式 - 交互式对话
uv run quant-agent chat

# 单 Agent 模式 - 分析指定股票
uv run quant-agent analyze 600519.SH

# 搜索股票
uv run quant-agent search 茅台

# 多 Agent 团队分析 (推荐)
uv run quant-agent team-analyze 600519.SH

# 语义搜索
uv run quant-agent mcp "茅台相关新闻" --category 新闻

# 调试模式
uv run quant-agent team-analyze 600519.SH --log-level DEBUG
```

## 项目结构

```
quant-agent/
├── src/quant_agent/
│   ├── core/
│   │   ├── coordinator.py    # QuantCoordinator - 多 Agent 协调器
│   │   ├── agent.py          # QuantAgent - 单 Agent 模式
│   │   └── config.py         # 配置管理
│   ├── knowledge/
│   │   ├── graphiti_client.py # Graphiti 知识图谱客户端
│   │   ├── glm_llm_client.py  # GLM LLM 客户端 (处理 GLM 特殊格式)
│   │   ├── vector_store.py    # SQLite + sqlite-vec 向量存储
│   │   └── entities.py        # 自定义实体类型
│   ├── agents/
│   │   ├── base.py            # SubAgentBase 基类
│   │   ├── technical.py       # 技术指标分析专家
│   │   ├── fundamental.py     # 基本面分析专家
│   │   ├── sentiment.py       # 情绪分析专家
│   │   ├── risk.py            # 风险评估专家
│   │   └── report_generator.py # 综合报告生成专家
│   ├── tools/
│   │   └── mcp_tools.py       # MCP 工具定义
│   ├── data/
│   │   └── tushare_client.py  # Tushare API 客户端
│   ├── utils/
│   │   ├── logging_config.py  # 日志配置
│   │   ├── helpers.py         # 工具函数
│   │   └── report.py          # 报告格式化
│   └── cli.py                 # Typer CLI 入口
├── data/                      # SQLite 数据库存储
├── tests/
├── pyproject.toml
├── CLAUDE.md                  # Claude Code 开发指南
└── README.md
```

## 架构

### 多 Agent 架构

```
┌─────────────────────────────────────────────────────┐
│                  CLI Layer (cli.py)                  │
├─────────────────────────────────────────────────────┤
│            Coordinator (QuantCoordinator)            │
│  - 任务分解                                          │
│  - Agent 调度                                        │
│  - 结果聚合                                          │
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
│  - tushare_* 工具 (行情/财务/资金流)                 │
│  - calculate_* 工具 (技术指标计算)                   │
├─────────────────────────────────────────────────────┤
│                   Data Layer                         │
│  - Tushare API (行情/财务数据)                       │
│  - Neo4j + Graphiti (知识图谱)                       │
│  - SQLite + sqlite-vec (向量存储)                    │
└─────────────────────────────────────────────────────┘
```

### 工作流程

1. **接收请求**：Coordinator 接收分析请求
2. **上下文增强**：查询 GraphRAG 获取历史上下文
3. **并行分析**：4 个专业 Agent 并行执行分析
4. **结果聚合**：汇总各 Agent 分析结果
5. **报告生成**：ReportGenerator 生成综合报告
6. **知识存储**：将结果存储到知识图谱

### GLM 集成

`glm_llm_client.py` 处理 GLM API 的特殊响应格式：
- 从 `reasoning_content` 提取内容（当 `content` 为空时）
- 处理 JSON 中的 markdown 代码块
- 规范化实体/边提取的字段名
- 将列表响应转换为期望的字典格式

## 开发

### 运行测试

```bash
uv run pytest                              # 运行所有测试
uv run pytest tests/unit/test_tools.py -v  # 单个测试文件
uv run pytest -k "test_ma" -v              # 匹配模式
```

### 代码检查

```bash
uv run ruff check .              # 检查 lint 错误
uv run ruff check . --fix        # 自动修复
uv run ruff format .             # 格式化
uv run mypy src/                 # 类型检查
```

### 添加新工具

在 `src/quant_agent/tools/mcp_tools.py` 中：

```python
from claude_agent_sdk import tool

@tool(
    "my_tool",
    "工具描述",
    {"param1": str, "param2": int | None},
)
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    result = process(args["param1"])
    return {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]
    }
```

然后在 `create_quant_mcp_server()` 中注册。

## 注意事项

- ⚠️ **所有分析仅供参考，不构成投资建议**
- Tushare 部分接口需要积分，可在官网获取
- Neo4j 需要独立运行（Docker 或本地安装）
- 确保 `.env` 文件不被提交到版本控制
- 使用 GLM API 时需要配置 `glm_llm_client.py` 处理特殊格式

## License

MIT

# Contributing to Quant Agent

感谢你有兴趣为 Quant Agent 做出贡献！

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/quant-agent.git
cd quant-agent

# 安装依赖
uv sync

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入你的 API keys

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run mypy src/
```

## 代码规范

- 使用 Python 3.12+
- 遵循 PEP 8 规范
- 使用 `ruff format` 格式化代码
- 添加类型注解，通过 `mypy --strict` 检查
- 为新功能添加测试

## 提交代码

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### Commit 消息规范

使用约定式提交：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 添加新工具

在 `src/quant_agent/tools/mcp_tools.py` 中：

```python
from claude_agent_sdk import tool

@tool(
    "tool_name",
    "工具描述",
    {"param1": str, "param2": int | None},
)
async def tool_handler(args: dict[str, Any]) -> dict[str, Any]:
    # 实现逻辑
    return {"content": [{"type": "text", "text": result}]}
```

## 添加新 Agent

1. 在 `src/quant_agent/agents/` 创建新文件
2. 继承 `SubAgentBase` 基类
3. 在 `QuantCoordinator` 中注册

## 问题反馈

- 使用 GitHub Issues 报告 Bug
- 提供复现步骤和环境信息
- 标注适当的标签 (bug, enhancement, question)

## 许可证

提交代码即表示你同意你的贡献将在 MIT 许可证下授权。

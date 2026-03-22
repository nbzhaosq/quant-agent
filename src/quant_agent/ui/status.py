"""Status display components for multi-agent team analysis."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table
from rich.text import Text


class AnalysisStage(Enum):
    INIT = "init"
    PARSING = "parsing"
    GRAPH_RAG = "graph_rag"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    REPORT = "report"
    STORING = "storing"
    DONE = "done"


STAGE_INFO: dict[AnalysisStage, dict[str, str]] = {
    AnalysisStage.INIT: {"name": "初始化", "icon": "🚀", "color": "blue"},
    AnalysisStage.PARSING: {"name": "解析请求", "icon": "📝", "color": "yellow"},
    AnalysisStage.GRAPH_RAG: {"name": "查询历史上下文", "icon": "🔍", "color": "cyan"},
    AnalysisStage.TECHNICAL: {"name": "技术分析", "icon": "📈", "color": "green"},
    AnalysisStage.FUNDAMENTAL: {"name": "基本面分析", "icon": "📊", "color": "blue"},
    AnalysisStage.SENTIMENT: {"name": "情绪分析", "icon": "🎭", "color": "magenta"},
    AnalysisStage.RISK: {"name": "风险评估", "icon": "⚠️", "color": "red"},
    AnalysisStage.REPORT: {"name": "生成报告", "icon": "📋", "color": "yellow"},
    AnalysisStage.STORING: {"name": "存储结果", "icon": "💾", "color": "dim"},
    AnalysisStage.DONE: {"name": "完成", "icon": "✅", "color": "green"},
}


@dataclass
class AgentStatus:
    role: str
    status: str = "pending"
    progress: float = 0.0
    message: str = ""
    result_summary: str = ""
    confidence: float = 0.0
    error: str = ""


@dataclass
class TeamAnalysisState:
    user_input: str = ""
    parsed_prompt: str = ""
    stock_code: str = ""
    current_stage: AnalysisStage = AnalysisStage.INIT
    stage_message: str = ""
    agents: dict[str, AgentStatus] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    logs: list[str] = field(default_factory=list)

    def add_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 50:
            self.logs = self.logs[-50:]


class TeamStatusDisplay:
    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.state = TeamAnalysisState()
        self._live: Live | None = None
        self._progress: Progress | None = None
        self._main_task: TaskID | None = None
        self._agent_tasks: dict[str, TaskID] = {}
        self._callbacks: list[Callable[[str, dict[str, Any]], None]] = []

    def on_event(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        self._callbacks.append(callback)

    def emit(self, event: str, data: dict[str, Any]) -> None:
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def start(self, user_input: str) -> None:
        self.state = TeamAnalysisState(user_input=user_input)
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )
        self._main_task = self._progress.add_task("[cyan]分析进度[/cyan]", total=100)
        for role in ["technical", "fundamental", "sentiment", "risk"]:
            self.state.agents[role] = AgentStatus(role=role)
            task_id = self._progress.add_task(f"  {role}", total=100, visible=False)
            self._agent_tasks[role] = task_id
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=4,
            transient=False,
        )
        self._live.start()
        self._log(f"开始分析: {user_input[:50]}...")

    def stop(self) -> None:
        if self._live:
            self._live.stop()
            self._live = None

    def _log(self, message: str) -> None:
        self.state.add_log(message)
        self.emit("log", {"message": message})
        self._refresh()

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    def set_stage(self, stage: AnalysisStage, message: str = "") -> None:
        self.state.current_stage = stage
        self.state.stage_message = message
        info = STAGE_INFO.get(stage, {})
        stage_name = info.get("name", stage.value)
        self._log(
            f"{info.get('icon', '▶')} {stage_name}: {message}"
            if message
            else f"{info.get('icon', '▶')} {stage_name}"
        )
        stage_progress = {
            AnalysisStage.INIT: 5,
            AnalysisStage.PARSING: 10,
            AnalysisStage.GRAPH_RAG: 15,
            AnalysisStage.TECHNICAL: 30,
            AnalysisStage.FUNDAMENTAL: 45,
            AnalysisStage.SENTIMENT: 60,
            AnalysisStage.RISK: 75,
            AnalysisStage.REPORT: 90,
            AnalysisStage.STORING: 95,
            AnalysisStage.DONE: 100,
        }
        if self._progress and self._main_task is not None:
            self._progress.update(self._main_task, completed=stage_progress.get(stage, 0))
        self._refresh()

    def set_parsed_prompt(self, prompt: str, stock_code: str) -> None:
        self.state.parsed_prompt = prompt
        self.state.stock_code = stock_code
        self._log(f"股票代码: {stock_code}")
        self._refresh()

    def update_agent(
        self,
        role: str,
        status: str,
        progress: float = 0.0,
        message: str = "",
        result_summary: str = "",
        confidence: float = 0.0,
        error: str = "",
    ) -> None:
        if role not in self.state.agents:
            self.state.agents[role] = AgentStatus(role=role)
        agent = self.state.agents[role]
        agent.status = status
        agent.progress = progress
        agent.message = message
        agent.result_summary = result_summary
        agent.confidence = confidence
        agent.error = error
        if self._progress and role in self._agent_tasks:
            self._progress.update(
                self._agent_tasks[role],
                visible=True,
                completed=int(progress),
                description=f"  {role}: {message}" if message else f"  {role}",
            )
        self.emit("agent_update", {"role": role, "status": status, "progress": progress})
        self._refresh()

    def agent_started(self, role: str) -> None:
        self.update_agent(role, status="running", progress=0, message="启动中...")
        self._log(f"🤖 {role} agent 开始工作")

    def agent_progress(self, role: str, progress: float, message: str = "") -> None:
        self.update_agent(role, status="running", progress=progress, message=message)

    def agent_completed(self, role: str, result_summary: str, confidence: float) -> None:
        self.update_agent(
            role,
            status="completed",
            progress=100,
            message="完成",
            result_summary=result_summary,
            confidence=confidence,
        )
        self._log(f"✅ {role} agent 完成 (置信度: {confidence:.0%})")

    def agent_failed(self, role: str, error: str) -> None:
        self.update_agent(role, status="failed", progress=0, message="失败", error=error)
        self._log(f"❌ {role} agent 失败: {error}")

    def _render(self) -> Group:
        elements = []
        header = Table.grid(padding=(0, 2))
        header.add_column(style="bold cyan", width=12)
        header.add_column()
        elapsed = time.time() - self.state.start_time
        header.add_row("股票代码:", self.state.stock_code or "解析中...")
        header.add_row("当前阶段:", self._format_stage())
        header.add_row("耗时:", f"{elapsed:.1f}s")
        elements.append(
            Panel(
                header,
                title="[bold]📊 投研团队分析状态[/bold]",
                border_style="cyan",
            )
        )
        if self.state.parsed_prompt:
            prompt_display = self.state.parsed_prompt
            if len(prompt_display) > 200:
                prompt_display = prompt_display[:200] + "..."
            elements.append(
                Panel(
                    prompt_display,
                    title="[bold]📝 分析指令[/bold]",
                    border_style="yellow",
                )
            )
        if self._progress:
            elements.append(
                Panel(self._progress, title="[bold]⏳ 进度[/bold]", border_style="green")
            )
        agents_table = Table.grid(padding=(0, 2))
        agents_table.add_column(width=15)
        agents_table.add_column(width=10)
        agents_table.add_column()
        agents_table.add_column(width=8)
        for role, agent in self.state.agents.items():
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
            }.get(agent.status, "❓")
            status_color = {
                "pending": "dim",
                "running": "yellow",
                "completed": "green",
                "failed": "red",
            }.get(agent.status, "white")
            confidence_str = (
                f"[{status_color}]{agent.confidence:.0%}[/{status_color}]"
                if agent.confidence > 0
                else ""
            )
            agents_table.add_row(
                f"[bold]{role}[/bold]",
                f"[{status_color}]{status_icon} {agent.status}[/{status_color}]",
                agent.message or agent.result_summary or "",
                confidence_str,
            )
        elements.append(
            Panel(
                agents_table,
                title="[bold]🤖 Agent 状态[/bold]",
                border_style="blue",
            )
        )
        if self.state.logs:
            logs_text = "\n".join(self.state.logs[-10:])
            elements.append(
                Panel(
                    logs_text,
                    title="[bold]📜 日志[/bold]",
                    border_style="dim",
                )
            )
        return Group(*elements)

    def _format_stage(self) -> Text:
        info = STAGE_INFO.get(self.state.current_stage, {})
        color = info.get("color", "white")
        icon = info.get("icon", "▶")
        name = info.get("name", self.state.current_stage.value)
        text = Text()
        text.append(f"{icon} ", style=color)
        text.append(name, style=f"bold {color}")
        if self.state.stage_message:
            text.append(f" - {self.state.stage_message}", style="dim")
        return text

    def get_final_summary(self) -> str:
        lines = []
        lines.append(f"股票: {self.state.stock_code}")
        elapsed = time.time() - self.state.start_time
        lines.append(f"分析耗时: {elapsed:.1f}s")
        lines.append("")
        lines.append("Agent 结果:")
        for role, agent in self.state.agents.items():
            if agent.status == "completed":
                lines.append(f"  ✅ {role}: {agent.confidence:.0%} 置信度")
            elif agent.status == "failed":
                lines.append(f"  ❌ {role}: 失败 - {agent.error}")
        return "\n".join(lines)

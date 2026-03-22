"""CLI interface for Quant Agent."""

import asyncio
import logging

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from quant_agent.core import QuantAgent
from quant_agent.core.coordinator import QuantCoordinator
from quant_agent.ui.status import TeamStatusDisplay, AnalysisStage
from quant_agent.utils.logging_config import setup_logging
from quant_agent.utils.report import generate_reports

app = typer.Typer(
    name="quant-agent",
    help="AI-powered quantitative investment analysis agent",
)
console = Console()

setup_logging()
logger = logging.getLogger(__name__)


@app.command()
def chat(
    stock: str | None = typer.Option(None, "--stock", "-s", help="Stock code to analyze"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
) -> None:
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    agent = QuantAgent()

    console.print(
        Panel.fit(
            "[bold green]Quant Agent[/bold green] - AI 量化投资分析助手\n"
            "输入问题开始分析，输入 'quit' 或 'exit' 退出",
            title="欢迎",
        )
    )

    if stock:
        initial_query = f"请分析 {stock} 这只股票"
        console.print(f"\n[blue]User:[/blue] {initial_query}")
        logger.info(f"分析请求: {stock}")
        response = agent.chat(initial_query)
        console.print(f"\n[green]Agent:[/green]")
        console.print(Markdown(response))

    while True:
        try:
            user_input = Prompt.ask("\n[blue]You[/blue]")

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]再见！[/yellow]")
                break

            if not user_input.strip():
                continue
            logger.info(f"用户输入: {user_input[:50]}...")
            response = agent.chat(user_input)
            console.print(f"\n[green]Agent:[/green]")
            console.print(Markdown(response))
        except KeyboardInterrupt:
            console.print("\n[yellow]再见![/yellow]")
            break
        except Exception as e:
            logger.error(f"错误: {e}")
            console.print(f"[red]错误: {e}[/red]")


@app.command()
def analyze(
    stock: str = typer.Argument(..., help="Stock code or name"),
    report: str = typer.Option(
        "summary", "--report", "-r", help="Report type: summary, technical, fundamental"
    ),
    days: int = typer.Option(120, "--days", "-d", help="Number of trading days to analyze"),
    debug: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Analyze a stock with AI-powered analysis."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Confirm analysis parameters
    if not yes:
        console.print(Panel.fit(
            f"[bold]分析参数确认[/bold]\n\n"
            f"股票代码: [cyan]{stock}[/cyan]\n"
            f"报告类型: [cyan]{report}[/cyan]\n"
            f"分析天数: [cyan]{days}[/cyan] 个交易日\n\n"
            f"是否开始分析?",
            title="确认",
        ))
        confirm = Prompt.ask("确认开始?", choices=["y", "n"], default="y")
        if confirm.lower() != "y":
            console.print("[yellow]已取消分析[/yellow]")
            return

    agent = QuantAgent()
    if report == "technical":
        query = f"请对 {stock} 进行技术分析，包括均线、MACD、RSI等指标，分析最近{days}个交易日的数据"
    elif report == "fundamental":
        query = f"请对 {stock} 进行基本面分析,包括财务数据、估值等"
    else:
        query = f"请全面分析 {stock}，包括技术面和基本面，分析最近{days}个交易日的数据"
    logger.info(f"开始分析: {stock} (报告类型: {report})")
    console.print(f"[blue]正在分析 {stock}...[/blue]")
    response = agent.chat(query)
    console.print(Markdown(response))


@app.command()
def search(keyword: str = typer.Argument(..., help="Stock name or code to search")) -> None:
    agent = QuantAgent()
    logger.info(f"搜索股票: {keyword}")
    response = agent.chat(f"搜索股票：{keyword}")
    console.print(Markdown(response))


def _format_team_result(result: dict) -> str:
    lines = [f"# 综合分析报告: {result.get('stock_code', 'Unknown')}"]
    lines.append(f"\n**分析时间**: {result.get('timestamp', 'N/A')}")
    lines.append("\n---\n")
    for agent_result in result.get("results", []):
        role = agent_result.get("agent_role", "unknown")
        summary = agent_result.get("summary", "No summary")
        confidence = agent_result.get("confidence", 0)
        lines.append(f"\n## {role.upper()}\n")
        lines.append(f"{summary}\n")
        lines.append(f"*置信度*: {confidence:.0%}\n")
    if result.get("final_report"):
        lines.append("\n---\n")
        lines.append("\n## 最终报告\n")
        lines.append(result["final_report"].get("summary", ""))
    return "\n".join(lines)


@app.command("team-analyze")
def team_analyze(
    stock: str = typer.Argument(..., help="Stock code or name"),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text, json"),
    days: int = typer.Option(120, "--days", "-d", help="Number of trading days to analyze"),
    debug: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    no_status: bool = typer.Option(False, "--no-status", help="Disable status display"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Multi-agent team analysis with comprehensive reports."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Confirm analysis parameters
    if not yes:
        console.print(Panel.fit(
            f"[bold]多Agent分析参数确认[/bold]\n\n"
            f"股票代码: [cyan]{stock}[/cyan]\n"
            f"分析天数: [cyan]{days}[/cyan] 个交易日\n"
            f"输出格式: [cyan]{output}[/cyan]\n\n"
            f"将启动技术分析、基本面分析、情绪分析、风险评估等多个Agent",
            title="确认",
        ))
        confirm = Prompt.ask("确认开始?", choices=["y", "n"], default="y")
        if confirm.lower() != "y":
            console.print("[yellow]已取消分析[/yellow]")
            return

    status_display = None if no_status else TeamStatusDisplay(console)
    coordinator = QuantCoordinator(days=days)

    def progress_callback(event: str, data: dict) -> None:
        if status_display:
            if event == "stage":
                stage = AnalysisStage(data.get("stage", "init"))
                status_display.set_stage(stage, data.get("message", ""))
            elif event == "parsed_prompt":
                status_display.set_parsed_prompt(data.get("prompt", ""), data.get("stock_code", ""))
            elif event == "agent_start":
                status_display.agent_started(data.get("role", "unknown"))
            elif event == "agent_progress":
                status_display.agent_progress(
                    data.get("role", "unknown"),
                    data.get("progress", 0),
                    data.get("message", ""),
                )
            elif event == "agent_complete":
                status_display.agent_completed(
                    data.get("role", "unknown"),
                    data.get("summary", ""),
                    data.get("confidence", 0),
                )
            elif event == "agent_error":
                status_display.agent_failed(
                    data.get("role", "unknown"), data.get("error", "Unknown error")
                )

    coordinator.set_progress_callback(progress_callback)

    try:
        if status_display:
            status_display.start(stock)
        else:
            console.print(f"[blue]正在启动多 Agent 团队分析 {stock}...[/blue]")

        result = asyncio.run(coordinator.analyze(stock))

        if status_display:
            status_display.set_stage(AnalysisStage.DONE, "分析完成")
            status_display.stop()

        if output == "json":
            import json

            console.print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            report_paths = generate_reports(result)
            _print_summary(console, result, report_paths)

    except Exception as e:
        if status_display:
            status_display.stop()
        logger.error(f"分析失败: {e}")
        console.print(f"[red]分析失败: {e}[/red]")
    finally:
        if status_display:
            status_display.stop()


def _print_summary(console: Console, result: dict, report_paths: dict[str, str]) -> None:
    stock_code = result.get("stock_code", "Unknown")
    final_report = result.get("final_report", {})

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]分析完成[/bold green]\n\n"
            f"股票代码: {stock_code}\n"
            f"综合建议: {final_report.get('details', {}).get('recommendation', 'N/A')}\n"
            f"风险等级: {final_report.get('details', {}).get('risk_level', 'N/A')}\n"
            f"置信度: {final_report.get('confidence', 0):.0%}",
            title="分析概要",
        )
    )

    console.print()
    console.print("[bold]报告文件:[/bold]")
    console.print(f"  Markdown: {report_paths['markdown']}")
    console.print(f"  HTML:     {report_paths['html']}")
    console.print()


@app.command()
def mcp(
    query: str = typer.Argument(..., help="Semantic search query"),
    category: str | None = typer.Option(
        None, "--category", "-c", help="Search category ( optional)"
    ),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
) -> None:
    console.print(f"[blue]正在搜索: {query}...[/blue]")
    agent = QuantAgent()
    search_query = f"搜索: {query}"
    if category:
        search_query += f" 分类: {category}"
    response = agent.chat(search_query)
    console.print(Markdown(response))


@app.command()
def version() -> None:
    from quant_agent import __version__

    console.print(f"quant-agent version {__version__}")


if __name__ == "__main__":
    app()

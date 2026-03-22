"""Report generator utility - generates markdown and HTML reports."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from quant_agent.agents.base import AgentRole


def generate_reports(
    result: dict[str, Any],
    output_dir: str = "report",
) -> dict[str, str]:
    stock_code = result.get("stock_code", "unknown")
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H%M%S")

    stock_dir = Path(output_dir) / stock_code
    stock_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"analysis-{date_str}-{time_str}"
    md_path = stock_dir / f"{base_name}.md"
    html_path = stock_dir / f"{base_name}.html"

    md_content = _generate_markdown(result, timestamp)
    html_content = _generate_html(result, timestamp)

    md_path.write_text(md_content, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")

    return {"markdown": str(md_path), "html": str(html_path)}


def _generate_markdown(result: dict[str, Any], timestamp: datetime) -> str:
    stock_code = result.get("stock_code", "Unknown")
    context = result.get("context", {})
    fact_count = context.get("fact_count", 0) if context else 0

    lines = [
        f"# 投资分析报告",
        "",
        f"**股票代码**: {stock_code}",
        f"**生成时间**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**数据来源**: Tushare API, Graphiti",
        f"**历史记录**: {fact_count} 条" if fact_count else "**历史记录**: 无",
        "",
        "---",
        "",
    ]

    agent_results = result.get("results", [])
    role_names = {
        "technical": "技术面分析",
        "fundamental": "基本面分析",
        "sentiment": "情绪面分析",
        "risk": "风险评估",
        "report": "综合报告",
    }

    for agent_result in agent_results:
        role = agent_result.get("agent_role", "unknown")
        summary = agent_result.get("summary", "无摘要")
        confidence = agent_result.get("confidence", 0)
        details = agent_result.get("details", {})
        raw_response = agent_result.get("raw_response", "")
        errors = agent_result.get("errors", [])
        role_title = role_names.get(role, role.upper())
        lines.extend(
            [
                f"## {role_title}",
                "",
                f"**置信度**: {confidence:.0%}",
                "",
            ]
        )
        if details:
            lines.append("### 关键指标")
            lines.append("")
            for key, value in details.items():
                if isinstance(value, dict):
                    lines.append(f"- **{key}**:")
                    for k, v in value.items():
                        lines.append(f"  - {k}: {v}")
                elif isinstance(value, list):
                    lines.append(f"- **{key}**: {', '.join(map(str, value))}")
                else:
                    lines.append(f"- **{key}**: {value}")
            lines.append("")
        if raw_response:
            lines.extend(
                [
                    "### 详细分析",
                    "",
                    "```",
                    raw_response,
                    "```",
                    "",
                ]
            )
        if errors:
            lines.extend(
                [
                    "### 错误信息",
                    "",
                ]
            )
            for err in errors:
                lines.append(f"- {err}")
            lines.append("")
        lines.extend(["---", ""])
    final_report = result.get("final_report")
    if final_report:
        lines.extend(
            [
                "## 综合结论",
                "",
            ]
        )
        summary = final_report.get("summary", "")
        if summary:
            lines.append(summary)
            lines.append("")
        details = final_report.get("details", {})
        if details:
            lines.append("### 综合评估")
            lines.append("")
            for key, value in details.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        raw_response = final_report.get("raw_response", "")
        if raw_response:
            lines.extend(
                [
                    "### 完整报告",
                    "",
                    "```",
                    raw_response,
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "---",
            "",
            "> 本报告由 Quant Agent 生成，仅供参考，不构成投资建议。",
        ]
    )
    return "\n".join(lines)


def _generate_html(result: dict[str, Any], timestamp: datetime) -> str:
    stock_code = result.get("stock_code", "Unknown")
    context = result.get("context", {})
    fact_count = context.get("fact_count", 0) if context else 0
    price_data = result.get("price_data", [])

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>投资分析报告 - {stock_code}</title>",
        "<style>",
        _get_html_styles(),
        "</style>",
        "</head>",
        "<body>",
        '<div class="container">',
        f"<h1>投资分析报告: {stock_code}</h1>",
        f'<p class="meta">生成时间: {timestamp.strftime("%Y-%m-%d %H:%M:%S")} | 数据来源: Tushare API | 历史记录: {fact_count} 条</p>',
        "<hr>",
    ]

    # Add price chart if data available
    if price_data:
        html_parts.extend(_generate_chart_section(stock_code, price_data))

    agent_results = result.get("results", [])
    role_colors = {
        "technical": "#3498db",
        "fundamental": "#27ae60",
        "sentiment": "#e74c3c",
        "risk": "#e74c3c",
        "report": "#2ecc71",
    }
    role_names = {
        "technical": "技术面分析",
        "fundamental": "基本面分析",
        "sentiment": "情绪面分析",
        "risk": "风险评估",
        "report": "综合报告",
    }
    for agent_result in agent_results:
        role = agent_result.get("agent_role", "unknown")
        summary = agent_result.get("summary", "无摘要")
        confidence = agent_result.get("confidence", 0)
        details = agent_result.get("details", {})
        raw_response = agent_result.get("raw_response", "")
        role_title = role_names.get(role, role.upper())
        role_color = role_colors.get(role, "#333")
        confidence_class = "high" if confidence >= 0.7 else "medium" if confidence >= 0.5 else "low"
        html_parts.extend(
            [
                '<div class="section">',
                f'<h2 style="border-color: {role_color}">{role_title}</h2>',
                f'<span class="confidence {confidence_class}">置信度: {confidence:.0%}</span>',
            ]
        )
        if details:
            html_parts.append('<div class="details">')
            html_parts.append("<h3>关键指标</h3>")
            html_parts.append("<ul>")
            for key, value in details.items():
                if isinstance(value, dict):
                    html_parts.append(f"<li><strong>{key}</strong>:")
                    html_parts.append("<ul>")
                    for k, v in value.items():
                        html_parts.append(f"<li>{k}: {v}</li>")
                    html_parts.append("</ul>")
                else:
                    html_parts.append(f"<li><strong>{key}</strong>: {value}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")
        if raw_response:
            html_parts.extend(
                [
                    '<div class="raw-response">',
                    "<h3>详细分析</h3>",
                    f'<div class="markdown-content" data-content="{_escape_html(raw_response)}"></div>',
                    "</div>",
                ]
            )
        html_parts.append("</div>")
    final_report = result.get("final_report")
    if final_report:
        html_parts.extend(
            [
                '<div class="section final">',
                "<h2>综合结论</h2>",
            ]
        )
        summary = final_report.get("summary", "")
        if summary:
            html_parts.append(
                f'<div class="markdown-content" data-content="{_escape_html(summary)}"></div>'
            )
        details = final_report.get("details", {})
        if details:
            html_parts.append("<ul>")
            for key, value in details.items():
                html_parts.append(f"<li><strong>{key}</strong>: {value}</li>")
            html_parts.append("</ul>")
        raw_response = final_report.get("raw_response", "")
        if raw_response:
            html_parts.append(
                f'<div class="markdown-content" data-content="{_escape_html(raw_response)}"></div>'
            )
        html_parts.append("</div>")
    html_parts.extend(
        [
            '<div class="footer">',
            "<p>本报告由 Quant Agent 生成，仅供参考，不构成投资建议。</p>",
            "</div>",
            "</div>",
            "<!-- Marked.js for markdown rendering -->",
            '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>',
            "<script>",
            "document.addEventListener('DOMContentLoaded', function() {",
            "    document.querySelectorAll('.markdown-content').forEach(function(el) {",
            "        const rawContent = el.getAttribute('data-content');",
            "        if (rawContent) {",
            "            el.innerHTML = marked.parse(rawContent);",
            "        }",
            "    });",
            "});",
            "</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(html_parts)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&#39;")
        .replace('"', "&quot;")
    )


def _generate_chart_section(stock_code: str, price_data: list[dict]) -> list[str]:
    """Generate lightweight-charts K-line section."""
    # Convert price data to candlestick format for lightweight-charts
    candlestick_data = []
    volume_data = []
    for item in price_data:
        if item.get("open") and item.get("high") and item.get("low") and item.get("close"):
            # Convert YYYYMMDD to YYYY-MM-DD format for lightweight-charts
            date_str = item["time"]
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            candlestick_data.append({
                "time": formatted_date,
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
            })
            if item.get("volume"):
                volume_data.append({
                    "time": formatted_date,
                    "value": item["volume"],
                    "color": "#26a69a" if item["close"] >= item["open"] else "#ef5350",
                })

    candlestick_json = json.dumps(candlestick_data, ensure_ascii=False)
    volume_json = json.dumps(volume_data, ensure_ascii=False)

    return [
        '<div class="section chart-section">',
        '<h2 style="border-color: #2196F3;">📈 K线图</h2>',
        f'<p class="chart-info">{stock_code} 日K线走势 (最近 {len(candlestick_data)} 个交易日)</p>',
        '<div id="price-chart" style="height: 400px; margin: 15px 0;"></div>',
        '<div id="volume-chart" style="height: 150px; margin: 15px 0;"></div>',
        '</div>',
        '<!-- Lightweight Charts -->',
        '<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>',
        '<script>',
        'document.addEventListener("DOMContentLoaded", function() {',
        '  const candlestickData = ' + candlestick_json + ';',
        '  const volumeData = ' + volume_json + ';',
        '  ',
        '  if (candlestickData.length === 0) return;',
        '  ',
        '  // Create main chart',
        '  const chartContainer = document.getElementById("price-chart");',
        '  const chart = LightweightCharts.createChart(chartContainer, {',
        '    layout: {',
        '      background: { type: "solid", color: "#ffffff" },',
        '      textColor: "#333",',
        '    },',
        '    grid: {',
        '      vertLines: { color: "#e1e1e1" },',
        '      horzLines: { color: "#e1e1e1" },',
        '    },',
        '    crosshair: {',
        '      mode: LightweightCharts.CrosshairMode.Normal,',
        '    },',
        '    rightPriceScale: {',
        '      borderColor: "#cccccc",',
        '    },',
        '    timeScale: {',
        '      borderColor: "#cccccc",',
        '      timeVisible: true,',
        '    },',
        '  });',
        '  ',
        '  // Candlestick series',
        '  const candlestickSeries = chart.addCandlestickSeries({',
        '    upColor: "#26a69a",',
        '    downColor: "#ef5350",',
        '    borderVisible: false,',
        '    wickUpColor: "#26a69a",',
        '    wickDownColor: "#ef5350",',
        '  });',
        '  candlestickSeries.setData(candlestickData);',
        '  ',
        '  // Volume chart',
        '  const volumeContainer = document.getElementById("volume-chart");',
        '  const volumeChart = LightweightCharts.createChart(volumeContainer, {',
        '    layout: {',
        '      background: { type: "solid", color: "#ffffff" },',
        '      textColor: "#333",',
        '    },',
        '    grid: {',
        '      vertLines: { color: "#e1e1e1" },',
        '      horzLines: { color: "#e1e1e1" },',
        '    },',
        '    rightPriceScale: {',
        '      borderColor: "#cccccc",',
        '    },',
        '    timeScale: {',
        '      borderColor: "#cccccc",',
        '    },',
        '  });',
        '  ',
        '  const volumeSeries = volumeChart.addHistogramSeries({',
        '    priceFormat: { type: "volume" },',
        '  });',
        '  volumeSeries.setData(volumeData);',
        '  ',
        '  // Sync time scales',
        '  chart.timeScale().subscribeVisibleLogicalRangeChange(range => {',
        '    volumeChart.timeScale().setVisibleLogicalRange(range);',
        '  });',
        '  volumeChart.timeScale().subscribeVisibleLogicalRangeChange(range => {',
        '    chart.timeScale().setVisibleLogicalRange(range);',
        '  });',
        '  ',
        '  // Resize handler',
        '  window.addEventListener("resize", () => {',
        '    chart.applyOptions({ width: chartContainer.clientWidth });',
        '    volumeChart.applyOptions({ width: volumeContainer.clientWidth });',
        '  });',
        '  ',
        '  // Fit content',
        '  chart.timeScale().fitContent();',
        '  volumeChart.timeScale().fitContent();',
        '});',
        '</script>',
    ]


def _get_html_styles() -> str:
    return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fff;
            min-height: 100vh;
        }
        h1 { color: #1a1a1a; margin-bottom: 10px; font-size: 28px; }
        h2 { color: #2c3e50; margin: 25px 0 15px; padding-bottom: 10px; border-bottom: 3px solid #3498db; }
        h3 { color: #34495e; margin: 15px 0 10px; font-size: 16px; }
        .meta { color: #7f8c8d; font-size: 14px; margin-bottom: 20px; }
        hr { border: none; border-top: 1px solid #eee; margin: 30px 0; }
        .section { margin: 25px 0; padding: 20px; background: #fafafa; border-radius: 8px; }
        .section.final { background: #e8f5e9; border-left: 4px solid #27ae60; }
        .chart-section { background: #fff; border: 1px solid #e0e0e0; }
        .chart-info { color: #666; font-size: 14px; margin-bottom: 10px; }
        .confidence { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 13px; font-weight: 500; margin-bottom: 15px; }
        .confidence.high { background: #d4edda; color: #155724; }
        .confidence.medium { background: #fff3cd; color: #856404; }
        .confidence.low { background: #f8d7da; color: #721c24; }
        .details { background: #fff; padding: 15px; border-radius: 6px; margin: 15px 0; border: 1px solid #eee; }
        .details ul { padding-left: 20px; margin: 10px 0; }
        .details li { margin: 5px 0; }
        .raw-response { margin: 15px 0; }
        .raw-response pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.5; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 12px; text-align: center; }
        ul { padding-left: 25px; }
        li { margin: 5px 0; }
        .markdown-content { background: #fff; padding: 15px; border-radius: 6px; line-height: 1.8; margin: 10px 0; }
        .markdown-content p { margin: 10px 0; }
        .markdown-content ul, .markdown-content ol { padding-left: 25px; margin: 10px 0; }
        .markdown-content li { margin: 5px 0; }
        .markdown-content h3 { color: #34495e; margin: 15px 0 10px; }
        .markdown-content h4 { color: #555; margin: 12px 0 8px; font-size: 15px; }
        .markdown-content strong { color: #2c3e50; }
        .markdown-content code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        .markdown-content pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 6px; overflow-x: auto; }
        .markdown-content pre code { background: none; padding: 0; }
    """

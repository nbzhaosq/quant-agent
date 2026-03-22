"""MCP tools using Claude Agent SDK @tool decorator."""

import json
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from claude_agent_sdk import tool, create_sdk_mcp_server


def _get_tushare_client() -> Any:
    """Lazy import and create TushareClient to avoid circular imports."""
    from quant_agent.data.tushare_client import TushareClient
    return TushareClient()


# ============================================================================
# Tushare Data Tools
# ============================================================================


@tool(
    "tushare_search",
    "Search for A-share stocks by name or code. Use this to find the correct ts_code for a stock.",
    {"keyword": str},
)
async def tushare_search(args: dict[str, Any]) -> dict[str, Any]:
    """Search for stocks by name or code."""
    client = _get_tushare_client()
    keyword = args["keyword"]
    df = client.search_stock(keyword)

    if df.empty:
        return {
            "content": [{"type": "text", "text": f"未找到匹配 '{keyword}' 的股票"}]
        }

    result = df[["ts_code", "name", "market", "list_date"]].head(10).to_dict("records")
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}
        ]
    }


@tool(
    "tushare_daily",
    "Get historical daily price data for a stock including OHLCV.",
    {"ts_code": str, "start_date": str | None, "end_date": str | None},
)
async def tushare_daily(args: dict[str, Any]) -> dict[str, Any]:
    """Get daily price data."""
    client = _get_tushare_client()
    ts_code = args["ts_code"]
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    df = client.get_daily(ts_code, start_date, end_date)

    if df.empty:
        return {
            "content": [{"type": "text", "text": f"未找到 {ts_code} 的行情数据"}]
        }

    df = df.sort_values("trade_date", ascending=False)
    result = df.head(30).to_dict("records")
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}
        ]
    }


@tool(
    "tushare_financial",
    "Get financial statements (income, balance sheet, cash flow) for a stock.",
    {"ts_code": str, "report_type": str},
)
async def tushare_financial(args: dict[str, Any]) -> dict[str, Any]:
    """Get financial statements."""
    client = _get_tushare_client()
    ts_code = args["ts_code"]
    report_type = args["report_type"]

    if report_type == "income":
        df = client.get_income(ts_code)
        key_fields = [
            "ts_code", "ann_date", "f_ann_date", "end_date",
            "revenue", "oper_cost", "sell_exp", "admin_exp",
            "fin_exp", "income_tax", "n_income", "basic_eps",
        ]
    elif report_type == "balance":
        df = client.get_balancesheet(ts_code)
        key_fields = [
            "ts_code", "end_date", "total_assets", "total_liab",
            "total_hldr_eqy_exc_min_int", "capital_rese", "surplus_rese",
            "money_cap", "trad_asset", "notes_receiv", "accounts_receiv",
        ]
    elif report_type == "cashflow":
        df = client.get_cashflow(ts_code)
        key_fields = [
            "ts_code", "end_date", "n_cashflow_act",
            "n_cashflow_inv_act", "n_cash_flows_fnc_act",
            "cash_recp_sg_and_rs", "recp_tax_rends", "n_incr_cash_cash_equ",
        ]
    else:
        return {
            "content": [{"type": "text", "text": f"不支持的报表类型: {report_type}"}],
            "is_error": True,
        }

    if df.empty:
        return {
            "content": [{"type": "text", "text": f"未找到 {ts_code} 的{report_type}数据"}]
        }

    available_fields = [f for f in key_fields if f in df.columns]
    result = df[available_fields].head(4).to_dict("records")
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}
        ]
    }


@tool(
    "tushare_moneyflow",
    "Get money flow data showing institutional and retail trading activity.",
    {"ts_code": str, "days": int | None},
)
async def tushare_moneyflow(args: dict[str, Any]) -> dict[str, Any]:
    """Get money flow data."""
    client = _get_tushare_client()
    ts_code = args["ts_code"]
    days = args.get("days", 30)

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    df = client.get_moneyflow(ts_code, start_date, end_date)

    if df.empty:
        return {
            "content": [{"type": "text", "text": f"未找到 {ts_code} 的资金流向数据"}]
        }

    result = df.head(20).to_dict("records")
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}
        ]
    }


# ============================================================================
# Technical Analysis Tools
# ============================================================================


@tool(
    "calculate_ma",
    "Calculate moving averages (MA5, MA10, MA20, MA60) from price data.",
    {
        "prices": list[float],
        "periods": list[int] | None,
    },
)
async def calculate_ma(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate moving averages."""
    prices = args["prices"]
    periods = args.get("periods", [5, 10, 20, 60])

    df = pd.DataFrame({"close": prices})
    result: dict[str, Any] = {"current_price": prices[-1] if prices else None}

    for period in periods:
        if len(prices) >= period:
            ma = df["close"].rolling(window=period).mean()
            result[f"MA{period}"] = round(ma.iloc[-1], 2)
            result[f"MA{period}_trend"] = "above" if prices[-1] > result[f"MA{period}"] else "below"

    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
        ]
    }


@tool(
    "calculate_macd",
    "Calculate MACD (Moving Average Convergence Divergence) indicator.",
    {"prices": list[float]},
)
async def calculate_macd(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate MACD indicator."""
    prices = args["prices"]

    if len(prices) < 35:
        return {
            "content": [{"type": "text", "text": "数据不足，至少需要35天的数据来计算MACD"}],
            "is_error": True,
        }

    df = pd.DataFrame({"close": prices})

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = (dif - dea) * 2

    signal = "金叉" if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2] \
        else "死叉" if dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2] \
        else "多头" if dif.iloc[-1] > dea.iloc[-1] else "空头"

    result = {
        "DIF": round(dif.iloc[-1], 4),
        "DEA": round(dea.iloc[-1], 4),
        "MACD": round(macd.iloc[-1], 4),
        "signal": signal,
        "trend": "上升" if macd.iloc[-1] > macd.iloc[-2] else "下降",
    }

    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
        ]
    }


@tool(
    "calculate_rsi",
    "Calculate RSI (Relative Strength Index) indicator.",
    {"prices": list[float], "period": int | None},
)
async def calculate_rsi(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate RSI indicator."""
    prices = args["prices"]
    period = args.get("period", 14)

    if len(prices) < period + 1:
        return {
            "content": [{"type": "text", "text": f"数据不足，至少需要{period + 1}天的数据来计算RSI"}],
            "is_error": True,
        }

    df = pd.DataFrame({"close": prices})
    delta = df["close"].diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    rsi_value = rsi.iloc[-1]
    level = "超买" if rsi_value > 70 else "超卖" if rsi_value < 30 else "中性"
    suggestion = "注意回调风险" if rsi_value > 70 \
        else "可能存在反弹机会" if rsi_value < 30 \
        else "指标正常区间"

    result = {
        "RSI": round(rsi_value, 2),
        "level": level,
        "suggestion": suggestion,
    }

    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
        ]
    }


@tool(
    "calculate_volatility",
    "Calculate price volatility (standard deviation and ATR).",
    {
        "high": list[float],
        "low": list[float],
        "close": list[float],
    },
)
async def calculate_volatility(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate volatility metrics."""
    high = args["high"]
    low = args["low"]
    close = args["close"]

    df = pd.DataFrame({"high": high, "low": low, "close": close})

    # Calculate ATR
    df["prev_close"] = df["close"].shift(1)
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["prev_close"]),
            abs(df["low"] - df["prev_close"]),
        ),
    )
    atr = df["tr"].rolling(window=14).mean()

    # Calculate annualized volatility
    returns = pd.Series(close).pct_change()
    volatility = returns.rolling(window=20).std() * np.sqrt(252)

    vol_value = volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0
    vol_level = "高波动" if vol_value > 0.4 else "中等波动" if vol_value > 0.2 else "低波动"

    result = {
        "ATR": round(atr.iloc[-1], 4) if not pd.isna(atr.iloc[-1]) else None,
        "ATR_percent": round(atr.iloc[-1] / close[-1] * 100, 2) if atr.iloc[-1] else None,
        "volatility_annual": round(vol_value * 100, 2),
        "volatility_level": vol_level,
    }

    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
        ]
    }


def create_quant_mcp_server() -> Any:
    """Create the MCP server with all quant tools."""
    return create_sdk_mcp_server(
        name="quant",
        version="1.0.0",
        tools=[
            tushare_search,
            tushare_daily,
            tushare_financial,
            tushare_moneyflow,
            calculate_ma,
            calculate_macd,
            calculate_rsi,
            calculate_volatility,
        ],
    )

"""Custom entity types for quant research knowledge graph."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Stock(BaseModel):
    """A-share stock entity for knowledge graph."""

    ts_code: str | None = Field(None, description="Stock code e.g., 600519.SH")
    name: str | None = Field(None, description="Stock name")
    industry: str | None = Field(None, description="Industry sector")
    sector: str | None = Field(None, description="Market sector")
    market_cap: float | None = Field(None, description="Market capitalization")
    pe_ratio: float | None = Field(None, description="Price-to-earnings ratio")
    pb_ratio: float | None = Field(None, description="Price-to-book ratio")
    list_date: datetime | None = Field(None, description="Listing date")


class Company(BaseModel):
    """Company entity for knowledge graph."""

    name: str | None = Field(None, description="Full company name")
    headquarters: str | None = Field(None, description="Headquarters location")
    employee_count: int | None = Field(None, description="Number of employees")
    founded_date: datetime | None = Field(None, description="Company founding date")


class NewsEvent(BaseModel):
    """News/event entity for knowledge graph."""

    title: str | None = Field(None, description="News title")
    category: str | None = Field(None, description="News category: earnings/merger/policy/etc")
    sentiment: str | None = Field(None, description="Sentiment: positive/negative/neutral")
    impact_level: str | None = Field(None, description="Impact level: high/medium/low")
    published_date: datetime | None = Field(None, description="Publication date")
    source: str | None = Field(None, description="News source")


class Sector(BaseModel):
    """Market sector entity for knowledge graph."""

    name: str | None = Field(None, description="Sector name")
    description: str | None = Field(None, description="Sector description")
    avg_pe: float | None = Field(None, description="Average P/E ratio")
    market_cap: float | None = Field(None, description="Total sector market cap")


class AnalysisReport(BaseModel):
    """Analysis report entity for knowledge graph."""

    ts_code: str | None = Field(None, description="Stock code analyzed")
    report_type: str | None = Field(
        None, description="Report type: technical/fundamental/sentiment/risk"
    )
    summary: str | None = Field(None, description="Analysis summary")
    recommendation: str | None = Field(None, description="Investment recommendation")
    confidence: float | None = Field(None, description="Confidence score 0-1")
    created_date: datetime | None = Field(None, description="Report creation date")
    analyst: str | None = Field(None, description="Analyst agent type")


class StockSectorRelation(BaseModel):
    """Stock-Sector relationship edge."""

    weight: float | None = Field(None, description="Sector weight percentage")
    added_date: datetime | None = Field(None, description="Date added to sector")


class NewsImpact(BaseModel):
    """News-Stock impact relationship edge."""

    impact_type: str | None = Field(None, description="Type of impact")
    confidence: float | None = Field(None, description="Impact confidence 0-1")

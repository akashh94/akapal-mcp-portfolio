"""MCP Portfolio Server â€” SSE transport.

Provides portfolio data via MCP tools.
Currently backed by mock data (StaticBrokerageService).
Future: real E*TRADE API connection.
"""

import logging
import os

from mcp.server.fastmcp import FastMCP

from akapal_mcp_portfolio.services.live_market_service import LiveMarketService
from akapal_mcp_portfolio.services.static_brokerage_service import StaticBrokerageService

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


_static_service = StaticBrokerageService()
_live_service = LiveMarketService()

mcp = FastMCP(
    "etrade-portfolio-mcp",
    instructions="Portfolio data from E*TRADE â€” mock data until real API connection is established.",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
)


# â”€â”€ Tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@mcp.tool()
def get_account_summary() -> dict:
    """Return the active account's balances and portfolio performance summary."""
    return _static_service.get_portfolio_summary().to_dict()


@mcp.tool()
def get_portfolio_holdings() -> list[dict]:
    """Return all holdings with allocation and performance fields."""
    return [h.to_dict() for h in _static_service.get_holdings()]


@mcp.tool()
def get_sector_allocation() -> list[dict]:
    """Return the portfolio's allocation by sector."""
    return [s.to_dict() for s in _static_service.get_sector_allocation()]


@mcp.tool()
def get_quote(symbol: str) -> dict | None:
    """Return a current quote for the given stock symbol.

    Tries to fetch real-time data first; falls back to mock data
    when the live service is unavailable.
    """
    live = _live_service.get_quote(symbol)
    if live is not None:
        return live.to_dict()
    quote = _static_service.get_quote(symbol)
    return quote.to_dict() if quote else None


@mcp.tool()
def get_market_summary() -> list[dict]:
    """Return market index summary data."""
    return [i.to_dict() for i in _static_service.get_market_summary()]


@mcp.tool()
def get_faq(query: str = "") -> list[dict]:
    """Return mock brokerage support FAQ entries, optionally filtered by text."""
    entries = _static_service.get_faq()
    q = query.strip().lower()
    return [
        entry for entry in entries
        if not q or q in f"{entry['question']} {entry['answer']}".lower()
    ]


@mcp.tool()
def search_financial_info(query: str = "", source: str = "") -> dict:
    """Search broker data and public financial sources by keyword.

    When *query* mentions holdings, portfolio, or shares, returns live (mock)
    portfolio data. Optionally filter by *source* (yahoo, bloomberg, reuters,
    morningstar, sec).
    """
    _SEARCH_SOURCES = {
        "yahoo": "Yahoo Finance",
        "bloomberg": "Bloomberg",
        "reuters": "Reuters",
        "morningstar": "Morningstar",
        "sec": "SEC Edgar",
    }
    q = query.strip().lower() if query else ""

    # Tier 1: private brokerage data
    if q and any(kw in q for kw in ("holdings", "portfolio", "shares", "position")):
        holdings = _static_service.get_holdings()
        summary = _static_service.get_portfolio_summary()
        rows = [
            f"{h.symbol} ({h.company_name}): {h.shares} shares @ ${h.current_price:.2f} "
            f"= ${h.market_value:,.2f} | {h.day_change_percent:+.2f}% day | "
            f"weight {h.portfolio_weight:.1f}%"
            for h in holdings
        ]
        return {
            "results": rows,
            "source": "Live Portfolio",
            "summary": {
                "total_value": summary.total_value,
                "cash_balance": summary.cash_balance,
                "holdings_count": len(holdings),
            },
        }

    if q and any(kw in q for kw in ("transactions", "trades", "history")):
        return {
            "results": [
                "Mock data: recent trades include BUY AAPL 10 shares @ $198.50 on 2026-07-08",
                "Mock data: BUY MSFT 5 shares @ $443.00 on 2026-07-07",
            ],
            "source": "Transaction History (Mock)",
        }

    # Tier 2: source requested but no implementation yet
    src_label = _SEARCH_SOURCES.get(source.strip().lower()) if source else None
    if src_label:
        return {
            "results": [
                f'Public web search for "{query}" via {src_label} is not yet '
                "connected. Add an API key or web-search backend to enable "
                "live financial-news retrieval.",
            ],
            "source": src_label,
            "status": "integration_pending",
        }

    # Tier 3: list available sources
    if not q:
        return {
            "results": [f"Search via {label} (key: {key})" for key, label in _SEARCH_SOURCES.items()],
            "source": "Available Sources",
        }

    return {
        "results": [f'No data found for "{query}" in local brokerage or public sources.'],
        "source": "search_financial_info",
    }


@mcp.tool()
def preview_order_impact(symbol: str, quantity: float, side: str) -> dict:
    """Estimate a mock buy or sell order's portfolio impact without placing it."""
    normalized_side = side.strip().upper()
    if normalized_side not in {"BUY", "SELL"}:
        return {"error": "side must be BUY or SELL"}
    if quantity <= 0:
        return {"error": "quantity must be greater than zero"}
    quote = _static_service.get_quote(symbol)
    if quote is None:
        return {"error": f"No mock quote is available for {symbol.upper().strip()}."}

    summary = _static_service.get_portfolio_summary()
    holding = next((item for item in _static_service.get_holdings() if item.symbol == quote.symbol), None)
    current_value = holding.market_value if holding else 0.0
    order_value = round(quote.price * quantity, 2)
    projected_value = current_value + order_value if normalized_side == "BUY" else max(0.0, current_value - order_value)
    projected_weight = round(projected_value / summary.total_value * 100, 2)
    return {
        "symbol": quote.symbol,
        "side": normalized_side,
        "quantity": quantity,
        "estimated_price": quote.price,
        "estimated_order_value": order_value,
        "projected_position_weight_percent": projected_weight,
        "concentration_warning": projected_weight > 15,
        "is_mock": True,
        "order_submitted": False,
    }


@mcp.tool()
def get_concentration_analysis() -> dict:
    """Identify positions exceeding the 15% concentration threshold."""
    holdings = _static_service.get_holdings()
    concentrated = [h for h in holdings if h.portfolio_weight > 15]
    return {
        "threshold_percent": 15,
        "largest_positions": [
            h.to_dict()
            for h in sorted(holdings, key=lambda x: x.portfolio_weight, reverse=True)[:5]
        ],
        "concentrated_positions": [h.to_dict() for h in concentrated],
        "is_concentrated": bool(concentrated),
        "data_source": "mock brokerage data",
    }


# â”€â”€ Entry Point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting ETrade Portfolio MCP server on port %s with SSE transport", port)
    mcp.run(transport="sse")

# akapal-mcp-portfolio

MCP server that exposes portfolio and brokerage data through [Model Context Protocol](https://modelcontextprotocol.io) tools over SSE transport.

Data is currently backed by mock brokerage data (`StaticBrokerageService`). Live quotes are attempted first via `LiveMarketService` (yfinance) with automatic fallback to mock data when the live source is unavailable. A real E*TRADE API connection is planned as the next step.

## Features

- **SSE transport** on port `8080` (configurable via `PORT`), binds to `0.0.0.0`
- **Mock brokerage data** — balances, holdings, sector allocation, quotes, market summary, FAQ
- **Live quote fallback** — real-time quotes when available, mock otherwise
- **Order preview** — estimates the portfolio impact of a buy/sell order without placing it
- **Concentration analysis** — flags positions exceeding a 15% threshold
- **Keyword search** — queries brokerage data and lists public financial sources (Yahoo, Bloomberg, Reuters, Morningstar, SEC)

## Requirements

- Python 3.11+

## Installation

```bash
pip install .
```

For development:

```bash
pip install -e .
```

## Usage

Start the server:

```bash
python -m akapal_mcp_portfolio.app
```

Or via Docker:

```bash
docker build -t akapal-mcp-portfolio .
docker run -p 8080:8080 akapal-mcp-portfolio
```

The server listens on `http://0.0.0.0:8080` and serves the MCP SSE endpoint. Point an MCP client (e.g. Claude Desktop, IDE MCP config) at it to discover and call the tools.

### Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `8080` | HTTP port for the SSE server |

## Tools

| Tool | Description |
| --- | --- |
| `get_account_summary` | Active account balances and portfolio performance summary |
| `get_portfolio_holdings` | All holdings with allocation and performance fields |
| `get_sector_allocation` | Portfolio allocation by sector |
| `get_quote(symbol)` | Current quote for a symbol; live first, mock fallback |
| `get_market_summary` | Market index summary data |
| `get_faq(query)` | Mock support FAQ entries, optionally filtered by text |
| `search_financial_info(query, source)` | Keyword search over broker data and public sources |
| `preview_order_impact(symbol, quantity, side)` | Estimate mock order impact without placing it (`side` must be `BUY` or `SELL`) |
| `get_concentration_analysis` | Positions exceeding the 15% concentration threshold |

## Project Structure

```
akapal_mcp_portfolio/
├── app.py                     # FastMCP server, SSE transport, tool definitions
├── models/                    # Dataclasses for account, holdings, quote, market, etc.
└── services/
    ├── static_brokerage_service.py   # Mock brokerage data
    └── live_market_service.py        # Live quotes (yfinance) with fallback
```

## Roadmap

- Connect real E*TRADE API for live brokerage data
- Wire up live financial-news retrieval for the public sources in `search_financial_info`

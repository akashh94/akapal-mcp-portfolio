"""Real-time stock quotes via yfinance.

Falls back to ``None`` on any error (unknown symbol, network issue, rate
limit) so callers can chain to a mock or cached source.
"""

import logging

from models.quote import Quote

_LOGGER = logging.getLogger(__name__)


class LiveMarketService:
    """Wraps ``yfinance.Ticker`` to return ``Quote`` instances."""

    def get_quote(self, symbol: str) -> Quote | None:
        import yfinance as yf  # defer import so startup doesn't fail if absent

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            price = _field(info, "currentPrice", "regularMarketPrice")
            if price is None:
                _LOGGER.warning("yfinance returned no price for %s", symbol)
                return None

            return Quote(
                symbol=symbol,
                company_name=_field(info, "longName", "shortName") or symbol,
                price=price,
                change=_field(info, "regularMarketChange") or 0.0,
                change_percent=_field(info, "regularMarketChangePercent") or 0.0,
                open_price=_field(info, "regularMarketOpen") or price,
                high_price=_field(info, "regularMarketDayHigh") or price,
                low_price=_field(info, "regularMarketDayLow") or price,
                volume=int(_field(info, "regularMarketVolume") or 0),
                average_volume=int(_field(info, "averageVolume") or 0),
                market_cap=_format_market_cap(_field(info, "marketCap")),
                pe_ratio=_field(info, "trailingPE"),
                eps=_field(info, "trailingEps"),
                week_52_high=_field(info, "fiftyTwoWeekHigh") or price,
                week_52_low=_field(info, "fiftyTwoWeekLow") or price * 0.75,
                dividend_yield=_field(info, "dividendYield", "trailingAnnualDividendYield"),
            )
        except Exception:
            _LOGGER.warning("Failed to fetch live quote for %s", symbol, exc_info=True)
            return None


def _field(info: dict, *keys: str) -> float | str | None:
    """Return the first non-None value for *keys* from *info*."""
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return None


def _format_market_cap(value: float | int | None) -> str:
    """Format a numeric market cap as a human-friendly string."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if v >= 1_000_000_000_000:
            return f"${v / 1_000_000_000_000:.1f}T"
        if v >= 1_000_000_000:
            return f"${v / 1_000_000_000:.1f}B"
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return str(value)

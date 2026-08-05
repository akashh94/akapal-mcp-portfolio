from akapal_mcp_portfolio.models.base import BaseModel


class MarketIndex(BaseModel):
    symbol: str
    name: str
    value: float
    change: float
    change_percent: float

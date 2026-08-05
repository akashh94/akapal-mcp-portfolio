from akapal_mcp_portfolio.models.base import BaseModel


class SectorAllocation(BaseModel):
    sector_name: str
    market_value: float
    portfolio_weight: float

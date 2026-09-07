from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    asset_type = Column(String)  # "STOCK" veya "FUND"
    amount = Column(Float)
    avg_cost = Column(Float)
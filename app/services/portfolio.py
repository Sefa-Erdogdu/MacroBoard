from sqlalchemy.orm import Session
from app.models import PortfolioItem
from app.services.market import MarketService
from app.services.tefas import TefasService

class PortfolioService:
    @staticmethod
    def add_item(db: Session, symbol: str, asset_type: str, amount: float, avg_cost: float):
        item = PortfolioItem(
            symbol=symbol.upper(),
            asset_type=asset_type.upper(),
            amount=amount,
            avg_cost=avg_cost
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def add_or_merge_item(db: Session, symbol: str, asset_type: str, amount: float, avg_cost: float):
        symbol = symbol.upper()
        asset_type = asset_type.upper()

        existing = db.query(PortfolioItem).filter(
            PortfolioItem.symbol == symbol,
            PortfolioItem.asset_type == asset_type
        ).first()

        if existing:
            # Ağırlıklı ortalama maliyet hesapla
            existing_total_cost = existing.amount * existing.avg_cost
            new_total_cost = amount * avg_cost
            merged_amount = existing.amount + amount

            if merged_amount > 0:
                merged_avg_cost = (existing_total_cost + new_total_cost) / merged_amount
            else:
                merged_avg_cost = avg_cost

            existing.amount = merged_amount
            existing.avg_cost = merged_avg_cost
            db.commit()
            db.refresh(existing)
            return existing
        else:
            return PortfolioService.add_item(db, symbol, asset_type, amount, avg_cost)

    @staticmethod
    def get_summary(db: Session):
        items = db.query(PortfolioItem).all()
        
        # Anlık Dolar/TL kurunu çekiyoruz
        usd_quote = MarketService.get_symbol_quote("TRY=X")
        usd_try_rate = usd_quote.get("price", 1.0) if "error" not in usd_quote else 1.0

        result = []
        total_value_try = 0.0
        total_cost_try = 0.0

        for item in items:
            current_price = 0.0
            currency = "TRY"

            if item.asset_type == "STOCK":
                quote = MarketService.get_symbol_quote(item.symbol)
                current_price = quote.get("price", 0.0)
                if item.symbol.endswith(".IS"):
                    currency = "TRY"
                else:
                    currency = quote.get("currency", "USD")
            elif item.asset_type == "FUND":
                quote = TefasService.get_fund_quote(item.symbol)
                current_price = quote.get("price", 0.0)
                currency = "TRY"

            # Fiyat çekilemezse (0 kalırsa) maliyet fiyatını baz alarak portföyü koru
            if current_price == 0.0:
                current_price = item.avg_cost

            # Dolar cinsinden varlıkları güncel Dolar/TL kuruyla çarpıyoruz
            fx_rate = usd_try_rate if currency == "USD" else 1.0
            
            # Değer ve Maliyet Hesaplamaları (TL Bazında)
            value_in_try = round(current_price * item.amount * fx_rate, 2)
            cost_in_try = round(item.avg_cost * item.amount * fx_rate, 2)
            
            profit_loss_try = round(value_in_try - cost_in_try, 2)
            profit_loss_percent = round(((value_in_try - cost_in_try) / cost_in_try) * 100, 2) if cost_in_try > 0 else 0.0

            total_value_try += value_in_try
            total_cost_try += cost_in_try

            result.append({
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "amount": item.amount,
                "avg_cost": item.avg_cost,
                "currency": currency,
                "current_price": current_price,
                "value_try": value_in_try,
                "cost_try": cost_in_try,
                "profit_loss_try": profit_loss_try,
                "profit_loss_percent": profit_loss_percent
            })

        total_profit_loss_try = round(total_value_try - total_cost_try, 2)
        total_profit_loss_percent = round(((total_value_try - total_cost_try) / total_cost_try) * 100, 2) if total_cost_try > 0 else 0.0

        return {
            "usd_try_rate": usd_try_rate,
            "total_portfolio_value_try": round(total_value_try, 2),
            "total_portfolio_cost_try": round(total_cost_try, 2),
            "total_profit_loss_try": total_profit_loss_try,
            "total_profit_loss_percent": total_profit_loss_percent,
            "items": result
        }

    @staticmethod
    def delete_item(db: Session, item_id: int) -> bool:
        item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True
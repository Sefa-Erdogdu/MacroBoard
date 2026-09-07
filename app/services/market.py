import yfinance as yf

class MarketService:
    @staticmethod
    def get_symbol_quote(symbol: str):
        symbol = symbol.upper()
        
        # Yahoo Finance üzerinde bulunmayan ALTIN.S1.IS için dinamik hesaplama (1 Sertifika = 0.01 Gram Altın)
        if symbol in ["ALTIN.S1.IS", "ALTIN.S1"]:
            try:
                gold_ounce = yf.Ticker("GC=F").fast_info.get("lastPrice", 0.0)
                usd_try = yf.Ticker("TRY=X").fast_info.get("lastPrice", 1.0)
                if gold_ounce > 0 and usd_try > 0:
                    gram_try = (gold_ounce * usd_try) / 31.1035
                    cert_price = round(gram_try / 100, 2)
                    return {"symbol": symbol, "price": cert_price, "currency": "TRY"}
            except Exception:
                pass

        # Standart Hisse ve Varlık Sorgusu
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info.get("lastPrice", 0.0)
            currency = ticker.fast_info.get("currency", "USD")
            
            if symbol.endswith(".IS"):
                currency = "TRY"
                
            return {
                "symbol": symbol,
                "price": round(price, 2) if price else 0.0,
                "currency": currency
            }
        except Exception as e:
            return {"error": str(e)}
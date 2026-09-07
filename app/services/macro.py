import yfinance as yf

class MacroService:
    # Makro göstergeler ve yfinance sembol karşılıkları
    INDICATORS = {
        "USDTRY": "TRY=X",        # Dolar / TL
        "EURTRY": "EURTRY=X",     # Euro / TL
        "US10Y": "^TNX",          # ABD 10 Yıllık Tahvil Faizi
        "GOLD": "GC=F",           # Ons Altın (USD)
        "BRENT": "BZ=F",          # Brent Petrol
        "SP500": "^GSPC"          # S&P 500 Endeksi
    }

    @staticmethod
    def get_macro_overview() -> dict:
        summary = {}
        
        for key, ticker_symbol in MacroService.INDICATORS.items():
            try:
                ticker = yf.Ticker(ticker_symbol)
                history = ticker.history(period="5d")
                
                if not history.empty:
                    latest = float(history['Close'].iloc[-1])
                    prev = float(history['Close'].iloc[-2]) if len(history) > 1 else latest
                    change_percent = round(((latest - prev) / prev) * 100, 2)
                    
                    summary[key] = {
                        "value": round(latest, 2),
                        "previous": round(prev, 2),
                        "change_percent": change_percent
                    }
            except Exception:
                summary[key] = {"error": "Veri alınamadı"}
                
        return summary
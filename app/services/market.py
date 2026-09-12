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

    @staticmethod
    def get_batch_quotes(symbols: list) -> dict:
            """
            Birden fazla hisse/ETF sembolünü paralel (batch) olarak çeker.
            Sıralı N ayrı istek yerine, hepsini aynı anda gönderir.
            Dönüş: {sembol: {"price": ..., "currency": ...}, ...}
            """
            results = {}
            clean_symbols = [s for s in symbols if s not in ["ALTIN.S1.IS", "ALTIN.S1"]]
            if not clean_symbols:
                return results

            try:
                data = yf.download(
                    tickers=" ".join(clean_symbols),
                    period="5d",
                    group_by="ticker",
                    threads=True,
                    progress=False
                )
                for sym in clean_symbols:
                    try:
                        hist = data if len(clean_symbols) == 1 else data[sym]
                        closes = hist["Close"].dropna()
                        if len(closes) == 0:
                            continue
                        price = float(closes.iloc[-1])
                        currency = "TRY" if sym.endswith(".IS") else "USD"
                        results[sym] = {"price": round(price, 2), "currency": currency}
                    except Exception:
                        continue
            except Exception:
                pass

            # Toplu istekte eksik kalan/başarısız sembolleri tek tek dene (güvenlik ağı)
            for sym in clean_symbols:
                if sym not in results:
                    quote = MarketService.get_symbol_quote(sym)
                    if "error" not in quote:
                        results[sym] = {"price": quote["price"], "currency": quote.get("currency", "USD")}

            return results
from tefas import Crawler
from datetime import datetime, timedelta

class TefasService:
    @staticmethod
    def get_fund_quote(fund_code: str) -> dict:
        code = fund_code.strip().upper()
        tefas = Crawler()
        
        # Hafta sonu ve tatillere takılmamak için son 7 günün verisini istiyoruz
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        try:
            # Parametreler: start, end, name
            df = tefas.fetch(start=start_date, end=end_date, name=code)
            
            if df is None or df.empty:
                return {"error": f"'{code}' fonu için TEFAS verisi bulunamadı."}
            
            # En güncel kayıt
            latest = df.iloc[-1]
            price = float(latest.get('price', 0))
            title = str(latest.get('title', code))
            
            # Bir önceki günün fiyatı
            prev_price = float(df.iloc[-2].get('price', price)) if len(df) > 1 else price
            change_percent = round(((price - prev_price) / prev_price) * 100, 2) if prev_price > 0 else 0.0

            return {
                "symbol": code,
                "title": title,
                "price": price,
                "previous_close": prev_price,
                "change_percent": change_percent,
                "currency": "TRY"
            }
        except Exception as e:
            return {"error": f"TEFAS verisi alınırken hata oluştu: {str(e)}"}
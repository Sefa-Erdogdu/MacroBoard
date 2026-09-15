from tefas import Crawler
from datetime import datetime, timedelta
import pandas as pd

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

            # En güncel kayıt — eğer son satırın fiyatı 0/boşsa (TEFAS o günü
            # henüz yayınlamamışsa), geriye doğru ilk geçerli (>0) fiyatı bul
            valid_prices = df[df['price'].astype(float) > 0]
            if valid_prices.empty:
                return {"error": f"'{code}' fonu için geçerli fiyat verisi bulunamadı."}

            latest = valid_prices.iloc[-1]
            price = float(latest.get('price', 0))
            title = str(latest.get('title', code))

            # Bir önceki günün fiyatı
            prev_price = float(valid_prices.iloc[-2].get('price', price)) if len(valid_prices) > 1 else price
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

    @staticmethod
    def get_fund_volatility(fund_code: str, days: int = 90) -> float:
        """TEFAS fonu için yıllıklandırılmış volatilite (%) hesaplar."""
        code = fund_code.strip().upper()
        try:
            tefas = Crawler()
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            df = tefas.fetch(start=start_date, end=end_date, name=code)

            if df is None or df.empty or len(df) < 5:
                return 0.0

            prices = df["price"].astype(float)
            prices = prices[prices > 0]  # Hatalı/boş (0) fiyat satırlarını at
            if len(prices) < 5:
                return 0.0

            returns = prices.pct_change().dropna()
            # Tek günlük %50'den büyük sıçramalar gerçek piyasa hareketinden çok
            # veri hatasına (o günün fiyatının boş/0 gelmesine) işaret eder — at.
            returns = returns[returns.abs() < 0.5]
            if len(returns) < 3:
                return 0.0

            annualized = returns.std() * (252 ** 0.5) * 100
            return round(float(annualized), 2)
        except Exception:
            return 0.0

    @staticmethod
    def get_fund_history(fund_code: str, days: int = 90):
        """TEFAS fonu için geçmiş fiyat serisini (grafik için) döndürür."""
        code = fund_code.strip().upper()
        try:
            tefas = Crawler()
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            df = tefas.fetch(start=start_date, end=end_date, name=code)

            if df is None or df.empty:
                return None

            df = df[df["price"].astype(float) > 0].copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            return df[["date", "price"]]
        except Exception:
            return None
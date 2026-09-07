import pdfplumber
import re
from app.services.tefas import TefasService

class PdfImportService:
    @staticmethod
    def parse_midas_statement(file_bytes) -> dict:
        try:
            full_text = ""
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    full_text += page_text + "\n"
        except Exception as e:
            return {"error": f"PDF okunurken hata oluştu: {str(e)}"}

        if not full_text.strip():
            return {"error": "PDF içinden metin okunamadı."}

        # Sadece 'Portföy Özeti' bölümünü al (işlem geçmişi tablosuna karışmasın)
        start_marker = "PORTFÖY ÖZETİ"
        end_marker = "YATIRIM İŞLEMLERİ"
        start_idx = full_text.find(start_marker)
        end_idx = full_text.find(end_marker)

        if start_idx == -1:
            return {"error": "PDF içinde 'Portföy Özeti' bölümü bulunamadı."}

        section_text = full_text[start_idx: end_idx if end_idx != -1 else None]

        # Satır deseni: SEMBOL - açıklama ... ADET ORT.MALİYET TRY KAR/ZARAR TRY TOPLAM TRY
        pattern = re.compile(
            r'([A-ZÇĞİÖŞÜ0-9\.]{2,15})\s*-\s*.+?\s+(\d[\d\.]*)\s+([\d\.,]+)\s*TRY\s+-?[\d\.,]+\s*TRY\s+[\d\.,]+\s*TRY'
        )

        rows_found = []
        seen = set()
        for match in pattern.finditer(section_text):
            symbol = match.group(1).strip().upper()
            amount_raw = match.group(2).strip()
            cost_raw = match.group(3).strip()

            if symbol in ["ADET", "TARİHİ", "SERMAYE", "PİYASASI"] or symbol in seen:
                continue

            amount = PdfImportService._parse_number(amount_raw)
            avg_cost = PdfImportService._parse_number(cost_raw)

            if amount <= 0:
                continue

            seen.add(symbol)
            rows_found.append({"symbol": symbol, "amount": amount, "avg_cost": avg_cost})

        if not rows_found:
            return {"error": "PDF içinde okunabilir bir varlık satırı bulunamadı."}

        # Her sembol için varlık tipini otomatik belirle
        enriched = []
        for item in rows_found:
            symbol = item["symbol"]

            if symbol == "ALTIN.S1":
                enriched.append({**item, "symbol": "ALTIN.S1.IS", "asset_type": "STOCK"})
                continue

            tefas_check = TefasService.get_fund_quote(symbol)
            if "error" not in tefas_check:
                enriched.append({**item, "asset_type": "FUND"})
            else:
                enriched.append({**item, "asset_type": "STOCK"})

        return {"items": enriched}

    @staticmethod
    def _parse_number(raw: str) -> float:
        try:
            cleaned = raw.replace("TRY", "").replace("₺", "").strip()
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except Exception:
            return 0.0
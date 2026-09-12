from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services.pdf_import import PdfImportService
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, get_db
from app.services.market import MarketService
from app.services.tefas import TefasService
from app.services.macro import MacroService
from app.services.portfolio import PortfolioService

# Tabloları veritabanında oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MacroBoard API",
    version="0.1.0",
    description="Finansal ve Makroekonomik Veri Terminali API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AddAssetSchema(BaseModel):
    symbol: str
    asset_type: str  # "STOCK" veya "FUND"
    amount: float
    avg_cost: float

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MacroBoard API çalışıyor."}

@app.get("/api/v1/quote/{symbol}")
def get_quote(symbol: str):
    result = MarketService.get_symbol_quote(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/v1/fund/{code}")
def get_fund_quote(code: str):
    result = TefasService.get_fund_quote(code)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/v1/macro/overview")
def get_macro_overview():
    return MacroService.get_macro_overview()

@app.post("/api/v1/portfolio/add")
def add_portfolio_item(asset: AddAssetSchema, db: Session = Depends(get_db)):
    return PortfolioService.add_or_merge_item(db, asset.symbol, asset.asset_type, asset.amount, asset.avg_cost)

@app.get("/api/v1/portfolio/summary")
def get_portfolio_summary(db: Session = Depends(get_db)):
    return PortfolioService.get_summary(db)

@app.delete("/api/v1/portfolio/delete/{item_id}")
def delete_portfolio_item(item_id: int, db: Session = Depends(get_db)):
    success = PortfolioService.delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Varlık bulunamadı.")
    return {"status": "success", "message": f"ID {item_id} olan varlık silindi."}

@app.post("/api/v1/portfolio/import/preview")
async def import_pdf_preview(file: UploadFile = File(...)):
    contents = await file.read()
    import io
    result = PdfImportService.parse_midas_statement(io.BytesIO(contents))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/v1/portfolio/import/confirm")
def import_pdf_confirm(items: list[AddAssetSchema], db: Session = Depends(get_db)):
    added = []
    for asset in items:
        item = PortfolioService.add_or_replace_item(db, asset.symbol, asset.asset_type, asset.amount, asset.avg_cost)
        added.append(item.symbol)
    return {"status": "success", "added": added, "count": len(added)}
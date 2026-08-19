from fastapi import FastAPI
from app.database import Base, engine
from app.routers import invoices

# Create tables if not present
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligent Expense Extractor API",
    version="0.1.0",
    description="Backend API for managing invoices, line items, and receipt OCR processing."
)

# Register routers
app.include_router(invoices.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Expense Extractor API is operational"}
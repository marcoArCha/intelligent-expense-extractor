import os
from dotenv import load_dotenv
from fastapi import FastAPI

# Carga las variables de entorno definidas en el archivo .env
load_dotenv()

from app.database import Base, engine
from app.routers import invoices, uploads

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligent Expense Extractor API",
    version="0.2.0",
    description="Backend API for managing invoices, line items, and receipt OCR processing."
)

app.include_router(invoices.router)
app.include_router(uploads.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Expense Extractor API is operational"}
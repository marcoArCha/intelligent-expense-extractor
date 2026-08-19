from fastapi import FastAPI
from app.database import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="0.1.0")

@app.get("/")
def root():
    return {"status": "ok", "message": "API is operational"}
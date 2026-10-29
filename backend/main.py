"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload import router as upload_router
from routers.data import router as data_router
from database import Base, engine
import models

app = FastAPI(title="Feedback Analysis API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"])
app.include_router(upload_router)
app.include_router(data_router)

@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok"}

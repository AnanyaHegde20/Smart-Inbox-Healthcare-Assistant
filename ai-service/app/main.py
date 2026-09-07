import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import batch_router, health_router, process_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

app = FastAPI(
    title="Smart Inbox Assistant - AI Service",
    description="Document processing, classification, and summarisation microservice.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(process_router, prefix="/api/v1", tags=["processing"])
app.include_router(batch_router, prefix="/api/v1", tags=["batch"])

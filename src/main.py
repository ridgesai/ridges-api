from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.operations import DatabaseManager

from src.endpoints.ingestion import router as ingestion_router
from src.endpoints.retrieval import router as retrieval_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database connection pool
    db_manager = DatabaseManager()
    yield
    # Shutdown: Close all database connections
    db_manager.close_all_connections()

app = FastAPI(lifespan=lifespan)

# Include ingestion routes
app.include_router(
    ingestion_router,
    prefix="/ingestion",
)

app.include_router(
    retrieval_router,
    prefix="/retrieval",
)

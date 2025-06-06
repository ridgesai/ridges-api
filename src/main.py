from fastapi import FastAPI

from src.endpoints.ingestion import router as ingestion_router
from src.endpoints.retrieval import router as retrieval_router

app = FastAPI()

# Include ingestion routes
app.include_router(
    ingestion_router,
    prefix="/ingestion",
)

app.include_router(
    retrieval_router,
    prefix="/retrieval",
)

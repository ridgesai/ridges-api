from fastapi import FastAPI

from src.endpoints.ingestion import router as ingestion_router

app = FastAPI()

# Include ingestion routes
app.include_router(
    ingestion_router,
    prefix="/ingestion",
)

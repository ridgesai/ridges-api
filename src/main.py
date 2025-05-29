from fastapi import FastAPI

from src.endpoints import ingestion

app = FastAPI()

# Include ingestion routes
app.include_router(
    ingestion,
    prefix="ingestion",
)
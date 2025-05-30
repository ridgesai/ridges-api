from fastapi import FastAPI

from src.endpoints.ingestion import router

app = FastAPI()

# Include ingestion routes
app.include_router(
    router,
    prefix="/ingestion",
)

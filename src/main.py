from fastapi import FastAPI

from endpoints.validator import router as validator_router
from endpoints.miner import router as miner_router

app = FastAPI()

# Include ingestion routes
app.include_router(
    validator_router,
    prefix="/validator",
)

# Include retrieval routes
app.include_router(
    miner_router,
    prefix="/miner",
)

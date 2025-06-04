from fastapi import FastAPI

from endpoints.validator import router as validator_router
from endpoints.miner import router as miner_router
from endpoints.dashboard import router as dashboard_router

app = FastAPI()

# Include validator routes
app.include_router(
    validator_router,
    prefix="/validator",
)

# Include miner routes
app.include_router(
    miner_router,
    prefix="/miner",
)

# Include dashboard routes
app.include_router(
    dashboard_router,
    prefix="/dashboard",
)
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import logging
from datetime import datetime
import json

from src.utils.auth import verify_request
from src.db.models import CodegenChallenge, CodegenResponse, RegressionChallenge, RegressionResponse, Agent
from src.db.operations import DatabaseManager

from src.utils.config import PROBLEM_TYPES

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def get_codegen_challenge(challenge_id: str):
    challenge = db.get_codegen_challenges(challenge_id=challenge_id)

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=f"Codegen challenge {challenge_id} not found"
        )    
    
    return {
        "status": "success",
        "message": f"Codegen challenge {challenge_id} retrieved successfully",
        "challenge": challenge[0],
    }

async def get_codegen_challenges():
    challenges = db.get_codegen_challenges()

    if not challenges:
        raise HTTPException(
            status_code=404,
            detail="No codegen challenges found"
        )
    
    for challenge in challenges:
        challenge["response_count"] = len(db.get_codegen_challenge_responses(challenge_id=challenge["challenge_id"]))

    return {
        "status": "success",
        "message": "Codegen challenges retrieved successfully",
        "challenges": challenges,
    }

router = APIRouter()

routes = [
    ("/codegen-challenge", get_codegen_challenge),
    ("/codegen-challenges", get_codegen_challenges),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import Optional

from src.utils.auth import verify_request
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def get_codegen_challenge(challenge_id: str):
    challenge = db.get_codegen_challenges(challenge_id=challenge_id)

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"Codegen challenge {challenge_id} not found",
                "challenge": None,
                "responses": []
            }
        )
    
    responses = db.get_codegen_challenge_responses(challenge_id=challenge_id)
    challenge[0]["response_count"] = len(responses)
    
    return {
        "status": "success",
        "message": f"Codegen challenge {challenge_id} retrieved successfully",
        "challenge": challenge[0],
        "responses": responses
    }

async def get_codegen_challenges():
    challenges = db.get_codegen_challenges()

    if not challenges:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No codegen challenges found",
                "challenges": []
            }
        )
    
    for challenge in challenges:
        challenge["response_count"] = len(db.get_codegen_challenge_responses(challenge_id=challenge["challenge_id"]))

    return {
        "status": "success",
        "message": "Codegen challenges retrieved successfully",
        "challenges": challenges,
    }

async def get_miner_responses(min_score: Optional[float] = 0, min_response_count: Optional[int] = 0, sort_by_score: Optional[bool] = False):
    responses = db.get_codegen_challenge_responses()

    if not responses:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No miner responses found",
                "miners": []
            }
        )
    
    miner_responses = {}
    for response in responses:
        miner_hotkey = response.miner_hotkey
        if miner_hotkey not in miner_responses:
            miner_responses[miner_hotkey] = []
        miner_responses[miner_hotkey].append(response)
    
    miners = [{"miner_hotkey": hotkey, "response_count": len(responses), "responses": responses} for hotkey, responses in miner_responses.items() if len(responses) >= min_response_count]

    if sort_by_score:
        for miner in miners:
            scores = [response.score for response in miner["responses"]]
            miner["average_score"] = sum(scores) / len(scores)
        
        miners.sort(key=lambda x: x["average_score"], reverse=True)

    if min_score:
        miners = [miner for miner in miners if miner["average_score"] >= min_score]

    return {
        "status": "success",
        "message": "Miner responses retrieved successfully" if miners else "No miner responses found with the given parameters",
        "miners": miners
    }

router = APIRouter()

routes = [
    ("/codegen-challenge", get_codegen_challenge),
    ("/codegen-challenges", get_codegen_challenges),
    ("/miner-responses", get_miner_responses),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )
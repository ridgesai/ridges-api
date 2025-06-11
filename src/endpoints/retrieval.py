from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import Optional

from src.utils.auth import verify_request
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager()

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
    
    return {
        "status": "success",
        "message": f"Codegen challenge {challenge_id} retrieved successfully",
        "challenge": challenge[0],
        "responses": responses
    }

async def get_codegen_challenges(max_challenges: int = 5):
    if max_challenges > 150:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "message": "Max challenges must be less than 150",
                "challenge_count": 0,
                "challenges": []
            }
        )

    challenges = db.get_codegen_challenges()

    if not challenges:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No codegen challenges found",
                "challenge_count": 0,
                "challenges": []
            }
        )

    challenges = [challenge for challenge in challenges if challenge["response_count"] > 0]
    challenges.sort(key=lambda x: x["created_at"], reverse=True)
    challenges = challenges[:max_challenges]

    return {
        "status": "success",
        "message": f"Codegen challenges retrieved successfully",
        "challenge_count": len(challenges),
        "challenges": challenges,
    }

async def get_miner_responses(min_score: float = 0, min_response_count: int = 0, sort_by_score: bool = False, max_miners: int = 5):
    if max_miners > 150:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "message": "Max miners must be less than 150",
                "miner_count": 0,
                "miners": []
            }
        )

    responses = db.get_codegen_challenge_responses()

    if not responses:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No graded miner responses found",
                "miners": []
            }
        )
    
    miner_responses = {}
    for response in responses:
        miner_hotkey = response.miner_hotkey
        response.processing_time = (response.completed_at - response.received_at).total_seconds()
        if miner_hotkey not in miner_responses:
            miner_responses[miner_hotkey] = []
        miner_responses[miner_hotkey].append(response)
    
    miners = [{"miner_hotkey": hotkey, "response_count": len(responses), "responses": responses} for hotkey, responses in miner_responses.items() if len(responses) >= min_response_count]

    for miner in miners:
        scores = [response.score for response in miner["responses"] if response.score is not None]
        miner["average_score"] = sum(scores) / len(scores) if scores else 0
    
    if min_score:
        miners = [miner for miner in miners if miner.get("average_score", 0) >= min_score]

    if sort_by_score:
        miners.sort(key=lambda x: x.get("average_score", 0), reverse=True)

    miners = miners[:max_miners]

    return {
        "status": "success",
        "message": "Graded miner responses retrieved successfully" if miners else "No graded miner responses found with the given parameters",
        "miner_count": len(miners),
        "miners": miners
    }

async def get_single_miner_responses(miner_hotkey: str):
    responses = db.get_codegen_challenge_responses(miner_hotkey=miner_hotkey)

    if not responses:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"No miner graded responses found for miner {miner_hotkey}",
                "responses": []
            }
        )

    return {
        "status": "success",
        "message": f"Miner graded responses retrieved successfully for miner {miner_hotkey}",
        "details": {
            "response_count": len(responses),
            "responses": responses
        }
    }

router = APIRouter()

routes = [
    ("/codegen-challenge", get_codegen_challenge),
    ("/codegen-challenges", get_codegen_challenges),
    ("/miner-responses", get_miner_responses),
    ("/single-miner-responses", get_single_miner_responses),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )

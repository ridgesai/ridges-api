from fastapi import APIRouter, Depends, Request, HTTPException
import logging

from src.db.operations import DatabaseManager
from src.utils.auth import verify_request
from src.models.codegen_challenge_responses import CodegenChallengeResponses, ReturnedResponse

db = DatabaseManager("data.db")

logger = logging.getLogger(__name__)

async def get_challenge_responses(challenge_id: str, max_rows: int = 100):
    print(challenge_id)

    challenge = db.get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Requested challenge not found")
    
    responses = db.get_responses(challenge_id, max_rows)

    codegen_responses = []

    for response in responses:
        codegen_responses.append(ReturnedResponse(
            miner_hotkey=response.miner_hotkey,
            response_patch=response.response_patch,
            score=response.score,
            completion_time_seconds=(response.completed_at - response.received_at).total_seconds()
        ))

    return CodegenChallengeResponses(
        challenge=challenge,
        responses=codegen_responses
    )

router = APIRouter()

routes = [
    ("/challenge-responses", get_challenge_responses),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )
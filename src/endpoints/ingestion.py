from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import logging

from src.utils.auth import verify_request
from src.db.models import CodegenChallenge, CodegenResponse
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def codegen_challenges(data: List[CodegenChallenge]):
    try:
        for challenge in data:
            db.store_codegen_challenge(challenge)
    except Exception as e:
        logger.error(f"Error parsing codegen challenges: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Challenge {challenge.challenge_id} already exists in database")   

    return {
        "status": "success",
        "message": f"Successfully recorded {len(data)} codegen challenges",
    }


async def codegen_responses(data: List[CodegenResponse]):

    for response in data:
        try:
            db.store_codegen_response(response)
        except Exception as e:
            logger.error(f"Error parsing codegen responses: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Response with fron miner hotkey {response.miner_hotkey} for challenge {response.challenge_id} already exists in database")

    return {
        "status": "success",
        "message": f"Successfully recorded {len(data)} codegen responses",
    }


router = APIRouter()

routes = [
    ("/codegen-challenges", codegen_challenges), 
    ("/codegen-responses", codegen_responses)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

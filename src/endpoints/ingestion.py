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
    details = {
        "total_sent_codegen_challenges": len(data),
        "total_stored_codegen_challenges": 0,
        "total_unstored_codegen_challenges": 0,
        "list_of_stored_codegen_challenges": [],
        "list_of_unstored_codegen_challenges": [],
    }

    for challenge in data:
        result = db.store_codegen_challenge(challenge)
        if result == 0:
            details["total_unstored_codegen_challenges"] += 1
            details["list_of_unstored_codegen_challenges"].append(challenge.challenge_id + "-" + challenge.validator_hotkey)
        else:
            details["total_stored_codegen_challenges"] += 1
            details["list_of_stored_codegen_challenges"].append(challenge.challenge_id + "-" + challenge.validator_hotkey)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_codegen_challenges']} of {details['total_sent_codegen_challenges']} codegen challenges. {details['total_unstored_codegen_challenges']} challenges were not stored due to duplicate challenge ids",
    }


async def codegen_responses(data: List[CodegenResponse]):
    details = {
        "total_sent_codegen_responses": len(data),
        "total_stored_codegen_responses": 0,
        "total_unstored_codegen_responses": 0,
        "list_of_stored_codegen_responses": [],
        "list_of_unstored_codegen_responses": [],
    }

    for response in data:
        result = db.store_codegen_response(response)
        if result == 0:
            details["total_unstored_codegen_responses"] += 1
            details["list_of_unstored_codegen_responses"].append(response.challenge_id)
        else:
            details["total_stored_codegen_responses"] += 1
            details["list_of_stored_codegen_responses"].append(response.challenge_id)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_codegen_responses']} of {details['total_sent_codegen_responses']} codegen responses. {details['total_unstored_codegen_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations",
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

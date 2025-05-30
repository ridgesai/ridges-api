from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException
import logging
import json

from src.utils.auth import verify_request
from src.models import CodegenResponse, CodegenChallenge

from src.utils.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("data.db"))

async def raw_logs(data: List[Dict[str, Any]]):
    # TODO: implement log drain. Not sure how you want to do this
    
    return {
        "status": "error",
        "message": "not implemented",
    }

async def codegen_challenges(data: List[Dict[str, Any]]):
    challenges_to_record: List[CodegenChallenge] = []

    # Parse data into CodegenChallenge objects
    try:
        for item in data:
            # Parse string lists into actual lists
            if 'dynamic_checklist' in item and isinstance(item['dynamic_checklist'], str):
                item['dynamic_checklist'] = json.loads(item['dynamic_checklist'])
            if 'context_file_paths' in item and isinstance(item['context_file_paths'], str):
                item['context_file_paths'] = json.loads(item['context_file_paths'])
            challenges_to_record.append(CodegenChallenge(**item))
    except Exception as e:
        logger.error(f"Error parsing codegen challenges: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request body format: {str(e)}")
    
    # Store in database
    try:
        for challenge in challenges_to_record:
            db.store_codegen_challenge(challenge)
        logger.info(f"Successfully recorded {len(challenges_to_record)} challenges")
    except Exception as e:
        logger.error(f"Error storing codegen challenges: {str(e)}")

    return {
        "status": "success",
        "message": f"Successfully recorded {len(challenges_to_record)} responses",
    }


async def codegen_responses(data: List[Dict[str, Any]]):
    responses_to_record: List[CodegenResponse] = []

    try:
        for item in data:
            responses_to_record.append(CodegenResponse(**item))
    except Exception as e:
        logger.error(f"Error parsing codegen responses: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request body format: {str(e)}")
    
    # Store in database
    try:
        for response in responses_to_record:
            db.store_response(response)
        logger.info(f"Successfully recorded {len(responses_to_record)} responses")
    except Exception as e:
        logger.error(f"Error storing codegen responses: {str(e)}")

    return {
        "status": "success",
        "message": f"Successfully recorded {len(responses_to_record)} responses",
    }


router = APIRouter()

routes = [
    ("/logs", raw_logs),
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

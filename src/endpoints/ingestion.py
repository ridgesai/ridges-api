from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Request, HTTPException

from src.utils.auth import verify_request
from src.models import CodegenResponse, CodegenChallenge

async def raw_logs(data: List[Dict[str, Any]]):
    # TODO: implement log drain. Not sure how you want to do this
    
    return {
        "status": "error",
        "message": "not implemented",
    }

async def codegen_challenges(data: List[Dict[str, Any]]):
    challenges_to_record: List[CodegenChallenge] = []

    try:
        for item in data:
            challenges_to_record.append(CodegenChallenge(**item))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body format: {str(e)}")
    
    # TODO: store in database

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
        raise HTTPException(status_code=400, detail=f"Invalid request body format: {str(e)}")
    
    # TODO: store in database

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

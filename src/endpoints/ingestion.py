from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException
import logging
import json
import sqlite3
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.utils.auth import verify_request
from models.pydantic_models import ChallengeCreate, CodegenChallengeCreate, AgentCreate, ResponseCreate, ChallengeRead, CodegenChallengeRead, AgentRead, ResponseRead
from src.db.database import Challenge, CodegenChallenge, Agent, Response, DatabaseManager

#  from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def raw_logs(data: List[Dict[str, Any]]):
    # TODO: implement log drain. Not sure how you want to do this
    
    return {
        "status": "error",
        "message": "not implemented",
    }

async def upload_codegen_challenge(codegenChallengeRequest: CodegenChallengeCreate):
    try:
        codegenChallenge = CodegenChallenge(**codegenChallengeRequest.model_dump())
        db.add_codegen_challenge(codegenChallenge)
        
        baseChallenge = Challenge(
            challenge_id=codegenChallengeRequest.challenge_id, 
            created_at=codegenChallengeRequest.created_at, 
            type="codegen", 
            validator_hotkey=codegenChallengeRequest.validator_hotkey
        )
        db.add_challenge(baseChallenge)
    except IntegrityError as e:
        logger.error(f"Error uploading challenge - database integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Challenge already exists or violates constraints.")
    except SQLAlchemyError as e:
        logger.error(f"Error uploading challenge - database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    except Exception as e:
        logger.error(f"Error uploading challenge: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request body format.")
    
    return {
        "status": "success",
        "message": "Challenge uploaded successfully",
    }

# async def codegen_responses(data: List[Dict[str, Any]]):
#     responses_to_record: List[CodegenResponse] = []

#     try:
#         for item in data:
#             responses_to_record.append(CodegenResponse(**item))
#     except Exception as e:
#         logger.error(f"Error parsing codegen responses: {str(e)}")
#         raise HTTPException(status_code=400, detail=f"Invalid request body format: {str(e)}")
    
#     # Store in database
#     try:
#         for response in responses_to_record:
#             db.store_response(response)
#         logger.info(f"Successfully recorded {len(responses_to_record)} responses")
#     except Exception as e:
#         logger.error(f"Error storing codegen responses: {str(e)}")

#     return {
#         "status": "success",
#         "message": f"Successfully recorded {len(responses_to_record)} responses",
#     }


router = APIRouter()

routes = [
    ("/logs", raw_logs),
    ("/upload-codegen-challenge", upload_codegen_challenge), 
    # ("/codegen-responses", codegen_responses)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import zipfile
import shutil
import uuid
from botocore.exceptions import ClientError
import subprocess

from src.utils.auth import verify_request
from db.models import ChallengeCreate, CodegenChallengeCreate, AgentCreate, ResponseCreate, ChallengeRead, CodegenChallengeRead, AgentRead, ResponseRead
from db.schema import Challenge, CodegenChallenge, Agent, Response
from db.operations import DatabaseManager


logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def raw_logs(data: List[Dict[str, Any]]):
    # TODO: implement log drain. Not sure how you want to do this
    
    return {
        "status": "error",
        "message": "not implemented",
    }

async def upload_codegen_challenge(codegenChallengePayload: CodegenChallengeCreate):
    try:
        codegenChallenge = CodegenChallenge(**codegenChallengePayload.model_dump())
        db.add_codegen_challenge(codegenChallenge)
        
        challenge = Challenge(
            challenge_id=codegenChallengePayload.challenge_id, 
            created_at=codegenChallengePayload.created_at, 
            type="codegen", 
            validator_hotkey=codegenChallengePayload.validator_hotkey
        )
        db.add_challenge(challenge)
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

router = APIRouter()

routes = [
    ("/logs", raw_logs),
    ("/upload-codegen-challenge", upload_codegen_challenge)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["validator"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

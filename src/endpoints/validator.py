from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import boto3
import shutil

from src.utils.auth import verify_request
from src.utils.config import S3_BUCKET_NAME, AGENT_TYPES

from db.models import CodegenChallengeCreate
from db.schema import Challenge, CodegenChallenge
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

async def get_all_agents(type: str = None):
    if type and type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid agent type. Must be one of: {AGENT_TYPES}")
    
    try:
        agents = db.get_agents(type)
    except Exception as e:
        logger.error(f"Error getting all agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    return {
        "status": "success",
        "agents": agents,
    }

async def get_agent_metadata(agent_id: str):
    try:
        agent = db.get_agent(agent_id)
    except Exception as e:
        logger.error(f"Error getting agent metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "status": "success",
        "agent": agent,
    }

async def get_agent_zip(agent_id: str, background_tasks: BackgroundTasks):
    try:
        agent = db.get_agent(agent_id)
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Create temp directory
    temp_dir = Path('temp')
    temp_dir.mkdir(exist_ok=True)

    try:
        s3 = boto3.client('s3')
        s3.download_file(S3_BUCKET_NAME, f'{agent_id}/agent.zip', f'{temp_dir}/agent.zip')
    except Exception as e:
        logger.error(f"Error downloading agent from S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

    # Add cleanup task to run after response is sent
    background_tasks.add_task(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
    
    return FileResponse(path=f'{temp_dir}/agent.zip', filename='agent.zip')


router = APIRouter()

routes = [
    ("/logs", raw_logs, ["POST"]),
    ("/post/codegen-challenge", upload_codegen_challenge, ["POST"]),
    ("/get/all-agents", get_all_agents, ["GET"]),
    ("/get/agent-metadata", get_agent_metadata, ["GET"]),
    ("/get/agent-zip", get_agent_zip, ["GET"])
]

for path, endpoint, methods in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["validator"],
        dependencies=[Depends(verify_request)],
        methods=methods
    )

from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import boto3
import shutil

from src.utils.auth import verify_request
from src.utils.config import S3_BUCKET_NAME, PROBLEM_TYPES

from db.models import CodegenChallengeCreate, CodegenResponseCreate, RegressionChallengeCreate, RegressionResponseCreate
from db.schema import CodegenChallenge, CodegenResponse, RegressionResponse, RegressionChallenge
from db.operations import DatabaseManager


logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def post_codegen_challenges(codegenChallengePayload: List[CodegenChallengeCreate]):
    try:
        for challenge in codegenChallengePayload:
            codegen_challenge = CodegenChallenge(**challenge.model_dump())
            db.add_codegen_challenge(codegen_challenge)
    except IntegrityError as e:
        logger.error(f"Error uploading challenge - database integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Challenge already exists.")
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

async def post_regression_challenges(regressionChallengePayload: List[RegressionChallengeCreate]):
    try:
        for challenge in regressionChallengePayload:
            regression_challenge = RegressionChallenge(**challenge.model_dump())
            db.add_regression_challenge(regression_challenge)
    except IntegrityError as e:
        logger.error(f"Error uploading challenge - database integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Challenge already exists.")
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

async def post_codegen_responses(codegenResponsePayload: List[CodegenResponseCreate]):
    try:
        for response in codegenResponsePayload:
            codegen_response = CodegenResponse(**response.model_dump())
            db.add_codegen_response(codegen_response)
    except IntegrityError as e:
        logger.error(f"Error uploading response - database integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Response already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Error uploading response - database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    except Exception as e:
        logger.error(f"Error uploading response: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request body format.")
    
    return {
        "status": "success",
        "message": "Response uploaded successfully",
    }
    
async def post_regression_responses(regressionResponsePayload: List[RegressionResponseCreate]):
    try:
        for response in regressionResponsePayload:
            regression_response = RegressionResponse(**response.model_dump())
            db.add_regression_response(regression_response)
    except IntegrityError as e:
        logger.error(f"Error uploading response - database integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Response already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Error uploading response - database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    except Exception as e:
        logger.error(f"Error uploading response: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request body format.")
    
    return {
        "status": "success",
        "message": "Response uploaded successfully",
    }

async def get_agents(type: str = None):
    if type and type not in PROBLEM_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid agent type. Must be one of: {PROBLEM_TYPES}")
    
    try:
        agents = db.get_agents(type=type)
    except Exception as e:
        logger.error(f"Error getting all agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    if not agents and type:
        raise HTTPException(status_code=404, detail=f"No agents with type {type} found")
    elif not agents:
        raise HTTPException(status_code=404, detail=f"No agents found")
    
    return {
        "status": "success",
        "agents": agents,
    }

async def get_agent_metadata(agent_id: str):
    try:
        agent = db.get_agents(agent_id=agent_id)[0]
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
        agent = db.get_agents(agent_id=agent_id)[0]
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
    ("/post/codegen-challenges", post_codegen_challenges, ["POST"]),
    ("/post/codegen-responses", post_codegen_responses, ["POST"]),
    ("/post/regression-responses", post_regression_responses, ["POST"]),
    ("/post/regression-challenges", post_regression_challenges, ["POST"]),
    ("/get/agents", get_agents, ["GET"]),
    ("/get/agent-metadata", get_agent_metadata, ["GET"]),
    ("/get/agent-zip", get_agent_zip, ["GET"]),
]

for path, endpoint, methods in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["validator"],
        dependencies=[Depends(verify_request)],
        methods=methods
    )

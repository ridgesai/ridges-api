import boto3
import logging
from fastapi import HTTPException, APIRouter, Depends
from pathlib import Path

from src.utils.auth import verify_request
from src.utils.config import S3_BUCKET_NAME
from db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def get_agent_objects(agent_id: str, path: str = ""):
    try:
        agent = db.get_agents(agent_id=agent_id)
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    if not agent or len(agent) == 0:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Get agent and declare prefix
    agent = agent[0]
    prefix = f'{agent_id}/src/{path}'
    
    if not path or path.endswith("/"):
        # Get contents of prefix
        try:
            s3 = boto3.client('s3')
            contents = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)['Contents']
        except Exception as e:
            logger.error(f"Error downloading agent from S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
        
        # Get filenames
        filenames = []
        for obj in contents:
            filename = obj['Key'].split(prefix)[1]
            if "/" in filename:
                filename = filename.split("/")[0] + "/"
            filenames.append(filename)
        
        # Remove duplicates
        filenames = list(set(filenames))

        return {
            "status": "success",
            "filename": filenames,
        }
    
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=f'{agent_id}/src/{path}')
    except Exception as e:
        logger.error(f"Error downloading agent from S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
    
    file_content = response['Body'].read().decode('utf-8')
    filename = path.split("/")[-1]

    return {
        "status": "success",
        "filename": filename,
        "file_content": file_content,
    }

async def get_agent_responses(agent_id: str):
    try:
        responses = db.get_responses(agent_id=agent_id)
    except Exception as e:
        logger.error(f"Error getting responses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")
    
    if not responses:
        raise HTTPException(status_code=404, detail=f"No responses found for agent {agent_id}")
    
    responses_obj = []

    for response in responses:
        challenge = db.get_codegen_challenges(challenge_id=response.challenge_id)
        if not challenge:
            logger.error(f"Challenge {response.challenge_id} not found")
            continue
        challenge = challenge[0]
        response_obj = {
            "challenge": challenge,
            "response": response,
        }
        responses_obj.append(response_obj)
    
    return {
        "status": "success",
        "responses": responses_obj,
    }

router = APIRouter()

routes = [
    ("/get/agent-objects", get_agent_objects, ["GET"]),
    ("/get/agent-responses", get_agent_responses, ["GET"]),
]

for path, endpoint, methods in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["dashboard"],
        dependencies=[Depends(verify_request)],
        methods=methods
    )

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import logging
import boto3
import os
from dotenv import load_dotenv
from typing import List

from src.utils.auth import verify_request
from src.db.operations import DatabaseManager
from src.utils.config import PROBLEM_TYPES
from src.utils.chutes import ChutesManager

logger = logging.getLogger(__name__)

db = DatabaseManager()
chutes = ChutesManager()

load_dotenv()
s3_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

# Get version file
async def get_agent_file(agent_id: str):
    agent = db.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"Agent not found",
                "details": {
                    "agent_id": agent_id,
                    "agent_file": None
                }
            }
        )
    
    try:
        s3 = boto3.client('s3')
        agent_object = s3.get_object(Bucket=s3_bucket_name, Key=f"{agent_id}/agent.py")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Internal server error while retrieving agent file. Please try again later.",
                "details": {
                    "agent_id": agent_id,
                    "agent_file": None
                }
            }
        )
    
    headers = {
        "Content-Disposition": f'attachment; filename="agent.py"'
    }
    return StreamingResponse(agent_object['Body'], media_type='application/octet-stream', headers=headers)

router = APIRouter()

routes = [
    ("/agent-file", get_agent_file),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )

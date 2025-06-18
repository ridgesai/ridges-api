from typing import List, Optional, Union
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import logging
import uuid
from datetime import datetime
import boto3
import os
import ast
import sys
from dotenv import load_dotenv

from src.utils.config import PROBLEM_TYPES, PERMISSABLE_PACKAGES
from src.utils.auth import verify_request
from src.utils.models import Agent
from src.db.operations import DatabaseManager
from src.socket.server import WebSocketServer

logger = logging.getLogger(__name__)

load_dotenv()
s3_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
print(s3_bucket_name)

db = DatabaseManager()
server = WebSocketServer()

async def post_agent (
    agent_file: UploadFile = File(...),
    miner_hotkey: str = None,
):
    # TODO:Check if miner already has an agent qued, if so, rate limit the miner

    # Check if miner_hotkey is provided
    if not miner_hotkey:
        raise HTTPException(
            status_code=400,
            detail="miner_hotkey is required"
        )

    # Check filename
    if agent_file.filename != "agent.py":
        raise HTTPException(
            status_code=400,
            detail="File must be a python file named agent.py"
        )
    
    # Check file size
    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB in bytes
    file_size = 0
    content = b""
    for chunk in agent_file.file:
        file_size += len(chunk)
        content += chunk
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File size must not exceed 1MB"
            )
    # Reset file pointer
    await agent_file.seek(0)
    
    try:
        # Parse the file content
        tree = ast.parse(content.decode('utf-8'))
        
        # Check for if __name__ == "__main__"
        has_main_check = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    if isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__":
                        if len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq):
                            if isinstance(node.test.comparators[0], ast.Constant) and node.test.comparators[0].value == "__main__":
                                has_main_check = True
                                break
        
        if not has_main_check:
            raise HTTPException(
                status_code=400,
                detail='File must contain "if __name__ == "__main__":"'
            )
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    # Allow standard library packages (those that don't need pip install) and approved packages
                    if name.name in sys.stdlib_module_names or name.name in PERMISSABLE_PACKAGES:
                        continue
                    raise HTTPException(
                        status_code=400,
                        detail=f"Import '{name.name}' is not allowed. Only standard library and approved packages are permitted."
                    )
            elif isinstance(node, ast.ImportFrom):
                # Allow standard library packages (those that don't need pip install) and approved packages
                if node.module in sys.stdlib_module_names or node.module in PERMISSABLE_PACKAGES:
                    continue
                raise HTTPException(
                    status_code=400,
                    detail=f"Import from '{node.module}' is not allowed. Only standard library and approved packages are permitted."
                )

    except SyntaxError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Python syntax: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error validating the agent file: {str(e)}"
        )

    existing_agent = db.get_agent(miner_hotkey)
        
    agent_id = str(uuid.uuid4()) if not existing_agent else existing_agent.agent_id
    
    s3_client = boto3.client('s3')

    try:
        s3_client.upload_fileobj(agent_file.file, s3_bucket_name, f"{agent_id}/agent.py")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload agent to our database"
        )
    
    agent_object = Agent(
        agent_id=agent_id,
        miner_hotkey=existing_agent.miner_hotkey if existing_agent else miner_hotkey,
        created_at=existing_agent.created_at if existing_agent else datetime.now(),
        last_updated=datetime.now(),
        latest_version_id=existing_agent.latest_version_id + 1 if existing_agent else 0,
    )
    result = db.store_agent(agent_object)
    if result == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to store agent in our database"
        )

    await server.send_agent(agent_object)

    return {
        "status": "success",
        "details": {
            "agent_id": agent_id,
        },
        "message": f"Successfully updated agent {agent_id}" if existing_agent else f"Successfully created agent {agent_id}"
    }

router = APIRouter()

routes = [
    ("/agent", post_agent),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["upload"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

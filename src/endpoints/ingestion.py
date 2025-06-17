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
from src.utils.models import CodegenChallenge, CodegenResponse, RegressionChallenge, RegressionResponse, Agent, ValidatorVersion, Score
from src.db.operations import DatabaseManager
from src.socket.server import WebSocketServer

logger = logging.getLogger(__name__)

load_dotenv()
s3_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
print(s3_bucket_name)

db = DatabaseManager()
server = WebSocketServer()

async def post_codegen_challenges(data: List[CodegenChallenge], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
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
            details["list_of_unstored_codegen_challenges"].append(challenge.challenge_id)
        else:
            details["total_stored_codegen_challenges"] += 1
            details["list_of_stored_codegen_challenges"].append(challenge.challenge_id)

    logger.info(f"Successfully stored {details['total_stored_codegen_challenges']} of {details['total_sent_codegen_challenges']} codegen challenges. {details['total_unstored_codegen_challenges']} challenges were not stored due to duplicate challenge ids")
    logger.info(f"List of stored codegen challenges: {details['list_of_stored_codegen_challenges']}")
    logger.info(f"List of unstored codegen challenges: {details['list_of_unstored_codegen_challenges']}")

    if validator_hotkey != "LEGACY VALIDATOR":
        val_hotkey = validator_hotkey
    elif data[0].validator_hotkey:
        val_hotkey = data[0].validator_hotkey
    else:
        val_hotkey = "LEGACY VALIDATOR"

    validator_version_object = ValidatorVersion(
        validator_hotkey=val_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_codegen_challenges']} of {details['total_sent_codegen_challenges']} codegen challenges. {details['total_unstored_codegen_challenges']} challenges were not stored due to duplicate challenge ids",
    }

async def post_regression_challenges(data: List[RegressionChallenge], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    details = {
        "total_sent_regression_challenges": len(data),
        "total_stored_regression_challenges": 0,
        "total_unstored_regression_challenges": 0,
        "list_of_stored_regression_challenges": [],
        "list_of_unstored_regression_challenges": [],
    }

    for challenge in data:
        result = db.store_regression_challenge(challenge)
        if result == 0:
            details["total_unstored_regression_challenges"] += 1
            details["list_of_unstored_regression_challenges"].append(challenge.challenge_id)
        else:
            details["total_stored_regression_challenges"] += 1
            details["list_of_stored_regression_challenges"].append(challenge.challenge_id)

    logger.info(f"Successfully stored {details['total_stored_regression_challenges']} of {details['total_sent_regression_challenges']} regression challenges. {details['total_unstored_regression_challenges']} challenges were not stored due to duplicate challenge ids")
    logger.info(f"List of stored regression challenges: {details['list_of_stored_regression_challenges']}")
    logger.info(f"List of unstored regression challenges: {details['list_of_unstored_regression_challenges']}")

    if validator_hotkey != "LEGACY VALIDATOR":
        val_hotkey = validator_hotkey
    elif data[0].validator_hotkey:
        val_hotkey = data[0].validator_hotkey
    else:
        val_hotkey = "LEGACY VALIDATOR"

    validator_version_object = ValidatorVersion(
        validator_hotkey=val_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_regression_challenges']} of {details['total_sent_regression_challenges']} regression challenges. {details['total_unstored_regression_challenges']} challenges were not stored due to duplicate challenge ids",
    }

async def post_codegen_responses(data: List[CodegenResponse], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    details = {
        "total_sent_codegen_responses": len(data),
        "total_new_codegen_responses": 0,
        "total_updated_codegen_responses": 0,
        "list_of_new_codegen_responses": [],
        "list_of_updated_codegen_responses": [],
    }

    for response in data:
        result = db.store_codegen_response(response)
        if result == 0:
            details["total_new_codegen_responses"] += 1
            details["list_of_new_codegen_responses"].append(response.challenge_id + "-" + response.miner_hotkey)
        else:
            details["total_updated_codegen_responses"] += 1
            details["list_of_updated_codegen_responses"].append(response.challenge_id + "-" + response.miner_hotkey)

    logger.info(f"Successfully stored {details['total_new_codegen_responses']} of {details['total_sent_codegen_responses']} codegen responses. {details['total_updated_codegen_responses']} responses were updated due to duplicate challenge id / miner hotkey combinations")
    logger.info(f"List of new codegen responses: {details['list_of_new_codegen_responses']}")
    logger.info(f"List of updated codegen responses: {details['list_of_updated_codegen_responses']}")

    validator_version_object = ValidatorVersion(
        validator_hotkey=validator_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully uploaded {details['total_new_codegen_responses']} new codegen responses and updated {details['total_updated_codegen_responses']} existing codegen responses",
    }

async def post_regression_responses(data: List[RegressionResponse], validator_hotkey = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    details = {
        "total_sent_regression_responses": len(data),
        "total_stored_regression_responses": 0,
        "total_unstored_regression_responses": 0,
        "list_of_stored_regression_responses": [],
        "list_of_unstored_regression_responses": [],
    }

    for response in data:
        result = db.store_regression_response(response)
        if result == 0:
            details["total_unstored_regression_responses"] += 1
            details["list_of_unstored_regression_responses"].append(response.challenge_id + "-" + response.miner_hotkey)
        else:
            details["total_stored_regression_responses"] += 1
            details["list_of_stored_regression_responses"].append(response.challenge_id + "-" + response.miner_hotkey)

    logger.info(f"Successfully stored {details['total_stored_regression_responses']} of {details['total_sent_regression_responses']} regression responses. {details['total_unstored_regression_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations")
    logger.info(f"List of stored regression responses: {details['list_of_stored_regression_responses']}")
    logger.info(f"List of unstored regression responses: {details['list_of_unstored_regression_responses']}")

    validator_version_object = ValidatorVersion(
        validator_hotkey=validator_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_regression_responses']} of {details['total_sent_regression_responses']} regression responses. {details['total_unstored_regression_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations",
    }

async def post_agent (
    agent_file: UploadFile = File(...),
    miner_hotkey: str = None,
    type: str = None,
    registered_agent_id: Optional[str] = None,
):
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
    
    # Check if miner_hotkey is provided
    if not miner_hotkey:
        raise HTTPException(
            status_code=400,
            detail="miner_hotkey is required"
        )

    # Check if type is provided and is valid
    if not type or type not in PROBLEM_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type is required and must be one of {PROBLEM_TYPES}"
        )
    
    existing_agent = None
    if registered_agent_id:
        existing_agent = db.get_agent(registered_agent_id)
        if not existing_agent:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {registered_agent_id} not found"
            )
        
    agent_id = str(uuid.uuid4()) if not registered_agent_id else registered_agent_id
    
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
        type=existing_agent.type if existing_agent else type,
        version=existing_agent.version + 1 if existing_agent else 1,
        elo=existing_agent.elo if existing_agent else 500,
        num_responses=existing_agent.num_responses if existing_agent else 0
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
 
async def post_scores(data: Union[List[Score], Score]):
    details = {
        "total_sent_scores": len(data) if isinstance(data, list) else 1,
        "total_stored_scores": 0,
        "total_unstored_scores": 0,
        "list_of_stored_scores": [],
        "list_of_unstored_scores": [],
    }

    if isinstance(data, list):
        for score in data:
            result = db.store_score(score)
            if result == 0:
                details["total_unstored_scores"] += 1
                details["list_of_unstored_scores"].append(score)
            else:
                details["total_stored_scores"] += 1
                details["list_of_stored_scores"].append(score)
    else:
        result = db.store_score(data)
        if result == 0:
            details["total_unstored_scores"] += 1
            details["list_of_unstored_scores"].append(data)
        else:
            details["total_stored_scores"] += 1
            details["list_of_stored_scores"].append(data)

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_scores']} of {details['total_sent_scores']} scores. {details['total_unstored_scores']} scores were not stored due to duplicate validator_hotkey / miner_hotkey combinations",
    }

router = APIRouter()

routes = [
    ("/codegen-challenges", post_codegen_challenges), 
    ("/regression-challenges", post_regression_challenges),
    ("/codegen-responses", post_codegen_responses),
    ("/regression-responses", post_regression_responses),
    ("/scores", post_scores),
    ("/agent", post_agent),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

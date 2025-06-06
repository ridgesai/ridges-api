from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import logging
import zipfile
import uuid
import asyncio
import subprocess
import shutil
from datetime import datetime

from src.utils.auth import verify_request
from src.db.models import CodegenChallenge, CodegenResponse, RegressionChallenge, RegressionResponse, Agent
from src.db.operations import DatabaseManager

from src.utils.config import PROBLEM_TYPES

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

async def post_codegen_challenges(data: List[CodegenChallenge]):
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

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_codegen_challenges']} of {details['total_sent_codegen_challenges']} codegen challenges. {details['total_unstored_codegen_challenges']} challenges were not stored due to duplicate challenge ids",
    }

async def post_regression_challenges(data: List[RegressionChallenge]):
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

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_regression_challenges']} of {details['total_sent_regression_challenges']} regression challenges. {details['total_unstored_regression_challenges']} challenges were not stored due to duplicate challenge ids",
    }

async def post_codegen_responses(data: List[CodegenResponse]):
    details = {
        "total_sent_codegen_responses": len(data),
        "total_stored_codegen_responses": 0,
        "total_unstored_codegen_responses": 0,
        "list_of_stored_codegen_responses": [],
        "list_of_unstored_codegen_responses": [],
    }

    for response in data:
        result = db.store_codegen_response(response)
        if result == 0:
            details["total_unstored_codegen_responses"] += 1
            details["list_of_unstored_codegen_responses"].append(response.challenge_id + "-" + response.miner_hotkey)
        else:
            details["total_stored_codegen_responses"] += 1
            details["list_of_stored_codegen_responses"].append(response.challenge_id + "-" + response.miner_hotkey)

    logger.info(f"Successfully stored {details['total_stored_codegen_responses']} of {details['total_sent_codegen_responses']} codegen responses. {details['total_unstored_codegen_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations")
    logger.info(f"List of stored codegen responses: {details['list_of_stored_codegen_responses']}")
    logger.info(f"List of unstored codegen responses: {details['list_of_unstored_codegen_responses']}")

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_codegen_responses']} of {details['total_sent_codegen_responses']} codegen responses. {details['total_unstored_codegen_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations",
    }

async def post_regression_responses(data: List[RegressionResponse]):
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

    return {
        "status": "success",
        "details": details,
        "message": f"Successfully stored {details['total_stored_regression_responses']} of {details['total_sent_regression_responses']} regression responses. {details['total_unstored_regression_responses']} responses were not stored due to duplicate challenge id / miner hotkey combinations",
    }

async def post_agent (
    zip_file: UploadFile = File(...),
    miner_hotkey: str = None,
    type: str = None,
    registered_agent_id: Optional[str] = None,
):
    # Check if file is a zip file
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="File must be a zip file"
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
    
    # if provided_agent_id:
    #     agent = db.get_agent(provided_agent_id)
    #     if not agent:
    #         raise HTTPException(
    #             status_code=400,
    #             detail=f"Agent {agent_id} not found"
    #         )
    
    # Create a temporary directory for unzipping
    agent_id = uuid.uuid4() if not registered_agent_id else registered_agent_id
    temp_dir = Path(f"agent_{agent_id}")
    temp_dir.mkdir(exist_ok=True)

    async def process_zip():
        content = await zip_file.read()
        temp_zip = temp_dir / "agent.zip"
        with open(temp_zip, "wb") as f:
            f.write(content)
        
        src_dir = temp_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        total_size = 0
        max_size = 1 * 1024 * 1024
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            file_list = zip_ref.infolist()
            
            root_folder = None
            for file_info in file_list:
                path_parts = file_info.filename.split('/')
                if len(path_parts) > 1:
                    root_folder = path_parts[0]
                    break
            
            for file_info in file_list:
                if total_size + file_info.file_size > max_size:
                    raise HTTPException(
                        status_code=400,
                        detail="Unzipped content would exceed 1MB limit. Please reduce the size of the zip file."
                    )
                
                if file_info.filename == root_folder + '/':
                    continue
                
                if root_folder and file_info.filename.startswith(root_folder + '/'):
                    new_filename = file_info.filename[len(root_folder) + 1:]
                    file_info.filename = new_filename
                
                zip_ref.extract(file_info, src_dir)
                total_size += file_info.file_size

    try:
        await asyncio.wait_for(process_zip(), timeout=10.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Operation timed out after 10 seconds. Please reduce the size of the zip file."
        )

    subprocess.run(
        ['aws', 's3', 'sync', str(temp_dir), f's3://ridges-agents/{agent_id}'],
        capture_output=True,
        text=True,
        check=True
    )

    # If agent_id is provided, get the agent from the database
    if registered_agent_id:
        agent = db.get_agent(agent_id)
        created_at = agent.created_at
        version = agent.version + 1
        elo = agent.elo
        num_responses = agent.num_responses
    else:
        created_at = datetime.now()
        version = 1
        elo = 500
        num_responses = 0

    agent = Agent(
            agent_id=str(agent_id),
            miner_hotkey=miner_hotkey,
            created_at=created_at,
            last_updated=datetime.now(),
            type=type,
            version=version,
            elo=elo,
            num_responses=num_responses
        )
    # db.add_agent(agent)

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    return {
        "status": "success",
        "message": f"Agent {str(agent_id)} stored successfully",
    }

router = APIRouter()

routes = [
    ("/codegen-challenges", post_codegen_challenges), 
    ("/regression-challenges", post_regression_challenges),
    ("/codegen-responses", post_codegen_responses),
    ("/regression-responses", post_regression_responses),
    ("/agents", post_agent),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

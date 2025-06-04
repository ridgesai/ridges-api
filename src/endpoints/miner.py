from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile
import logging
import zipfile
import shutil
import uuid
from botocore.exceptions import ClientError
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.utils.config import PROBLEM_TYPES
from src.utils.auth import verify_request

from db.schema import Agent
from db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

router = APIRouter()

async def post_agent(
    zip_file: UploadFile = File(...),
    miner_hotkey: str = None,
    type: str = None,
    agent_id: Optional[str] = None
):
    # Check if file is a zip file
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="File must be a zip file"
        )
    
    # Validate required parameters
    if not miner_hotkey:
        raise HTTPException(
            status_code=400,
            detail="miner_hotkey is required"
        )
    if not type or type not in PROBLEM_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type is required and must be one of {PROBLEM_TYPES}"
        )
    
    # If agent_id is provided, get the agent from the database
    if agent_id:
        agent = db.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} not found"
            )
    
    # Create a temporary directory for unzipping
    new_agent_id = uuid.uuid4() if not agent_id else agent_id
    temp_dir = Path(f"agent_{new_agent_id}")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Read the zip file content
        content = await zip_file.read()
        # Create a temporary file to store the zip content
        temp_zip = temp_dir / "agent.zip"
        with open(temp_zip, "wb") as f:
            f.write(content)
        
        # Create src directory
        src_dir = temp_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Initialize size tracking
        total_size = 0
        max_size = 1 * 1024 * 1024  # 1MB in bytes
        
        # Open and process the zip file
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Get list of file information
            file_list = zip_ref.infolist()
            
            # Get the root folder name (first path component of any file)
            root_folder = None
            for file_info in file_list:
                path_parts = file_info.filename.split('/')
                if len(path_parts) > 1:
                    root_folder = path_parts[0]
                    break
            
            # Process each file in the zip
            for file_info in file_list:
                # Check if this file would exceed our size limit
                if total_size + file_info.file_size > max_size:
                    raise HTTPException(
                        status_code=400,
                        detail="Unzipped content would exceed 1MB limit"
                    )
                
                # Skip the root folder itself
                if file_info.filename == root_folder + '/':
                    continue
                
                # Remove root folder from path and extract
                if root_folder and file_info.filename.startswith(root_folder + '/'):
                    new_filename = file_info.filename[len(root_folder) + 1:]
                    file_info.filename = new_filename
                
                # Extract the file into src subdirectory
                zip_ref.extract(file_info, src_dir)
                total_size += file_info.file_size
        
        # Store in S3 with CLI
        subprocess.run(
            ['aws', 's3', 'sync', str(temp_dir), f's3://ridges-agents/{new_agent_id}'],
            capture_output=True,
            text=True,
            check=True
        )

        # If agent_id is provided, get the agent from the database
        if agent_id:
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

        # Store in database
        agent = Agent(
            agent_id=str(new_agent_id),
            miner_hotkey=miner_hotkey,
            created_at=created_at,
            type=type,
            version=version,
            elo=elo,
            num_responses=num_responses
        )
        db.add_agent(agent)
        
        return {
            "status": "success",
            "message": f"Agent {str(new_agent_id)} stored successfully",
        }
        
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="Invalid zip file format"
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail="Error storing agent"
        )
    except Exception as e:
        logger.error(f"Error uploading agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error uploading agent"
        )
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

router = APIRouter()

routes = [
    ("/post/agent", post_agent, ["POST"])
]

for path, endpoint, methods in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["miner"],
        dependencies=[Depends(verify_request)],
        methods=methods
    )

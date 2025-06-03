from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import zipfile
import shutil
import uuid
from botocore.exceptions import ClientError
import subprocess
from pathlib import Path

from src.utils.auth import verify_request
from db.operations import DatabaseManager


logger = logging.getLogger(__name__)

db = DatabaseManager(Path("platform.db"))

router = APIRouter()

async def upload_agent(zip_file: UploadFile = File(...)):
    # Check if file is a zip file
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="File must be a zip file"
        )
    
    # Create a temporary directory for unzipping
    agent_id = uuid.uuid4()
    temp_dir = Path(f"agent_{agent_id}")
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
            
            # Process each file in the zip
            for file_info in file_list:
                # Check if this file would exceed our size limit
                if total_size + file_info.file_size > max_size:
                    raise HTTPException(
                        status_code=400,
                        detail="Unzipped content would exceed 1MB limit"
                    )
                
                # Extract the file into src subdirectory
                zip_ref.extract(file_info, src_dir)
                total_size += file_info.file_size
        
        # Store in S3 with CLI
        subprocess.run(
            ['aws', 's3', 'sync', str(temp_dir), f's3://ridges-agents/{agent_id}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": "Agent stored successfully",
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
        logger.error(f"Error processing zip file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing zip file"
        )
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

router = APIRouter()

routes = [
    ("/upload-agent", upload_agent)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["miner"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

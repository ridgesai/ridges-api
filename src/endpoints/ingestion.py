from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException
import logging
from datetime import datetime
from src.utils.auth import verify_request
from src.db.models import CodegenChallenge, CodegenResponse, RegressionChallenge, RegressionResponse, ValidatorVersion, Score
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

# Global database manager instance (singleton)
db = DatabaseManager()

async def post_codegen_challenges(data: List[CodegenChallenge], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    result = db.store_codegen_challenges(data)

    if result == 0:
        raise HTTPException(status_code=500, detail="An error occurred while storing codegen challenges")

    logger.info(f"Successfully stored codegen challenges")

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
        "message": f"Successfully stored codegen challenges",
    }

async def post_regression_challenges(data: List[RegressionChallenge], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    result = db.store_regression_challenges(data)

    if result == 0:
        raise HTTPException(status_code=500, detail="An error occurred while storing regression challenges")

    logger.info(f"Successfully stored regression challenges")

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
        "message": f"Successfully stored regression challenges",
    }

async def post_codegen_responses(data: List[CodegenResponse], validator_hotkey: str = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    result = db.store_codegen_responses(data)

    if result == 0:
        raise HTTPException(status_code=500, detail="An error occurred while storing codegen responses")

    logger.info(f"Successfully stored codegen responses")

    validator_version_object = ValidatorVersion(
        validator_hotkey=validator_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "message": f"Successfully stored codegen responses",
    }

async def post_regression_responses(data: List[RegressionResponse], validator_hotkey = "LEGACY VALIDATOR", validator_version: str = "LEGACY"):
    result = db.store_regression_responses(data)

    if result == 0:
        raise HTTPException(status_code=500, detail="An error occurred while storing regression responses")

    logger.info(f"Successfully stored regression responses")

    validator_version_object = ValidatorVersion(
        validator_hotkey=validator_hotkey,
        version=validator_version,
        timestamp=datetime.now()
    )
    db.store_validator_version(validator_version_object)

    return {
        "status": "success",
        "message": f"Successfully stored regression responses",
    }
 
async def post_scores(data: List[Score]):
    if not data:
        return {
            "status": "failure",
            "message": "no scores to store",
        }
    
    db.store_scores(data)

    return {
        "status": "success",
        "message": f"Successfully stored {len(data)} scores",
    }

router = APIRouter()

routes = [
    ("/codegen-challenges", post_codegen_challenges), 
    ("/regression-challenges", post_regression_challenges),
    ("/codegen-responses", post_codegen_responses),
    ("/regression-responses", post_regression_responses),
    ("/scores-list", post_scores)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

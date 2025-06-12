from typing import List, Union
from fastapi import APIRouter, Depends
import logging
from datetime import datetime
from src.utils.auth import verify_request
from src.db.models import CodegenChallenge, CodegenResponse, RegressionChallenge, RegressionResponse, ValidatorVersion, Score
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

db = DatabaseManager()

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
    # ("/scores", post_scores)
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["ingestion"],
        dependencies=[Depends(verify_request)],
        methods=["POST"]
    )

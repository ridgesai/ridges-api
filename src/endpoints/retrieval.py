from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import Optional

from src.utils.auth import verify_request
from src.utils.cache import cache_manager, invalidate_cache_pattern
from src.db.operations import DatabaseManager

logger = logging.getLogger(__name__)

# Global database manager instance (singleton)
db = DatabaseManager()

async def get_codegen_challenge(challenge_id: str):
    challenge = db.get_codegen_challenges(challenge_id=challenge_id)

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"Codegen challenge {challenge_id} not found",
                "challenge": None,
                "responses": []
            }
        )
    
    responses = db.get_codegen_challenge_responses(challenge_id=challenge_id)
    print(len(responses))

    return {
        "status": "success",
        "message": f"Codegen challenge {challenge_id} retrieved successfully",
        "challenge": challenge[0],
        "responses": responses
    }

async def get_codegen_challenges(max_challenges: int = 5):
    if max_challenges > 150:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "message": "Max challenges must be less than 150",
                "challenge_count": 0,
                "challenges": []
            }
        )

    challenges = db.get_codegen_challenges()

    if not challenges:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No codegen challenges found",
                "challenge_count": 0,
                "challenges": []
            }
        )

    challenges = [challenge for challenge in challenges if challenge["response_count"] > 0]
    challenges.sort(key=lambda x: x["created_at"], reverse=True)
    challenges = challenges[:max_challenges]

    return {
        "status": "success",
        "message": f"Codegen challenges retrieved successfully",
        "challenge_count": len(challenges),
        "challenges": challenges,
    }

async def get_miner_responses(min_score: float = 0, min_response_count: int = 0, sort_by_score: bool = False, max_miners: int = 5):
    if max_miners > 150:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "message": "Max miners must be less than 150",
                "miner_count": 0,
                "miners": []
            }
        )

    miners = db.get_miner_responses(
        min_score=min_score,
        min_response_count=min_response_count,
        sort_by_score=sort_by_score,
        max_miners=max_miners
    )

    if not miners:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": "No graded miner responses found",
                "miners": []
            }
        )

    return {
        "status": "success",
        "message": "Graded miner responses retrieved successfully" if miners else "No graded miner responses found with the given parameters",
        "miner_count": len(miners),
        "miners": miners
    }

async def get_single_miner_responses(miner_hotkey: str):
    responses_obj = db.get_miner_responses(miner_hotkey=miner_hotkey)

    if not responses_obj:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "fail",
                "message": f"No miner graded responses found for miner {miner_hotkey}",
                "responses": []
            }
        )
    
    responses = responses_obj[0]['responses']

    return {
        "status": "success",
        "message": f"Miner graded responses retrieved",
        "details": {
            "miner_hotkey": miner_hotkey,
            "response_count": len(responses),
            "responses": responses
        }
    }

async def get_cache_stats():
    """Get cache statistics for monitoring."""
    stats = cache_manager.get_stats()
    return {
        "status": "success",
        "message": "Cache statistics retrieved successfully",
        "cache_stats": stats
    }

async def clear_cache():
    """Clear all cache entries (admin endpoint)."""
    cache_manager.clear()
    return {
        "status": "success",
        "message": "Cache cleared successfully"
    }

async def invalidate_cache(pattern: str):
    """Invalidate cache entries matching a pattern."""
    if not pattern or len(pattern) < 3:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "fail",
                "message": "Pattern must be at least 3 characters long"
            }
        )
    
    count = invalidate_cache_pattern(pattern)
    return {
        "status": "success",
        "message": f"Invalidated {count} cache entries matching pattern: {pattern}",
        "invalidated_count": count
    }

router = APIRouter()

routes = [
    ("/codegen-challenge", get_codegen_challenge),
    ("/codegen-challenges", get_codegen_challenges),
    ("/miner-responses", get_miner_responses),
    ("/single-miner-responses", get_single_miner_responses),
]

# Cache management routes (admin endpoints)
cache_routes = [
    ("/cache/stats", get_cache_stats),
    ("/cache/clear", clear_cache),
    ("/cache/invalidate", invalidate_cache),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["retrieval"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )

# Add cache management routes
for path, endpoint in cache_routes:
    # Get cache stats endpoint
    if "stats" in path:
        router.add_api_route(
            path,
            endpoint,
            tags=["cache"],
            dependencies=[Depends(verify_request)],
            methods=["GET"]
        )
    # Clear cache endpoint  
    elif "clear" in path:
        router.add_api_route(
            path,
            endpoint,
            tags=["cache"],
            dependencies=[Depends(verify_request)],
            methods=["POST"]
        )
    # Invalidate cache endpoint
    elif "invalidate" in path:
        router.add_api_route(
            path,
            endpoint,
            tags=["cache"],
            dependencies=[Depends(verify_request)],
            methods=["POST"]
        )

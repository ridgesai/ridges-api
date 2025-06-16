import asyncio
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from src.utils.auth import verify_request
from src.utils.chutes import ChutesManager

chutes = ChutesManager()

async def embedding(input: str):
    try:
        embedding = chutes.embed(input)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get embedding due to internal server error. Please try again later.")
    
    return embedding

async def inference(challenge_id: str, miner_hotkey: str, input_text: str = None, input_code: str = None, return_text: bool = False, return_code: bool = False, model: str = None):

    if not input_text and not input_code:
        raise HTTPException(status_code=400, detail="Either input_text or input_code must be provided.")

    if not return_text and not return_code:
        raise HTTPException(status_code=400, detail="Either return_text or return_code must be True.")

    try:
        return await chutes.inference(challenge_id, miner_hotkey, input_text, input_code, return_text, return_code, model)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to get inference due to internal server error. Please try again later.")

router = APIRouter()

routes = [
    ("/embedding", embedding),
    ("/inference", inference),
]

for path, endpoint in routes:
    router.add_api_route(
        path,
        endpoint,
        tags=["agents"],
        dependencies=[Depends(verify_request)],
        methods=["GET"]
    )

if __name__ == "__main__":
    chutes = ChutesManager()
    print(asyncio.run(chutes.inference("Tell me a 250 word story.", "", True, True)))

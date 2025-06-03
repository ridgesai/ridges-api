# from fastapi import APIRouter, Depends, Request, HTTPException
# import logging

# from src.db.operations import DatabaseManager
# from src.utils.auth import verify_request
# from src.models.codegen_challenge_responses import CodegenChallengeResponses, ReturnedResponse
# from src.models.miner_responses import MinerResponses, ReturnedCodegenChallenge, ReturnedCodegenResponses

# db = DatabaseManager("data.db")

# logger = logging.getLogger(__name__)

# async def get_challenge_responses(challenge_id: str, max_rows: int = 100):

#     challenge = db.get_challenge(challenge_id)
#     if not challenge:
#         raise HTTPException(status_code=404, detail="Requested challenge not found")
    
#     try:
#         responses = db.get_responses(challenge_id, max_rows)

#         stripped_responses = []

#         for response in responses:
#             stripped_responses.append(ReturnedResponse(
#                 miner_hotkey=response.miner_hotkey,
#                 response_patch=response.response_patch,
#                 score=response.score,
#                 completion_time_seconds=(response.completed_at - response.received_at).total_seconds()
#             ))

#         return CodegenChallengeResponses(
#             challenge=challenge,
#             responses=stripped_responses
#         )
    
#     except Exception as e:
#         logger.error(f"Error getting challenge responses: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
    
# async def get_miner_responses(miner_hotkey: str, max_rows: int = 100):

#     responses = db.get_miner_responses(miner_hotkey, max_rows)
#     if responses == []:
#         raise HTTPException(status_code=404, detail="No responses found. The miner with the requested hotkey does not exist or the has not been evaluated for any challenges yet.")

#     stripped_responses = []

#     for response in responses:
#         challenge = db.get_challenge(response.challenge_id)
#         stripped_responses.append(
#             ReturnedCodegenResponses(
#                 codegen_challenge=ReturnedCodegenChallenge(
#                     challenge_id=challenge.challenge_id,
#                     problem_statement=challenge.problem_statement,
#                     dynamic_checklist=challenge.dynamic_checklist,
#                     repository_name=challenge.repository_name,
#                     context_file_paths=challenge.context_file_paths
#                 ),
#                 completion_time_seconds=(response.completed_at - response.received_at).total_seconds(),
#                 score=response.score,
#                 patch=response.response_patch
#             )
#         )

#     return MinerResponses (
#         miner_hotkey=miner_hotkey,
#         responses=stripped_responses
#     )
    
# router = APIRouter()

# routes = [
#     ("/codegen-challenges", get_challenge_responses),
#     ("/codegen-responses", get_miner_responses),
# ]

# for path, endpoint in routes:
#     router.add_api_route(
#         path,
#         endpoint,
#         tags=["retrieval"],
#         dependencies=[Depends(verify_request)],
#         methods=["GET"]
#     )

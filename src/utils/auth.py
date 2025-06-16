from fastapi import Request, Header, HTTPException
from fiber import constants as cst
from fiber import utils
from fiber.chain.signatures import get_hash, verify_signature
from fiber.miner.security.nonce_management import NonceManager

# Create a single NonceManager instance that can be reused
nonce_manager = None

def get_config():
    if nonce_manager is None:
        nonce_manager = NonceManager()
    
    return nonce_manager

async def verify_request(
    request: Request,
    validator_hotkey: str = Header(..., alias=cst.VALIDATOR_HOTKEY),
    signature: str = Header(..., alias=cst.SIGNATURE),
    miner_hotkey: str = Header(..., alias=cst.MINER_HOTKEY),
    nonce: str = Header(..., alias=cst.NONCE),
    nonce_manager: NonceManager = get_config()
):
    if not nonce_manager.nonce_is_valid(nonce):
        raise HTTPException(
            status_code=401,
            detail="Oi, that nonce is not valid!",
        )
    
    body = await request.body()

    # Treat empty body (e.g., GET requests) as None to align with how clients
    # construct the signing message (they pass payload_hash=None for GET).
    payload_hash = None if not body else get_hash(body)
    message = utils.construct_header_signing_message(nonce=nonce, miner_hotkey=miner_hotkey, payload_hash=payload_hash)
    if not verify_signature(
        message=message,
        signer_ss58_address=validator_hotkey,
        signature=signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Oi, invalid signature, you're not who you said you were!",
        )

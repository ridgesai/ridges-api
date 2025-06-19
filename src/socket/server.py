import asyncio
import websockets
import json
from typing import Set, Optional

from src.utils.logging import get_logger
from src.socket.server_helpers import upsert_evaluation_run, get_next_evaluation, get_agent, create_evaluation, start_evaluation, finish_evaluation

logger = get_logger(__name__)

class WebSocketServer:
    _instance: Optional['WebSocketServer'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        if not self._initialized:
            self.host = host
            self.port = port
            self.uri = f"ws://{host}:{port}"
            self.clients: dict = {}  # Changed from Set to dict: {websocket: {"val_hotkey": str, "commit_hash": str}}
            self.server = None
            self._initialized = True
            asyncio.create_task(self.start())
    
    @classmethod
    def get_instance(cls) -> 'WebSocketServer':
        """Get the singleton instance of WebSocketServer"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def handle_connection(self, websocket):
        # Add new client to the set
        self.clients[websocket] = {"val_hotkey": None, "version_commit_hash": None}
        logger.info(f"Validator at {websocket.remote_address} connected to platform socket. Total validators connected: {len(self.clients)}")
        
        try:
            # Keep the connection alive and wait for messages
            while True:
                # Wait for client's response
                response = await websocket.recv()
                response_json = json.loads(response)

                if response_json["event"] == "validator-version":
                    self.clients[websocket]["val_hotkey"] = response_json["validator_hotkey"]
                    self.clients[websocket]["version_commit_hash"] = response_json["version_commit_hash"]
                    logger.info(f"Validator at {websocket.remote_address} has sent their validator version and version commit hash to the platform socket. Validator hotkey: {self.clients[websocket]['val_hotkey']}, Version commit hash: {self.clients[websocket]['version_commit_hash']}")

                if response_json["event"] == "get-next-evaluation":
                    validator_hotkey = self.clients[websocket]["val_hotkey"]
                    socket_message = await self.get_next_evaluation(validator_hotkey)
                    if socket_message:
                        try:
                            await websocket.send(json.dumps(socket_message))
                            logger.info(f"Platform socket sent requested evaluation to validator at {websocket.remote_address} with hotkey {validator_hotkey}")
                        except websockets.ConnectionClosed:
                            logger.warning(f"Failed to send requested evaluation to validator at {websocket.remote_address} with hotkey {validator_hotkey}")
                    else:
                        logger.info(f"No evaluations available for validator at {websocket.remote_address} with hotkey {validator_hotkey}")
                
                if response_json["event"] == "start-evaluation":
                    logger.info(f"Validator {websocket.remote_address} with hotkey {self.clients[websocket]['val_hotkey']} has started an evaluation {response_json['evaluation_id']}. Attempting to update the evaluation in the database.")
                    start_evaluation(response_json["evaluation_id"])

                if response_json["event"] == "finish-evaluation":
                    logger.info(f"Validator {websocket.remote_address} with hotkey {self.clients[websocket]['val_hotkey']} has finished an evaluation {response_json['evaluation_id']}. Attempting to update the evaluation in the database.")
                    finish_evaluation(response_json["evaluation_id"], response_json["errored"])

                if response_json["event"] == "upsert-evaluation-run":
                    logger.info(f"Validator {websocket.remote_address} sent an evaluation run. Upserting evaluation run.")
                    upsert_evaluation_run(response_json["evaluation_run"]) 

        except websockets.ConnectionClosed:
            logger.info(f"Validator at {websocket.remote_address} with hotkey {self.clients[websocket]['val_hotkey']} disconnected from platform socket. Total validators connected: {len(self.clients) - 1}")
        finally:
            # Remove client when they disconnect
            del self.clients[websocket]

    async def create_new_evaluations(self, version_id: str):
        for websocket, client_data in self.clients.items():
            create_evaluation(version_id, client_data["val_hotkey"])
            await websocket.send(json.dumps({"event": "evaluation-available"}))
    
    async def get_next_evaluation(self, validator_hotkey: str):
        try:
            evaluation = get_next_evaluation(validator_hotkey)
            agent_version = get_agent(evaluation.version_id)
            socket_message = {
                "event": "evaluation",
                "evaluation_id": evaluation.evaluation_id,
                "agent_version": {
                    "version_id": agent_version.version_id,
                    "agent_id": agent_version.agent_id,
                    "version_num": agent_version.version_num,
                    "created_at": agent_version.created_at.isoformat(),
                    "score": agent_version.score,
                    "miner_hotkey": agent_version.miner_hotkey
                }
            }
            return socket_message
        except Exception as e:
            logger.error(f"Error getting next evaluation: {str(e)}")
            return None
    
    async def start(self):
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
        logger.info(f"Platform socket started on {self.uri}")
        await asyncio.Future()  # run forever

import asyncio
import websockets
import json
from typing import Set, Optional

from src.utils.logging import get_logger
from src.socket.server_helpers import update_validator_versions, get_agent_to_evaluate, upsert_evaluation_run
from src.db.operations import DatabaseManager

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
            self.clients: Set[websockets.WebSocketClientProtocol] = set()
            self.server = None
            self.validator_versions: dict = {}
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
        self.clients.add(websocket)
        logger.info(f"Validator {websocket.remote_address} connected to platform socket. Total validators connected: {len(self.clients)}")
        
        try:
            # Keep the connection alive and wait for messages
            while True:
                # Wait for client's response
                response = await websocket.recv()
                response_json = json.loads(response)

                if response_json["event"] == "validator-version":
                    logger.info(f"Validator {websocket.remote_address} sent their validator version. Updating validator versions.")
                    self.validator_versions = update_validator_versions(response_json, self.validator_versions)

                if response_json["event"] == "agent-version":
                    socket_message = await self.get_next_agent_version(response_json["validator_hotkey"])
                    try:
                        await websocket.send(json.dumps(socket_message))
                        logger.info(f"Platform socket sent next agent version from queue to validator {websocket.remote_address}")
                    except websockets.ConnectionClosed:
                        logger.warning(f"Failed to send next agent version from queue to validator {websocket.remote_address}")

                if response_json["event"] == "upsert-evaluation-run":
                    logger.info(f"Validator {websocket.remote_address} sent an evaluation run. Upserting evaluation run.")
                    upsert_evaluation_run(response_json["evaluation_run"]) 

                if response_json["event"] == "request-agent-for-evaluation":
                    validator_hotkey = response_json.get("validator_hotkey")
                    if validator_hotkey:
                        socket_message = await self.get_next_agent_version(validator_hotkey)
                        try:
                            await websocket.send(json.dumps(socket_message))
                            logger.info(f"Platform socket sent requested agent version to validator {websocket.remote_address}")
                        except websockets.ConnectionClosed:
                            logger.warning(f"Failed to send requested agent version to validator {websocket.remote_address}")
                    else:
                        error_message = {
                            "event": "error",
                            "message": "validator_hotkey is required for request-agent-for-evaluation event"
                        }
                        await websocket.send(json.dumps(error_message))

        except websockets.ConnectionClosed:
            logger.info(f"Validator {websocket.remote_address} disconnected from platform socket. Total validators connected: {len(self.clients) - 1}")
        finally:
            # Remove client when they disconnect
            self.clients.remove(websocket)
    
    async def _send_to_all_clients(self, message: dict, log_message: str):
        """Helper method to send message to all clients and handle disconnections"""
        if not self.clients:
            logger.info(f"No validators are connected to the platform socket")
            return False
            
        # Send message to all connected clients
        for client in self.clients.copy():  # Use copy to avoid modification during iteration
            try:
                await client.send(json.dumps(message))
            except websockets.ConnectionClosed:
                # Client will be removed in handle_connection when the exception is caught
                pass
        
        logger.info(log_message)
        return True

    async def notify_of_new_agent_version(self):
        socket_message = {
            "event": "new-agent-version",
        }
        
        success = await self._send_to_all_clients(
            socket_message, 
            "Platform socket notified connected validators of new agent version"
        )
        
        if not success:
            logger.info("Tried to notify validators of new agent version, but no validators are connected to the platform socket")

    async def get_next_agent_version(self, validator_hotkey: str):
        try:
            agent_version = get_agent_to_evaluate(validator_hotkey)
            socket_message = {
                "event": "agent-for-evaluation",
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
            logger.error(f"Error getting next agent version: {str(e)}")
            return {
                "event": "agent-for-evaluation",
                "error": "No agents available to evaluate"
            }

    async def get_validator_version(self) -> list:
        socket_message = {
            "event": "get-validator-version",
        }
        
        success = await self._send_to_all_clients(
            socket_message, 
            "Platform socket requested validator versions from all connected validators"
        )

        if not success:
            logger.info("Tried to get validator versions, but no validators are connected to the platform socket")
    
    async def start(self):
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
        logger.info(f"Platform socket started on {self.uri}")
        await asyncio.Future()  # run forever

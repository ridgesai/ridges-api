import asyncio
import websockets
from typing import Set

from src.utils.models import Agent

class WebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.clients: Set[websockets.WebSocketClientProtocol] = set()
        self.server = None
        asyncio.create_task(self.start())
    
    async def handle_connection(self, websocket):
        # Add new client to the set
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Keep the connection alive and wait for messages
            while True:
                # Wait for client's response
                response = await websocket.recv()
                print(f"Client responded with: {response}")
                
        except websockets.ConnectionClosed:
            print("Client disconnected")
        finally:
            # Remove client when they disconnect
            self.clients.remove(websocket)
            print(f"Client removed. Total clients: {len(self.clients)}")
    
    async def send_agent(self, agent: Agent):
        if not self.clients:
            print("No clients connected")
            return
            
        # Create a set of disconnected clients to remove
        disconnected_clients = set()
        
        # Send message to all connected clients
        for client in self.clients:
            try:
                await client.send(agent.model_dump_json())
                print(f"Sent: {agent.agent_id} to a client")
            except websockets.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove any disconnected clients
        for client in disconnected_clients:
            self.clients.remove(client)
            print(f"Removed disconnected client. Total clients: {len(self.clients)}")
    
    async def start(self):
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
        print(f"WebSocket server started on {self.uri}")
        await asyncio.Future()  # run forever
    
    def get_client_count(self) -> int:
        return len(self.clients)

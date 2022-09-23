import websockets
import asyncio
from typing_extensions import TypedDict
from threading import Thread
import json

class BlockchainEvent(TypedDict):
    event_type: str
    message: str
    data: dict

class WebsocketServer:
    """Websocket server to handle transmissions of blockchain events"""

    def __init__(self, port):
        self.port = port
        self.connections = set()

    async def handler(self, websocket):
        """Handler for websocket connections"""
        self.connections.add(websocket)
        try:
            async for message in websocket:
                await self.broadcast(message)
        finally:
            self.connections.remove(websocket)

    async def broadcast(self, message):
        """Broadcast message to all connected clients"""
        if self.connections:
            await asyncio.wait([connection.send(json.dumps(message)) for connection in self.connections])

    def start(self):
        """Start the websocket server in a separate thread"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(self.handler, "127.0.0.1", self.port)
            loop.run_until_complete(start_server)
            loop.run_forever()
            loop.close()
        Thread(target=run, daemon=True).start()


        
        
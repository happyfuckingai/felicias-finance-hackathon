"""
Transport Layer for A2A Protocol

Handles network communication using HTTP/2, WebSocket, and other transport protocols
for secure agent-to-agent messaging.
"""

import asyncio
import json
import aiohttp
import websockets
from typing import Dict, Optional, Any, Callable, List, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from .messaging import Message, EncryptedMessage
from .auth import AuthToken

logger = logging.getLogger(__name__)


@dataclass
class TransportConfig:
    """Configuration for transport layer."""

    protocol: str = "http2"  # "http2", "websocket", "http"
    host: str = "localhost"
    port: int = 8443
    ssl_enabled: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    timeout: float = 30.0
    max_connections: int = 100
    heartbeat_interval: float = 30.0


class HTTP2Transport:
    """HTTP/2 based transport for A2A messages."""

    def __init__(self, config: TransportConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.server = None
        self.routes: Dict[str, Callable] = {}
        self.running = False

    async def start(self):
        """Start the HTTP/2 transport."""

        if self.config.ssl_enabled:
            ssl_context = self._create_ssl_context()
        else:
            ssl_context = None

        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            ssl=ssl_context
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

        logger.info(f"HTTP/2 transport started on {self.config.host}:{self.config.port}")
        self.running = True

    async def stop(self):
        """Stop the HTTP/2 transport."""

        if self.session:
            await self.session.close()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        self.running = False
        logger.info("HTTP/2 transport stopped")

    async def send_message(self, message: Message, target_url: str,
                          auth_token: AuthToken) -> Optional[Dict[str, Any]]:
        """Send a message via HTTP/2."""

        if not self.session or not self.running:
            raise RuntimeError("Transport not started")

        headers = {
            "Authorization": f"Bearer {auth_token.token}",
            "Content-Type": "application/json",
            "A2A-Message-Type": message.message_type,
            "A2A-Sender": message.sender_id,
            "A2A-Receiver": message.receiver_id,
        }

        if message.correlation_id:
            headers["A2A-Correlation-ID"] = message.correlation_id

        data = message.to_dict()

        try:
            async with self.session.post(target_url, json=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"HTTP/2 request failed: {response.status} - {await response.text()}")
                    return None

        except Exception as e:
            logger.error(f"HTTP/2 send failed: {e}")
            return None

    async def send_encrypted_message(self, encrypted_message: EncryptedMessage,
                                    target_url: str, auth_token: AuthToken) -> Optional[Dict[str, Any]]:
        """Send an encrypted message via HTTP/2."""

        if not self.session or not self.running:
            raise RuntimeError("Transport not started")

        headers = {
            "Authorization": f"Bearer {auth_token.token}",
            "Content-Type": "application/json",
            "A2A-Encrypted": "true",
        }

        data = encrypted_message.to_dict()

        try:
            async with self.session.post(target_url, json=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Encrypted HTTP/2 request failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Encrypted HTTP/2 send failed: {e}")
            return None

    def register_handler(self, path: str, handler: Callable):
        """Register a handler for incoming messages."""
        self.routes[path] = handler

    async def start_server(self):
        """Start HTTP/2 server for receiving messages."""

        from aiohttp import web

        app = web.Application()

        async def message_handler(request):
            """Handle incoming A2A messages."""

            try:
                # Validate authorization
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    return web.Response(status=401, text="Unauthorized")

                auth_token = auth_header[7:]  # Remove "Bearer "

                # Check if message is encrypted
                is_encrypted = request.headers.get("A2A-Encrypted", "false").lower() == "true"

                if is_encrypted:
                    data = await request.json()
                    encrypted_message = EncryptedMessage.from_dict(data)

                    # Route to appropriate handler
                    path = request.path
                    if path in self.routes:
                        return await self.routes[path](encrypted_message, auth_token)
                    else:
                        return web.Response(status=404, text="Handler not found")
                else:
                    data = await request.json()
                    message = Message.from_dict(data)

                    # Route to appropriate handler
                    path = request.path
                    if path in self.routes:
                        return await self.routes[path](message, auth_token)
                    else:
                        return web.Response(status=404, text="Handler not found")

            except Exception as e:
                logger.error(f"Message handling error: {e}")
                return web.Response(status=400, text="Bad request")

        # Register message endpoint
        app.router.add_post("/a2a/message", message_handler)
        app.router.add_post("/a2a/encrypted", message_handler)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()

        if self.config.ssl_enabled:
            ssl_context = self._create_ssl_context()
            site = web.TCPSite(runner, self.config.host, self.config.port, ssl_context=ssl_context)
        else:
            site = web.TCPSite(runner, self.config.host, self.config.port)

        await site.start()
        self.server = site

        logger.info(f"HTTP/2 server started on {self.config.host}:{self.config.port}")

    def _create_ssl_context(self):
        """Create SSL context for secure connections."""

        import ssl

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if self.config.cert_file and self.config.key_file:
            ssl_context.load_cert_chain(self.config.cert_file, self.config.key_file)

        # Enable HTTP/2
        ssl_context.set_alpn_protocols(['h2', 'http/1.1'])

        return ssl_context


class WebSocketTransport:
    """WebSocket based transport for real-time A2A messaging."""

    def __init__(self, config: TransportConfig):
        self.config = config
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.server = None

    async def start(self):
        """Start the WebSocket transport."""

        self.running = True

        # Start WebSocket server
        await self.start_server()

        logger.info(f"WebSocket transport started on {self.config.host}:{self.config.port}")

    async def stop(self):
        """Stop the WebSocket transport."""

        self.running = False

        # Close all connections
        for ws in self.connections.values():
            await ws.close()

        self.connections.clear()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("WebSocket transport stopped")

    async def send_message(self, message: Message, target_uri: str,
                          auth_token: AuthToken) -> bool:
        """Send a message via WebSocket."""

        try:
            async with websockets.connect(target_uri) as websocket:
                # Send authentication
                await websocket.send(json.dumps({
                    "type": "auth",
                    "token": auth_token.token
                }))

                # Wait for auth response
                auth_response = await websocket.recv()
                auth_data = json.loads(auth_response)

                if not auth_data.get("authenticated", False):
                    logger.error("WebSocket authentication failed")
                    return False

                # Send message
                message_data = {
                    "type": "message",
                    "data": message.to_dict()
                }

                await websocket.send(json.dumps(message_data))
                return True

        except Exception as e:
            logger.error(f"WebSocket send failed: {e}")
            return False

    async def broadcast_message(self, message: Message, auth_token: AuthToken):
        """Broadcast a message to all connected agents."""

        message_data = {
            "type": "broadcast",
            "data": message.to_dict(),
            "auth_token": auth_token.token
        }

        disconnected = []
        for agent_id, ws in self.connections.items():
            try:
                await ws.send(json.dumps(message_data))
            except Exception as e:
                logger.error(f"Failed to send to {agent_id}: {e}")
                disconnected.append(agent_id)

        # Clean up disconnected agents
        for agent_id in disconnected:
            del self.connections[agent_id]

    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for incoming messages."""
        self.handlers[message_type] = handler

    async def start_server(self):
        """Start WebSocket server."""

        uri = f"ws://{self.config.host}:{self.config.port}"

        async def ws_handler(websocket, path):
            """Handle WebSocket connections."""

            agent_id = None

            try:
                async for message in websocket:
                    data = json.loads(message)

                    if data["type"] == "auth":
                        # Handle authentication
                        token = data.get("token")
                        # In a real implementation, validate the token
                        agent_id = f"agent_{len(self.connections)}"  # Simplified

                        self.connections[agent_id] = websocket

                        await websocket.send(json.dumps({
                            "type": "auth_response",
                            "authenticated": True,
                            "agent_id": agent_id
                        }))

                    elif data["type"] == "message":
                        # Handle incoming message
                        message_data = data.get("data")
                        a2a_message = Message.from_dict(message_data)

                        # Route to handler
                        msg_type = a2a_message.message_type
                        if msg_type in self.handlers:
                            await self.handlers[msg_type](a2a_message, websocket)

                        # Echo back for now (could be response)
                        await websocket.send(json.dumps({
                            "type": "message_response",
                            "status": "received",
                            "message_id": a2a_message.message_id
                        }))

            except websockets.exceptions.ConnectionClosed:
                if agent_id:
                    self.connections.pop(agent_id, None)
                logger.info(f"WebSocket connection closed for {agent_id}")

        # Start server
        if self.config.ssl_enabled:
            ssl_context = self._create_ssl_context()
            self.server = await websockets.serve(
                ws_handler, self.config.host, self.config.port, ssl=ssl_context
            )
        else:
            self.server = await websockets.serve(
                ws_handler, self.config.host, self.config.port
            )

    def _create_ssl_context(self):
        """Create SSL context for secure WebSocket connections."""

        import ssl

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if self.config.cert_file and self.config.key_file:
            ssl_context.load_cert_chain(self.config.cert_file, self.config.key_file)

        return ssl_context


class TransportLayer:
    """Unified transport layer supporting multiple protocols."""

    def __init__(self, config: TransportConfig):
        self.config = config
        self.transports: Dict[str, Union[HTTP2Transport, WebSocketTransport]] = {}
        self.current_transport: Optional[str] = None

        # Initialize transports based on protocol
        if config.protocol == "http2":
            self.transports["http2"] = HTTP2Transport(config)
            self.current_transport = "http2"
        elif config.protocol == "websocket":
            self.transports["websocket"] = WebSocketTransport(config)
            self.current_transport = "websocket"
        else:
            # Default to HTTP/2
            self.transports["http2"] = HTTP2Transport(config)
            self.current_transport = "http2"

    async def start(self):
        """Start the transport layer."""

        for transport in self.transports.values():
            await transport.start()

        logger.info(f"Transport layer started with protocol: {self.config.protocol}")

    async def stop(self):
        """Stop the transport layer."""

        for transport in self.transports.values():
            await transport.stop()

        logger.info("Transport layer stopped")

    async def send_message(self, message: Message, target: str,
                          auth_token: AuthToken) -> Optional[Any]:
        """Send a message using the current transport."""

        if not self.current_transport:
            raise RuntimeError("No transport configured")

        transport = self.transports.get(self.current_transport)
        if not transport:
            raise RuntimeError(f"Transport {self.current_transport} not available")

        if isinstance(transport, HTTP2Transport):
            return await transport.send_message(message, target, auth_token)
        elif isinstance(transport, WebSocketTransport):
            return await transport.send_message(message, target, auth_token)

        return None

    async def send_encrypted_message(self, encrypted_message: EncryptedMessage,
                                    target: str, auth_token: AuthToken) -> Optional[Any]:
        """Send an encrypted message using the current transport."""

        if not self.current_transport:
            raise RuntimeError("No transport configured")

        transport = self.transports.get(self.current_transport)
        if not transport:
            raise RuntimeError(f"Transport {self.current_transport} not available")

        if isinstance(transport, HTTP2Transport):
            return await transport.send_encrypted_message(encrypted_message, target, auth_token)

        return None

    def register_handler(self, path_or_type: str, handler: Callable):
        """Register a message handler."""

        for transport in self.transports.values():
            transport.register_handler(path_or_type, handler)

    async def start_server(self):
        """Start server for receiving messages."""

        for transport in self.transports.values():
            if hasattr(transport, 'start_server'):
                await transport.start_server()

    def switch_protocol(self, protocol: str):
        """Switch to a different transport protocol."""

        if protocol in self.transports:
            self.current_transport = protocol
            logger.info(f"Switched to {protocol} transport")
        else:
            raise ValueError(f"Transport protocol {protocol} not available")
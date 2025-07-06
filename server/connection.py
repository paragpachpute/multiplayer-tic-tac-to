import json
import websockets
import logging
import asyncio

class ClientConnection:
    """
    A wrapper around a client connection (TCP or WebSocket) to provide a
    unified interface for sending messages and managing client state.
    """
    def __init__(self, reader, writer=None):
        logging.info(f"Creating ClientConnection for reader: {reader}")
        # For TCP, reader and writer are separate. For WS, they are the same object.
        self._reader = reader
        self._writer = writer if writer else reader
        self.game_id = None
        self.player_symbol = None
        self.player_name = None
        self.registered = False

    @property
    def is_websocket(self) -> bool:
        """Returns True if the client is a WebSocket connection."""
        return hasattr(self._reader, 'recv')

    @property
    def is_tcp(self) -> bool:
        """Returns True if the client is a TCP connection."""
        return hasattr(self._reader, 'readline')

    async def send(self, response_data):
        """Sends a structured response to the client."""
        message = json.dumps(response_data)
        try:
            if self.is_websocket:
                await self._writer.send(message)
            elif self.is_tcp:
                self._writer.write((message + '\n').encode())
                await self._writer.drain()
        except (websockets.exceptions.ConnectionClosed, ConnectionResetError, BrokenPipeError):
            raise

    async def read(self):
        """Reads a single, complete message from the client."""
        if self.is_websocket:
            return await self._reader.recv()
        elif self.is_tcp:
            line = await self._reader.readline()
            return line.decode().strip()
        raise TypeError("Unsupported client type for reading.")

    def get_remote_address(self):
        """Returns the remote address of the client in a unified way."""
        if hasattr(self._writer, 'remote_address'):
            return self._writer.remote_address
        elif hasattr(self._writer, 'get_extra_info'):
            return self._writer.get_extra_info('peername', 'Unknown')
        return "Unknown"
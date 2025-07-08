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
        self._reader = reader
        self._writer = writer if writer else reader
        self.game_id = None
        self.player_symbol = None
        self.player_name = None
        self.registered = False

    @property
    def is_websocket(self) -> bool:
        return hasattr(self._reader, 'recv')

    @property
    def is_tcp(self) -> bool:
        return hasattr(self._reader, 'readline')

    async def send(self, response_data):
        """
        Sends a structured response to the client.
        This method uses a try...except block to handle disconnections gracefully.
        """
        message = json.dumps(response_data)
        try:
            if self.is_websocket:
                await self._writer.send(message)
            elif self.is_tcp:
                if not self._writer.is_closing():
                    self._writer.write((message + '\n').encode())
                    await self._writer.drain()
                else:
                    # If the TCP writer is closing, raise an error to be caught below.
                    raise ConnectionResetError
            else:
                raise TypeError("Unsupported client type")
        except (websockets.exceptions.ConnectionClosed, ConnectionResetError, BrokenPipeError) as e:
            # This is now an expected part of the flow.
            # We log it for information and re-raise it so the main handler knows
            # that the client has disconnected.
            logging.info(f"Could not send to {self.get_remote_address()}; connection is closed. Error: {e}")
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

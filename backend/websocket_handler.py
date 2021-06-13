import asyncio
import logging
import sys
import traceback
from backend.utils import dictify
from json import JSONDecodeError

import aiohttp

from backend.errors import *
from backend.game_manager import Lobby
import discord.http

from aiohttp import web

log = logging.getLogger("ws_log")


class BaseClientHandler:
    def __init__(self, app):
        self.ws = None
        self.user = None
        self.app = app
        self.backlog = asyncio.Queue()
        self.produce = asyncio.Queue()
        self.handlers = {}
        self.lobby = None
        self.last_event_manager = None


class WebSocketClientHandler(BaseClientHandler):
    def __init__(self, app):
        super().__init__(app)

        for k in self.__dir__():
            if k.startswith("on_"):
                event_name = k[3:]
                if event_name not in self.handlers:
                    self.handlers[event_name] = []
                self.handlers[event_name].append(self.__getattribute__(k))

    def __getattr__(self, item):
        if self.user:
            return self.user.__getattribute__(item)

    async def start_producing(self):
        try:
            while True:
                item = await self.produce.get()

                try:
                    await self.ws.send_json(item)
                    log.debug(f"User {self.user.name if self.user else '[unknown]'} received {item[0]} with data {item[1]}")
                except ConnectionResetError:
                    log.info(f"Putting event {item[0]} into backlog due to connection error!")
                    self.backlog.put_nowait(item)
                except Exception:
                    log.error(f"Error sending item: {item}. Erorr: {traceback.format_exc()}")
        except asyncio.CancelledError:
            log.debug(f"Producer for {self.user.name if self.user else 'a client'} stopped")
            raise

    async def consume(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        producer = asyncio.create_task(self.start_producing(), name=f"producer-for-{asyncio.current_task().get_name()}")

        if not self.user:
            session = request.cookies.get("session")
            user = request.app["app"].connected_http_clients.get(session)
            if not user:
                self.send_error("You are not logged in")
                await self.ws.close()
                return self.ws
            else:
                self.user = user
                log.debug(f"WS for session {session} connected with user {user.name}")

        # Update client to current state fo things
        self.send_login_info()
        for l in self.app.game_manager.lobbies:
            self.send_lobby_created(l)

        if self.lobby:
            self.send_joined_lobby(self.lobby)

        try:
            async for msg in self.ws:  # Handle client messages
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        parsed = msg.json()
                        event_name = parsed[0]
                        data = parsed[1] or {}
                    except Exception as e:
                        self.send_error(f"MalformedRequest", "Malformed request sent")
                    log.debug(f"User sent the event {event_name} with data {data}")
                    handlers = self.handlers.get(event_name, [])
                    for handler in handlers:
                        try:
                            await handler(data)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            e = sys.exc_info()
                            self.handle_error(event_name, data, e[1])

                    if event_name not in self.handlers:
                        log.warning(f"{event_name} was received and not handled (no handlers found)")

                elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    log.warning(f"Non-text WS message aaaaaaa, type is {msg.type}")
                    await self.ws.close()

        except asyncio.CancelledError:
            log.warning("WS handler got cancelled")
            await self.ws.close()
            raise
        except Exception:
            log.critical("UNHANDLED EXCEPTION STOPPING CLIENT HANDLER")
            traceback.print_exc()
            await self.ws.close()

        producer.cancel()
        # await asyncio.sleep(0.1)
        log.debug("Client disconnect")
        return self.ws

    def rest(self):  # called when client is disconnected but might reconnect
        pass

    def awaken(self):  # Called when client reconnects
        pass

    async def disconnect(self):
        await self.ws.close()

    def handle_error(self, event, data, error):
        log.error(f"Error processing event {event} with data {data}! {traceback.format_exc() if log.isEnabledFor(logging.DEBUG) else str(error)}")
        self.send_error(error.__class__.__name__, str(error))

    def _send(self, event, data):
        return self.produce.put_nowait([event, dictify(data)])

    # EVENTS RECEIVED FROM CLIENT

    async def on_join_chatroom(self, data):
        name = data.get("name")
        room = self.app.chatrooms.get(name, None)
        if room is not None:
            room.user_join(self)

    async def on_leave_chatroom(self, data):
        name = data.get("name")
        room = self.app.chatrooms.get(name, None)
        if room is not None:
            room.user_leave(self)

    async def on_chat_message_send(self, data):
        content = data.get("content")
        room_name = data.get("room", "general")
        room = self.app.chatrooms.get(room_name)
        room.send_message(content, self)

    async def on_create_lobby(self, data):
        options = data.get("options", {})
        lobby = self.app.game_manager.create_lobby(options)
        self.app.game_manager.user_join(self, lobby)

    async def on_input_response(self, data):
        id = data.get("id")
        data = data.get("data")
        if self.last_event_manager:
            self.last_event_manager.receive_input_response(id, data)
        else:
            log.warning("Received input response but no event manager is set! Ignoring")

    async def on_fetch_lobby(self, data):
        lobby = self.app.game_manager.get_lobby(data.get("lobby_id"))
        self.send_lobby_changed(lobby)
                
    async def on_join_lobby(self, data):
        self.app.game_manager.user_join(self, data.get("lobby_id"))

    # EVENTS THAT WILL BE SENT TO THE CLIENT
    # All  these must start with send_ for broadcasting purposes

    def send_error(self, exception, message: str):
        self._send("error_message", {"error": exception, "message": message})

    def send_chat_message(self, author: BaseClientHandler, content: str, room):
        name = "Server"
        if author is not None:
            name = author.user.name
        self._send("chat_message_create", {"author": name, "content": content, "room": room.name})

    def send_login_info(self):
        self._send("login_info", self.user.to_dict(include_password=False))

    def send_lobby_created(self, lobby: Lobby):
        self._send("lobby_create", lobby.to_dict())

    def send_lobby_deleted(self, lobby_id: str):
        self._send("lobby_deleted", {"id": lobby_id})

    def send_lobby_changed(self, lobby: Lobby):
        self._send("lobby_change", lobby.to_dict(self))

    def send_joined_lobby(self, lobby: Lobby):
        self._send("joined_game", lobby.to_dict())

    def join_lobby(self, lobby: Lobby):
        if not self.lobby:
            self.lobby = lobby
            self.send_joined_lobby(lobby)
        else:
            raise UserInDifferentGame(f"You are already in a game. Leave the game {self.lobby.name} to join a new one")

    def send_game_event(self, event):
        self._send("game_event", event.to_dict())

    def send_input_request(self, request):
        self.last_event_manager = request._event_manager
        self._send("input_request", request.to_dict())

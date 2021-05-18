import asyncio
import logging
import traceback
from aiohttp import web

log = logging.getLogger("ws_log")


class WebSocketClientHandler:
    def __init__(self, app):
        self.ws = None
        self.user = None
        self.app = app
        self.backlog = asyncio.Queue()
        self.produce = asyncio.Queue()
        self.handlers = {}
        self.last_event_manager = None

        for k in self.__dir__():
            if k.startswith("on_"):
                event_name = k[3:]
                if event_name not in self.handlers:
                    self.handlers[event_name] = []
                self.handlers[event_name].append(self.__getattribute__(k))

    async def start_producing(self):
        while True:
            try:
                item = await self.produce.get()
            except asyncio.CancelledError:
                break
            try:
                await self.ws.send_json(item)
                log.debug(f"User {self.user.name if self.user else '[unknown]'} received {item[0]} with data {item[1]}")
            except ConnectionResetError:
                log.info(f"Putting event {item[0]} into backlog! Error: {traceback.format_exc()}")
                await self.backlog.put(item)
            except:
                log.error(f"Error sending item: {item}. Erorr: {traceback.format_exc()}")
        log.debug(f"Producer for {self.user.name if self.user else 'a client'} stopped")

    async def consume(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        producer = asyncio.create_task(self.start_producing())

        if not self.user:
            session = request.cookies.get("session")
            user = request.app["app"].connected_http_clients.get(session)
            if not user:
                await self.send("not_logged_in", {})
                await self.ws.close()
                return self.ws
            else:
                self.user = user
                log.debug(f"WS for session {session} connected with user {user.name}")

        # Update client to current state fo things
        await self.send("login_info", {"user": self.user.to_dict(include_password=False)})
        await asyncio.gather(*[self.send("lobby_create", {"lobby": lobby.to_dict()}) for lobby in self.app.game_manager.lobbies.values()])

        async for msg in self.ws:
            parsed = msg.json()
            event_name = parsed[0]
            data = parsed[1] or {}
            handlers = self.handlers.get(event_name, [])
            for h in handlers:
                await h(data)

            if event_name not in self.handlers:
                log.warning(f"{event_name} was received and not handled (no handlers found)")

        producer.cancel()
        log.debug("Client disconnect")

    def send(self, event, data, nowait=False):
        if nowait:
            return self.produce.put_nowait([event, data])
        else:
            return self.produce.put([event, data])

    async def on_join_chatroom(self, data):
        name = data.get("name")
        room = self.app.chatrooms.get(name, None)
        if room is not None:
            await room.user_join(self)

    async def on_leave_chatroom(self, data):
        name = data.get("name")
        room = self.app.chatrooms.get(name, None)
        if room is not None:
            room.user_leave(self)

    async def on_chat_message_send(self, data):
        content = data.get("content")
        room_name = data.get("room", "general")
        room = self.app.chatrooms.get(room_name)
        await room.send_message(content, self)

    async def on_create_lobby(self, data):
        options = data.get("options", {})
        lobby = self.app.game_manager.create_lobby(options)
        self.app.chatrooms[lobby.id] = self.app.chatrooms["general"].__class__(lobby.id)  # Ugly hack, rewrite pls
        await self.app.broadcast("lobby_create", {"lobby": lobby.to_dict()})
        await self.app.game_manager.user_join(self, lobby)

    async def on_input_response(self, data):
        id = data.get("id")
        data = data.get("data")
        if self.last_event_manager:
            self.last_event_manager.receive_input_request(id, data)
        else:
            log.warning("Received input response but on event manager is set! Ignoring")

    async def on_fetch_lobby(self, data):
        lobby_id = data.get("lobby_id")
        if lobby_id:
            lobby = self.app.game_manager.lobbies.get(lobby_id)
            if lobby:
                await self.send("lobby_change", {"lobby": lobby.to_dict()})



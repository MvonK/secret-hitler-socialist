import aiohttp
from aiohttp import web
import asyncio
import hashlib
import random
import backend
from backend.user_manager import UserManager
from backend.game_manager import GameManager
from backend.websocket_handler import WebSocketClientHandler

import logging
import argparse
import aioredis


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-noweb", action="store_true")
    parser.add_argument("-debug", action="store_true")
    parser.add_argument("-infolog", action="store_true")
    parser.add_argument("-debuglog", action="store_true")
    return parser.parse_args()


config = parse_arguments()


loglevel = logging.INFO if config.infolog else (logging.DEBUG if config.debuglog else logging.WARNING)
logging.basicConfig(level=loglevel)
log = logging.getLogger("mainlog")


logging.getLogger('socketio').setLevel(loglevel)
logging.getLogger('engineio').setLevel(loglevel)


class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.members = set()

    async def send_message(self, message, author):
        if author in self.members:
            for m in self.members:
                await m.send("chat_message_create", {"author": author.user.name, "content": message, "room": self.name})
        else:
            log.warning(f"{author.user.name} tried to send a message to the chatroom {self.name} but is not connected")

    async def user_join(self, user):
        if not user in self.members:
            self.members.add(user)
            await user.send("chat_message_create", {"author": "Server",
                                                    "content": f"You are now connected to the room {self.name}",
                                                    "room": self.name})

    def user_leave(self, user):
        try:
            self.members.remove(user)
        except KeyError:
            pass


class Application:
    def __init__(self):
        self.app = web.Application()
        self.redis_pool = aioredis.ConnectionsPool("redis://localhost:6379", maxsize=10, minsize=0)

        self.user_manager = UserManager(self.redis_pool)
        self.game_manager = GameManager()

        self.connected_ws_clients = set()
        self.connected_http_clients = {}  # Session ID: User

        self.chatrooms = {}

    def setup(self, webserver=True, websockets=True):
        if websockets:
            log.info("Setting up websocket handler")
            self.app.router.add_routes([web.get("/ws", self.websocket_handler)])

        if webserver:
            log.info("Setting up http routes")
            self.setup_web()

        self.chatrooms["general"] = ChatRoom("general")

        self.app["app"] = self

    def setup_web(self):
        routes = web.RouteTableDef()

        async def root(request):
            return web.FileResponse("client/build/index.html")

        rootable = ["/lobbies", "/chat", "/secret", "/game", "/main"]
        for r in rootable:
            routes.route("GET", r)(root)

        @routes.post("/login")
        async def login(request):
            info = await request.json()
            username = info.get("username")
            password = info.get("password")

            response = web.Response()
            if username and password:
                user = await self.user_manager.get_user(await self.user_manager.get_uid(username))
                if user:
                    if user.password == password:
                        # Login successful, register
                        hashed = hashlib.md5(f"{username}:{password}+{random.random()}".encode()).hexdigest()
                        self.connected_http_clients[hashed] = user
                        response.set_cookie("session", hashed)
                        response.set_cookie("username", username)
                        response.body = "Login successful!!!"
                        return response

                response.set_status(403)
                response.body = "Wrong username-password combination"
            else:
                response.set_status(400)
                response.body = "Missing username or password"

            return response

        @routes.post("/logout")
        async def logout(request):
            session = request.cookies.get("session")
            response = web.Response()
            await response.prepare(request)

            if session:
                response.del_cookie("session")
                if session in self.connected_http_clients:
                    user = self.connected_http_clients.pop(session)
                    for c in self.connected_ws_clients:
                        if c.user is user:
                            c.disconnect()

            return response


        routes.static("/", "client/build")

        self.app.add_routes(routes)

    async def websocket_handler(self, request):
        log.debug("New websocket connection")
        handler = WebSocketClientHandler(self)
        self.connected_ws_clients.add(handler)
        await handler.consume(request)

        # Handler stopped processing messages. If it didn't initialize user, we can simply throw it away
        if handler.user is None:
            self.connected_ws_clients.remove(handler)

        #game_space = GameNamespace("/", user_manager, game_manager, sio)

    def broadcast(self, event, data):
        return asyncio.gather(*[client.send(event, data) for client in self.connected_ws_clients])


if __name__ == "__main__":
    print("Starting..")
    app = Application()
    app.setup(webserver=not config.noweb)
    web.run_app(app.app)




'''    if not config.noweb:
        log.info("Configuring web server routes")
        from backend.flask_routes import setup_routes

        setup_routes(app, user_manager, game_space)

    log.info("Starting the whole thing")
    sio.run(app, debug=config.debug, host="0.0.0.0", port=8080)'''

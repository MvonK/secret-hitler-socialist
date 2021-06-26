from aiohttp import web
import hashlib
import random
from backend.user_manager import UserManager
from backend.game_manager import GameManager
from backend.errors import *
from backend.models import ChatRoom
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


class Application:
    def __init__(self):
        self.app = web.Application()
        self.redis_pool = aioredis.ConnectionsPool("redis://redis:6379", maxsize=10, minsize=0)

        self.user_manager = UserManager(self.redis_pool)
        self.game_manager = GameManager(self)

        self.connected_ws_clients = set()
        self.connected_http_clients = {}  # Session ID: User
        self.resting_ws_clients = set()  # Disconnected WS clients that might come back

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

        rootable = ["/", "/lobbies", "/chat", "/secret", "/game/{game_id}", "/main/{any}"]
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
        session = request.cookies.get("session")
        handler = None
        if session and session in self.connected_http_clients:  # Try to reconnect from resting clients
            user = self.connected_http_clients[session]
            for resting_client in self.resting_ws_clients:
                if resting_client.user is user:
                    handler = resting_client
                    self.resting_ws_clients.remove(resting_client)
                    handler.awaken()
                    break

            for cl in self.connected_ws_clients:
                if cl.user is user:
                    await cl.disconnect()
            for cl in self.resting_ws_clients:
                if cl.user is user:
                    self.resting_ws_clients.remove(cl)

        if handler is None:
            handler = WebSocketClientHandler(self)
        self.connected_ws_clients.add(handler)
        to_ret = await handler.consume(request)

        # Handler stopped processing messages. If it didn't initialize user, we can simply throw it away
        self.connected_ws_clients.remove(handler)
        if handler.user is None:
            pass
        else:
            handler.rest()
            self.resting_ws_clients.add(handler)

        return to_ret

    def broadcast(self, event_name, *args, **kwargs):  # Calls  the send_ + event name method of all connected clients
        # return asyncio.gather(*[client.send(event, data) for client in self.connected_ws_clients])
        for client in self.connected_ws_clients:
            callback = client.__getattribute__("send_" + event_name)
            callback(*args, **kwargs)


if __name__ == "__main__":
    print("Starting..")
    app = Application()
    app.setup(webserver=not config.noweb)
    web.run_app(app.app, shutdown_timeout=5)




'''    if not config.noweb:
        log.info("Configuring web server routes")
        from backend.flask_routes import setup_routes

        setup_routes(app, user_manager, game_space)

    log.info("Starting the whole thing")
    sio.run(app, debug=config.debug, host="0.0.0.0", port=8080)'''

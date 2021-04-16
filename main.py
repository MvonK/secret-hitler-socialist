import eventlet
from flask_socketio import SocketIO
from flask import Flask, request, render_template, send_from_directory, redirect, send_file
import backend
from backend.user_manager import UserManager
from backend.game_manager import GameManager
from backend.socketio_handler import GameNamespace

import logging
import argparse
import redis

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


app = Flask(__name__, static_url_path="/client/build")
app.secret_key = b'\xbd$`\xac\xdc\xb5\x7f\xce\xcfHx\xa0\x8fvE@K\x90\x84\xef\x106\x01Y\x86\xa3\x8eX\xdc\xac\x02\xe3'
sio = SocketIO(app, manage_session=True, message_queue="redis://localhost:6379/0", cors_allowed_origins="*")


eventlet.monkey_patch(socket=True)
logging.getLogger('socketio').setLevel(loglevel)
logging.getLogger('engineio').setLevel(loglevel)


redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)
r.set("foo", "bar2")

user_manager = UserManager(redis_pool)
game_manager = GameManager()

sio.on_namespace(GameNamespace("/", user_manager, game_manager))

if __name__ == "__main__":
    if not config.noweb:
        log.info("Configuring web server routes")

        @app.route("/")
        def root():
            return send_file("client/build/index.html")

        @app.route("/<path:path>")
        def default(path):
            log.debug(f"Serving {path}")
            if path is None:
                path = "index.html"
            return send_from_directory("client/build/", path)

    log.info("Starting the whole thing")
    sio.run(app, debug=config.debug, host="0.0.0.0", port=8080)

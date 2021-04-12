from flask_socketio import SocketIO, send, emit, Namespace
from flask import request
import string
import redis

import logging

log = logging.getLogger("namespaces")


def validate_username(username):
    valid_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "_-"


class GameNamespace(Namespace):
    def __init__(self, path, redis_pool):
        super().__init__(path)
        self.redis = redis.Redis(connection_pool=redis_pool)

    def on_connect(self):

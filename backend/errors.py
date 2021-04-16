class SecretHitlerSocialistError(BaseException):
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return str(self.message)


class SocketIOError(SecretHitlerSocialistError):
    pass


class NotLoggedIn(SocketIOError):
    pass


class UserDoesntExist(SocketIOError):
    pass


class UserNotInGame(SocketIOError):
    pass


class UserNotInRoom(SocketIOError):
    pass


class GameManagerError(SecretHitlerSocialistError):
    pass


class GameDoesntExist(GameManagerError):
    pass

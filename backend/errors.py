class SecretHitlerSocialistError(BaseException):
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return f"{self.message}"


class CommunicationError(SecretHitlerSocialistError):
    pass


class NotLoggedIn(CommunicationError):
    pass


class UserDoesntExist(CommunicationError):
    pass


class UserNotInGame(CommunicationError):
    pass


class UserNotInRoom(CommunicationError):
    pass


class UserInDifferentGame(CommunicationError):
    pass


class GameManagerError(SecretHitlerSocialistError):
    pass


class GameDoesntExist(GameManagerError):
    pass

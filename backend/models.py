from .errors import *


class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.members = set()

    def send_message(self, message, author):
        if author in self.members:
            for m in self.members:
                m.send_chat_message(author, message, self)
        else:
            raise UserNotInRoom(f"You are not joined in the chat room {self.name}")

    def user_join(self, user):
        if user not in self.members:
            self.members.add(user)
            user.send_chat_message(None, f"You are now connected to the room {self.name}", self)

    def user_leave(self, user):
        try:
            self.members.remove(user)
        except KeyError:
            pass

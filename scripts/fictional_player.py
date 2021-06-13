import asyncio
import sys
import traceback

import aiohttp


class ExitException(BaseException):
    pass

class Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.ws = None
        self.input_resp_func = None

    async def consumer(self):
        async for msg in self.ws:
            try:
                val = msg.json()
                print(f"{self.username}: {val}")
                if val[0] == "input_request":
                    print("inp req")

                    self.input_resp_func = self.send_input_response(val[1]["id"])

                elif val[0] == "lobby_create":
                    print("autojoining")
                    await self.ws.send_json(["join_lobby", {"lobby_id": "78600"}])
            except:
                traceback.print_exc()

    def send_input_response(self, id):
        async def send(data):
            await self.ws.send_json(["input_response", {"id": id, "data": data}])
        return send

    async def producer(self):
        while True:
            inp = await asyncio.get_event_loop().run_in_executor(None, input, f"{self.username}: ")
            if self.input_resp_func:
                await self.input_resp_func(inp)
                self.input_resp_func = None
                continue
            else:
                if inp == "exit":
                    raise ExitException()
                elif inp == "":
                    continue
                else:
                    await self.ws.send_str(inp)

    async def connect(self, url="http://localhost:8080"):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/login", json={"username": self.username, "password": self.password}) as resp:
                if resp.status != 200:
                    print(f"{self.username} had error logging in! {await resp.json()}")
                else:
                    print(f"{self.username} logged in!")

            async with session.ws_connect(f"{url}/ws") as ws:
                self.ws = ws
                p = asyncio.create_task(self.producer())
                c = asyncio.create_task(self.consumer())
                try:
                    await p
                except (ExitException, asyncio.CancelledError):
                    p.cancel()
                    c.cancel()
                    raise asyncio.CancelledError

            self.ws = None


async def main():
    # pairs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "f")]
    pairs = [(sys.argv[1], sys.argv[2])]
    clients = asyncio.gather(*[Client(p[0], p[1]).connect() for p in pairs])
    await clients
    clients.cancel()
    return

if __name__ == "__main__":
    print("Starting")
    asyncio.run(main())


# ["join_chatroom", {"name": "general"}]
# ["chat_message_send", {"content": "Test"}]
# ["create_lobby", {"options": {"roles": ["Liberal", "Liberal", "Fascist", "Fascist"]}}]
# ["create_lobby",{"options":{"loyal_players":{"Liberal":3,"Fascist":1},"parties_playing":["Liberal","Fascist"]}}]
# ["join_lobby", {"lobby_id": "78600"}]
# ["input_response", {"id": 1, "data": "uid-1000055"}]
# ["input_response", {"id": 24, "data": "Fascist"}]

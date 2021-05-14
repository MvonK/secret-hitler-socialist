# SocketIO events

This should contain an exhaustive list of all socketio events that are gonna be sent, either from server to client or 
from client to server. Should contain a brief description of the event and all parameters it contains.

### From server
All events that can arrive from the server:

`chat_message_create` - A new chat message that was sent. This includes messages sent by that client.
- `author` - name of the author, `server` if it's a server a message
- `content` - Contents of the message
- `room` - The room this message was sent to

`login_info` - A response to `fetchLoginInfo`. This is sent automatically on when a connection is established.
- `user` - The `User` object the client is logged in as

`lobby_create` - A new lobby was created.
- `lobby` - The game object that was created

`lobby_deleted` - A lobby was deleted.
- `id` - The id of the lobby that was deleted

`lobby_change` - Lobby info is updated
- `lobby` - The new lobby data

`joined_game` - You have joined a lobby
- `lobby` - The lobby data


### From client
All events coming from clients

`chat_message_send` - A client sends a message to their game
- `content` - The message contents
- `room` - The room to send the message to

`fetch_login_info` - Fetch the username this client is logged in as
No parameters. Server responds with `loginInfo`

`create_lobby` - Create a lobby

`join_chatroom` - Join a chatroom
- `name` - The room name to join

`leave_chatroom` - Leave a chatroom
- `name` The room to leave

`join_lobby` - Join a lobby
- `lobby_id` - The lobby id you want to join

### Objects
Objects that might be sent over the network.

`User` - Object representing a user
- `uid` - The string uid assigned to the user. Unique among all users
- `name` - Username of this user
- `elo` - Integer representing the current ELO  
- `stats` - The `Statistics` object associated with this user

`Lobby` - Object representing a lobby. Lobby only exists if the associated game is running, or is yet to start.
- `name` - name of the lobby
- `id` - The unique lobby id
- `options` - the `GameOptions` object, representing the game settings
- `users` - list of `User` objects representing users waiting in the lobby

`GameState` - Represents a game state, such as policies, who is the president, etc
- `lobbyID` - The lobby ID this game is happening in
- `players` - The list of `Player` objects in this game
- `policies` - A dictionary with the short party name (lib fas soc) as keys and the amount of their policies in play 
  as the value 


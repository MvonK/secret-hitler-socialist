# SocketIO events

This should contain an exhaustive list of all socketio events that are gonna be sent, either from server to client or 
from client to server. Should contain a brief description of the event and all parameters it contains.

### From server
All events that can arrive from the server:

`chatMessageCreate` - A new chat message that was sent. This includes messages sent by that client.
- `author` - name of the author, `server` if it's a server a message
- `content` - Contents of the message
- `room` - The room this message was sent to

`loginInfo` - A response to `fetchLoginInfo`. This is sent automatically on when a connection is established.
- `user` - The `User` object the client is logged in as


### From client
All events coming from clients

`chatMessageSend` - A client sends a message to their game
- `content` - The message contents
- `room` - The room to send the message to

`fetchLoginInfo` - Fetch the username this client is logged in as
No parameters. Server responds with `loginInfo`

### Objects
Objects that might be sent over the network.

`User` - Object representing a user
- `uid` - The string uid assigned to the user. Unique among all users
- `name` - Username of this user
- `elo` - Integer representing the current ELO  
- `stats` - The `Statistics` object associated with this user
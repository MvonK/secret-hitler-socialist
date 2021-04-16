# SocketIO events

This should contain an exhaustive list of all socketio events that are gonna be sent, either from server to client or 
from client to server. Should contain a brief description of the event and all parameters it contains.

### From server
All events that can arrive from the server:

`chatMessageCreate` - A new message that was sent. This includes messages sent by that client.
- `author` - name of the author, `server` if it's a server a message
- `content` - Contents of the message
- `room` - The room this message was sent to


### From client
All events coming from clients

`chatMessageSend` - A client sends a message to their game
- `content` - The message contents
- `room` - The room to send the message to
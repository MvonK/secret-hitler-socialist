# HTTP endpoints of the app
All take certain parameters in as json data. May respond in different formats

### `/login`
- `username` - login username
- `password` - password associated with the response

This is an endpoint to send a POST request to with a username and password. If the credentials
are correct, code `200` will be returned and session cookie modified to represent the logged in status

Possible reponses: 
- `200` - OK, login successful
- `401` - Password didn't match the user
- `404` - User does not exist
- `400` - Wrong request, missing the username or password field


### `/logout`
- No parameters

Logs out the user, removing the session info and disconnecting them from the socketio handler,
if connected.
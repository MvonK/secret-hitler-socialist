# Design thoughts

This should be some summary of my thoughts on how the whole project should be designed. I am going to reuse many ides 
from my previous [project lambda](https://github.com/MvonK/lambda-connector). This applies mostly to backend. 
For frontend I am going to learn React because its cool and why not. 

### Backend
Technologies I'll use: Flask, flask-socketio, eventlet, redis, maybe docker. Most game communication will run via the
socketio protocol, because of its ease-of-use. The flask-socketio lib is nice and easy and I'm gonna take full 
advantage of that. Redis for some persistent storage and stuff, and docker if I want to scale it/make it more portable.

The issue I came accross in my last project was mostly the login system. The existing flask implementations are not 
compatible with flask-socketio, so the login system and relevant access points will have to be done by hand, 
nothing too bad. Socketio connection will only be allowed to be made, if the user is logged in. 

### Frontend
As I said in the intro, I'm gonna use React. I've never done react before, and a very little of vanilla javascript so
that's gonna be interesting. I don't have any ideas as of now, most of the design thoughts will probably come when I 
actually dive into designing the interface.

### Shitler core

The shitler-core module is really old and not-so-well written, I am going to rewrite it. It should, however, be able to 
run the shitler engine once it is done. It should be separated from the server and api as much as possible, for future
recycling. Or if i decide to write a discord bot for it lol. The kinda iffy part will be user input, as the game will 
have to wait for it and I'm not quite sure yet how I'm going to do that. I'm also going to need to add documentation to 
the engine, as currently it has none and is pretty incomprehensible. 

Quite interesting mechanic in the game itself are powers. They should be easily extensible, because expansions come and 
go, so their implementation should be as straight-forward as possible. Every event should have a unique string 
identifier such as "investigate". Powers usually also require some sort of extra input, like which player to 
investigate. When the power itself is executed, it should ask a client for generic input like "player", and provide
extra information like "Choose a player to investigate".

### Communication
The main idea behind communication is so that the client page will receive game states regularly, and will update
itself accordingly. This shouldn't be too hard due to nature of how react works. When the client should submit input
like a vote, or a player to execute, client should receive an according socketio event, with a unique ID. 
Then when the input is gathered, it should send a response to event, using the ID received in the request. This should
make it easier to debug and make the communication clear. 

The client does not have many input types available. It can be either Ja/Nein, Player (to investigate, 
execute etc.), pick a card from selection (i.e. when passing a policy), or a claim. 
The game state will also have to contain some private, per-player information. For example fascists know who hitler is 
so that has to reflect on the frontend. Game state should be sent out whenever client asks, or whenever the 
state changes.

### Redis
Redis is a simple key-value storage. It will be used to store mostly user data, such as ELO, password etc. Every client
will be assigned a unique UID, when they create a new account. This will also be a key in the redis db, prefixed by
`user-`. The value will be then json of the user. 
import io from 'socket.io-client';

export default io("localhost:8080/");
// export default io({ reconnect: false });
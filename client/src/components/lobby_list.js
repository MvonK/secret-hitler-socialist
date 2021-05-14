import react from "react"
import socket from "./socket"
import { Redirect } from "react-router-dom"

class Lobby extends react.Component {
  constructor(props) {
    super(props);
    console.log(props)
    this.state = {data: props.data, redirecting: false}
    this.joinGame = this.joinGame.bind(this)
  }

  joinGame() {
    this.setState({redirecting: true})
  }

  render() {
    if (this.state.redirecting) {
      return <Redirect to={"/game/" + this.state.data.id}/>
    } else {
      return (
        <div id={"lobby" + this.state.data.id} onClick={this.joinGame} className={"hoverable"}>
          This is a lobby with ID {this.state.data.id}
        </div>
      )
    }
  }
}

class LobbyList extends react.Component {
  constructor(props) {
    super(props);

    this.state = {lobbies: []}
    this.createGame = this.createGame.bind(this)
  }

  componentDidMount() {
    socket.on("lobby_create", (data) => {
      console.log("New lobby")
      console.log(data.lobby)
      let lobbies = [...this.state.lobbies]
      lobbies.push(data.lobby)
      this.setState({"lobbies": lobbies})
    })

    socket.on("lobby_delete", (data) => {
      console.log("Lobby deletion! ID: " + data.id)
      let lobbies = []
      this.state.lobbies.forEach(filter)

      function filter(item, index) {
        if (item.id !== data.id) {
          lobbies.push(item)
        }
      }

      this.setState({lobbies: lobbies})
    })

    socket.on("lobby_change", (data) => {
      console.log("Lobby edited! ID: " + data.lobby.id)
      let lobbies = []
      this.state.lobbies.forEach(filter)

      function filter(item, index) {
        if (item.id === data.id) {
          lobbies.push(data.lobby)
        } else {
          lobbies.push(item)
        }
      }

      this.setState({lobbies: lobbies})
    })
  }

  createGame() {
    socket.emit("create_lobby")
  }

  render() {
    return (
      <div id={"lobbylist"}>
        <button onClick={this.createGame}>Create game</button>

        <div id={"lobbies"}>
          {this.state.lobbies.map((lobby, ind) => <Lobby key={ind} data={lobby}/>)}
        </div>
      </div>
    )
  }
}

export default LobbyList;
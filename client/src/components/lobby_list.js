import react from "react"
import socket from "./socket"
import {Redirect, useLocation} from "react-router-dom"

class Lobby extends react.Component {
  constructor(props) {
    super(props);
    console.log(props)
    this.state = {data: props.data, redirecting_to: false}
    this.joinGame = this.joinGame.bind(this)
  }

  joinGame() {
    this.setState({redirecting_to: "/game/" + this.state.data.id})
  }

  render() {
    if (this.state.redirecting_to !== false) {
      return <Redirect to={this.state.redirecting_to}/>
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

    this.state = {lobbies: [], redirecting_to: undefined}
    this.createGame = this.createGame.bind(this)
  }

  componentWillUnmount() {

    console.log("UNMOUNTING LOBBYLIST YYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
  }

  componentDidMount() {
    console.log("MOUNTING LOBBYLIST AAAAAAAAAAAAAAAAAAAA")
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
    // socket.emit("create_lobby")
    this.setState({redirecting_to: "/main/options"})
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevState.redirecting_to !== undefined) {
      this.setState({redirecting_to: undefined})
    }
  }

  render() {
    if(this.state.redirecting_to !== undefined) {
      return <Redirect to={this.state.redirecting_to}/>
    }
    if (window.location.pathname !== "/main/lobbies"){
      return null
    }

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
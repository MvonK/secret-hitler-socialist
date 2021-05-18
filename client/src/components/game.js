import react from "react"
import socket from "./socket"
import ChatBlock from "./chat";


const image_prefix = "../static/images/game/tracks/"

class Player extends react.Component {
  constructor(props) {
    super(props);

    this.state = {id: props.id, party: props.party, alive: true}

  }

  componentDidMount() {
    socket.on("party_revealed", (data) => {
      if (data.player === this.state.id){
        this.setState({party: data.party})
      }
    })

    socket.on("player_shot", (data) => {
      if (data.player === this.state.id) {
        this.setState({alive: false})
      }
    })
  }

  render() {
    return (
      <div>
        This is player {this.state.id}
      </div>
    )
  }
}

class CardPlace extends react.Component {
  constructor(props) {
    super(props);


  }

  render() {
    let power = this.props.power;
    if (power == null){
      power = "None"
    }
    let power_images = []
    for (let i in this.props.power){
      let name = this.props.power[i]
      if (name === null){
        name = "None"
      }
      const powername = name.charAt(0).toUpperCase() + name.slice(1);
      power_images.push(<img src={image_prefix + this.props.party + "Power" + powername + ".png"} alt={this.props.party + " power to " + name}/>)
    }
    const policy_img = <img src={image_prefix + this.props.party + "Policy.png"} alt={this.props.party + " policy"}/>

    return (
      <div style={{...this.props.style,  backgroundImage: `url(${image_prefix + this.props.party + "TrackCard.png"})`}}>
        {(this.props.filled ? policy_img : power_images)}

      </div>
    )

  }
}

class PolicyBoard extends react.Component {
  constructor(props) {
    super(props);

    this.state = {party: props.party, powers: props.powers, policies: props.policies}
  }

  componentDidMount() {
    socket.on("policy_played", (data) => {
      if (data.policy === this.state.party) {
        this.setState({policies: this.state.policies + 1})
      }
    })
  }

  render() {
    let card_places = []
    for (let i = 0; i < this.state.powers.length; i++) {
      card_places.push(<CardPlace party={this.state.party} power={this.state.powers[i]}
                                  filled={this.state.policies > i}
                                  style={{
                                    position: "relative",
                                    width: 190, height: 259, float: "left"
                                  }}/>)
    }
    return (
      <div
        style={{
          backgroundImage: `url(${image_prefix + this.state.party + "Track.png"})`,
          width: "1304px",
          height: "422px",
          transform: "scale(0.8, 0.8)",
          position: "relative",
        }}>
        <div style={{top:83, left:65, position:"relative"}}>
          {card_places}
        </div>
      </div>
    )
  }
}

class LobbyBlock extends react.Component {

  constructor(props) {
    super(props);
    console.log(props.id)

    this.state = {id: props.id, joined: false, data: {}}

    this.on = this.on.bind(this)
    this.join = this.join.bind(this)

  }

  join(){
    console.log("Joining!")
    //this.setState({joined: true})
    socket.emit("join_lobby", {lobby_id: this.state.id})
  }

  on(event, callback) {
    socket.on(event, (data) => {
      if (data.lobby.id === this.state.id) {
        callback(data)
      }
    })
  }

  componentDidMount() {
    this.on("lobby_change", (data) => {
      this.setState({data: {...this.state.data, ...data.lobby}})
    })
    this.on("joined_game", (data) => {
      this.setState({data: {...this.state.data, ...data.lobby}, joined: true})
    })
    socket.emit("fetch_lobby", {"lobby_id": this.state.id})
  }

  render() {
    let boards = []
    console.log(this.state)
    if (this.state.data["options"] !== undefined) {
      for (let i = 0; i < this.state.data.options.parties_playing.length; i++) {
        const party = this.state.data.options.parties_playing[i]
        console.log(party)
        boards.push(<PolicyBoard party={party} powers={this.state.data.options.board_format[party]}
                                 policies={this.state.data.options.board[party]}/>)
      }
    }

    console.log(boards)
    //<PolicyBoard party={"Fascist"} powers={[null, null, "Inv", null, null]} policies={2}/>

    return (
      <div>
        This a game called {this.state.id}!
        {(this.state.joined ? <div>Joined</div> : <button onClick={this.join} style={{cursor: "pointer"}}>Join!</button>)}
        {boards}
        <ChatBlock roomName={this.state.id}/>
      </div>
    )
  }
}

export default LobbyBlock;
import react from "react"
import socket from "./socket"
import ChatBlock from "./chat";
import input_manager from "./input_manager"


const image_prefix = "../static/images/game/tracks/"

class Player extends react.Component {
  constructor(props) {
    super(props);

    this.state = {id: props.id, party: props.party, alive: true}
    this.onClick = this.onClick.bind(this)
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

  onClick(data) {
    this.setState({id: this.state.id + "_"})
  }

  render() {
    return (
      <div className={"fas"}
           style={{
             width: "100px",
             height: "155px",
             cursor: "pointer",
             gridColumn: this.props.gridColumn,
             gridRow: 1
           }} onClick={this.onClick}>
        <div>
          {this.state.id}
        </div>
        <img src={image_prefix + "player_icon.png"}/>
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
      power_images.push(<img key={i} src={image_prefix + this.props.party + "Power" + powername + ".png"} alt={this.props.party + " power to " + name}/>)
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
      card_places.push(<CardPlace key={i}
                                  party={this.state.party} power={this.state.powers[i]}
                                  filled={this.state.policies > i}
                                  style={{
                                    gridRow: 2, gridColumn: i+2
                                  }}/>)
    }
    return (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "5% 15% 15% 15% 15% 15% 10%",
          gridTemplateRows: "19% 60% 18%"
        }}>
        <img style={{gridRowStart:1, gridRowEnd: 3, gridColumnStart: 1, gridColumnEnd: 9}} src={image_prefix + this.state.party + "Track.png"}/>
        {card_places}

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

  join() {
    console.log("Joining!")
    //this.setState({joined: true})
    socket.emit("join_lobby", {lobby_id: this.state.id})
  }

  on(event, callback) {
    socket.on(event, (lobby) => {
      if (lobby.id === this.state.id) {
        callback(lobby)
      }
    })
  }

  componentDidMount() {
    this.on("lobby_change", (lobby) => {
      let is_joined = false
      if (lobby.private !== undefined) {
        if (lobby.private.joined) {
          is_joined = true
        }
      }
      this.setState({data: {...this.state.data, ...lobby}, joined: is_joined})
    })
    this.on("joined_game", (lobby) => {
      this.setState({data: {...this.state.data, ...lobby}, joined: true})
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
                                 policies={this.state.data.options.board[party]}
                                 key={i}
        />)
      }
    }

    let players = []
    if (this.state.data.users !== undefined) {
      for (let i = 0; i < this.state.data.users.length; i++) {
        players.push(<Player id={this.state.data.users[i]} key={i} gridColumn={2 + 2 * i}/>)
      }
    }

    console.log(boards)
    //<PolicyBoard party={"Fascist"} powers={[null, null, "Inv", null, null]} policies={2}/>

    return (
      <div style={{
        display:"grid",
        gridTemplateColumns: "120px 60% auto",
        gridTemplateRows: "75px 175px 300px "
      }}>
        <div style={{
          gridColumn: 2,
          gridRow: 1
        }}>
          This a game called {this.state.data.name}!
          {(this.state.joined ? <div>Joined</div> :
            <button onClick={this.join} style={{cursor: "pointer"}}>Join!</button>)}
        </div>
        <div style={{gridRow: 2, gridColumn:1,
          display:"grid", gridTemplateColumns: "120px 120px 10px 120px 10px 120px 10px 120px 10px 120px 10px 120px 10px 120px 10px 120px"
        }}>
          {players}
        </div>
        <div style={{gridRow: 3, gridColumn:2,
          display:"grid", gridTemplateColumns:"auto", gridTemplateRows: "120% 120% auto"}}>
          {boards}
        </div>
        <div style={{gridRow:3, gridColumn:3}}>
          <ChatBlock roomName={this.state.id}/>
        </div>
      </div>
    )
  }
}

export default LobbyBlock;
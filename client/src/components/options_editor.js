import react from "react"
import socket from "./socket"
import {Redirect, useLocation} from "react-router-dom"



class PartyOptions extends react.Component {
  constructor(props) {
    super(props)

    this.state = {
      powers: [[null], [null], [null], [null], [null]],
      starting_policies: 0,
      amount_in_draw_deck: 6,
      loyal_players: 2,
      playing: true
    }

    this.onStartingPoliciesChange = this.onStartingPoliciesChange.bind(this)
    this.onDeckAmountChange = this.onDeckAmountChange.bind(this)
    this.onPlayerAmountChange = this.onPlayerAmountChange.bind(this)
    this.onTogglePlaying = this.onTogglePlaying.bind(this)
  }

  onStartingPoliciesChange(data) {
    this.setState({starting_policies: data.nativeEvent.data})
  }

  onDeckAmountChange(data) {
    this.setState({amount_in_draw_deck: data.nativeEvent.data})
  }

  onPlayerAmountChange(data) {
    this.setState({loyal_players: data.nativeEvent.data})
  }

  onTogglePlaying(data) {
    this.setState({playing: !this.state.playing})
  }

  render() {

    return (
      <div>

        <div style={{paddingBlock: "15px"}}>
          <div style={{cursor: "pointer"}} onClick={this.onTogglePlaying}>
            <b>Party: {this.props.party} {this.state.playing ? "-" : "(not playing)"}</b>
          </div>
          {this.state.playing ?
            <div>
              <div>
                Starting amount of policies on board: <input type={"number"} min={0}
                                                             value={this.state.starting_policies}
                                                             onChange={this.onStartingPoliciesChange}
                                                             style={{width: "35px"}}/>
              </div>
              <div>
                Amount of policies in deck: <input type={"number"} min={0} value={this.state.amount_in_draw_deck}
                                                   onChange={this.onDeckAmountChange} style={{width: "35px"}}/>
              </div>
              <div>
                Amount of loyal players: <input type={"number"} min={0} value={this.state.loyal_players}
                                                onChange={this.onPlayerAmountChange} style={{width: "35px"}}/>
              </div>
            </div>
            : ""
          }
        </div>
      </div>
    )
  }
}

class OptionsEditorBlock extends react.Component {
  constructor(props) {
    super(props);
    this.state = {
      redirect: undefined,
      party_options: {
        Liberal: react.createRef(),
        Fascist: react.createRef(),
        Socialist: react.createRef(),
      }
    }
    this.goToLobbyList = this.goToLobbyList.bind(this)


    this.createGame = this.createGame.bind(this)
  }

  createGame(data) {
    let options = {starting_policies: {}, board_format: {}, deck_contents: {}, loyal_players: {}}
    let parties_playing = []
    for (let p in this.state.party_options) {
      if (this.state.party_options[p].current.state.playing) {
        parties_playing.push(p)
      }
    }
    options["parties_playing"] = parties_playing

    for (let i in parties_playing) {
      const p = parties_playing[i]
      console.log(p)
      const party_options = this.state.party_options[p].current.state
      options["starting_policies"][p] = parseInt(party_options.starting_policies)
      options["board_format"][p] = party_options.powers
      options["deck_contents"][p] = parseInt(party_options.amount_in_draw_deck)
      options["loyal_players"][p] = parseInt(party_options.loyal_players)
    }

    socket.emit("create_lobby", {options: options})
  }

  goToLobbyList(data) {
    this.setState({redirect: "/main/lobbies"})
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevState.redirect!== undefined) {
      this.setState({redirect: undefined})
    }
  }

  render() {
    if (window.location.pathname !== "/main/options"){
      return null
    }
    if (this.state.redirect !== undefined) {
      return (
        <Redirect to={this.state.redirect}/>
      )
    }

    let options_list = []
    for (let p in this.state.party_options) {
      options_list.push(<PartyOptions party={p} ref={this.state.party_options[p]} key={p}/>)
    }

    return (
      <div>
        <button onClick={this.goToLobbyList}>View lobbies</button>
        {options_list}
        <button onClick={this.createGame}>Create game!</button>
      </div>
    )
  }
}

export default OptionsEditorBlock;
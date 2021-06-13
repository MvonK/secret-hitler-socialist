import socket from "./socket"

class InputRequest {
  constructor(id, type, description) {
    this.id = id
    this.type = type
    this.description = description
  }

  respond(data){
    socket.emit("input_response", {"data": data})
  }
}

class InputManager {
  constructor() {
    this.requests = []


  }

  process_input(type, data) {
    let newreqes = []
    let responded = false
    for (let i = 0; i < this.requests.length; i++) {
      if (this.requests[i].type === type) {
        if (!responded) {
          this.requests.respond(data)
          responded = true
        } else {
          newreqes.push(this.requests[i])
        }
      } else {
        newreqes.push(this.requests[i])
      }
    }
    this.requests = newreqes
  }

  playerClick(player_id) {
    this.process_input("player", player_id)
  }

  voteClick(vote) {
    this.process_input("vote", vote)
  }

}

let input_manager = new InputManager();
export default input_manager

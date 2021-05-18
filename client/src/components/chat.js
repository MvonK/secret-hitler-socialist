import react from "react"
import socket from "./socket"
import {Redirect} from "react-router-dom";

class ChatBlock extends react.Component {
  chatContainer = react.createRef();

  constructor(props) {
    super(props);
    this.state = {textval: "", messages: [], redirect: undefined}
    this.roomName = props.roomName
    this.mystyle = {
      minWidth: "550px",
      maxWidth: "1500px",
      minHeight: "350px",
      maxHeight: "200px",
      position: "relative",
      float: "right"
    }

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);

  }

  componentDidMount() {
    socket.on("chat_message_create", (msg) => {
      if(msg.room === this.roomName) {
        this.newMessage(msg.author + ": " + msg.content)
      }
    })
    socket.on("connect", () => {
      this.setState({textval: ""})
      socket.emit("join_chatroom", {"name": this.roomName})
    })

    socket.on("joined_game", (data) => {
      console.log("Redirecting to game " + data.lobby.id + " cuz joined")
      this.setState({redirect: "/game/" + data.lobby.id})
    })

    socket.emit("join_chatroom", {"name": this.roomName})
  }

  componentWillUnmount() {
    socket.emit("leave_chatroom", {"name": this.roomName})
  }

  newMessage(message) {
    let all_messages = [...this.state["messages"]]
    all_messages.push(message)
    this.setState({messages: all_messages}, () => this.scrollToMyRef());
  }

  handleChange(event) {
    this.setState({textval: event.target.value});
  }

  handleSubmit(event) {
    const msg = this.state.textval;
    this.setState({textval: ""})
    socket.emit("chat_message_send", {content: msg, room: this.roomName})
    event.preventDefault();
  }

  scrollToMyRef = () => {
    const scroll =
      this.chatContainer.current.scrollHeight -
      this.chatContainer.current.clientHeight;
    this.chatContainer.current.scrollTo(0, scroll);
  };

  componentDidUpdate(prevProps, prevState, snapshot) {
    this.state.redirect = undefined
  }

  render() {
    if(this.state.redirect !== undefined){
      return(
        <Redirect to={this.state.redirect}/>
      )
    }

    return (
      <div className={"chat"} style={{...this.mystyle, ...this.props.style}}>
        <div ref={this.chatContainer}
             style={{textAlign: "left", marginLeft: "10px", overflowY:"auto", maxHeight:"320px", boxSizing:"inherit", height: "100%", width:"90%", position:"absolute", "top":0}}>
          {this.state.messages.map((str, ind) => <p key={ind} style={{marginBlock: "5px", inset:0, overflowX: "hidden"}}>{str}</p>)}
        </div>

        <form onSubmit={this.handleSubmit} style={{float:"bottom", position:"absolute", width: "100%", bottom: "0px"}}>
          <input type={"text"} value={this.state.textval} onChange={this.handleChange} style={{width:"85%", float:"left"}} disabled={socket.disconnected}
                 placeholder={socket.ws.readyState === WebSocket.OPEN ? "Type in message..." : "You are not logged in"}/>
          <button className={"chatBtn"} onClick={this.handleSubmit} style={{width:"10%", float:"center"}}>
            Send
          </button>
        </form>
      </div>
    )
  }
}

export default ChatBlock;
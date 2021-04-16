import react from "react"
import socket from "./socket"

class ChatBlock extends react.Component {
  chatContainer = react.createRef();

  constructor(props) {
    super(props);
    this.state = {textval: "", messages: []}

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  componentDidMount() {
    socket.on("chatMessageCreate", (msg) => this.newMessage(msg.author + ": " + msg.content))
  }

  newMessage(message) {
    console.log("New mesage omg lol whattt" + message)
    let all_messages = this.state["messages"]
    all_messages.push(message)
    this.setState({messages: all_messages}, () => this.scrollToMyRef());
  }

  handleChange(event) {
    this.setState({textval: event.target.value});
  }
  handleSubmit(event) {
    const msg = this.state.textval;
    this.setState({textval: ""})
    socket.emit("chatMessageSend", {content: msg, room: "general"})
    event.preventDefault();
  }

  scrollToMyRef = () => {
    const scroll =
      this.chatContainer.current.scrollHeight -
      this.chatContainer.current.clientHeight;
    this.chatContainer.current.scrollTo(0, scroll);
  };

  render() {
    return (
      <div className={"chat"} style={this.props.style}>
        <div ref={this.chatContainer}
             style={{textAlign: "left", marginLeft: "10px", overflow:"scroll", maxHeight:"320px", boxSizing:"inherit"}}>
          {this.state.messages.map((str, ind) => <p key={ind} style={{marginBlock: "5px", inset:0}}>{str}</p>)}
        </div>

        <form onSubmit={this.handleSubmit} style={{bottom:0, position:"absolute", width: "100%"}}>
          <input type={"text"} value={this.state.textval} onChange={this.handleChange} style={{width:"80%"}}/>
          <button className={"chatBtn"} onClick={this.handleSubmit} style={{width:"10%"}}>
            Send
          </button>
        </form>
      </div>
    )
  }
}

export default ChatBlock;
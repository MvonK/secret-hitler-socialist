import react from "react"
import socket from "./socket";

class LoginBlock extends react.Component {
  constructor(props) {
    super(props);
    this.state = {username: "", password: ""}

    this.handleUsernameChange = this.handleUsernameChange.bind(this);
    this.handlePassChange = this.handlePassChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getLoginForm = this.getLoginForm.bind(this)
    this.getLoginInfo = this.getLoginInfo.bind(this)

    this.buttonStyle = {maxWidth: "140px"}

    this.loginInfo = <div>
      {this.state.username}
    </div>
  }

  getLoginInfo() {
    socket.on("loginInfo", (resp) => {
      this.setState({username: resp.username})
    });
    socket.emit("fetchLoginInfo");
  }

  getLoginForm() {
    console.log("Giving out login form");
    return(
      <div id={"Login"}>
        <form onSubmit={this.handleSubmit} style={{maxWidth: "150px"}}>
          <input name={"username"} type={"text"} placeholder={"Username"} onChange={this.handleUsernameChange} style={this.buttonStyle}/>
          <input name={"password"} type={"text"} placeholder={"Password"} onChange={this.handlePassChange} style={this.buttonStyle}/>
          <button name={"submit"}>
            Submit
          </button>
        </form>
      </div>
    )
  }

  handleUsernameChange(event) {
    console.log(event);
    this.setState({username: event.target.value});
  }

  handlePassChange(event) {
    console.log(event);
    this.setState({password: event.target.value});
  }

  handleSubmit(event) {
    console.log(event);
    console.log(this.state)
    event.preventDefault();
  }

  componentDidMount() {
    this.getLoginInfo();
  }

  render(){
    return(
      <div style={{maxWidth: "150px", overflow:"hidden", float:"right"}}>
        {socket.connected ? this.loginInfo : this.getLoginForm()}
      </div>
    )
  }
}

export default LoginBlock;
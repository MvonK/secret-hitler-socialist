import react from "react"
import socket from "./socket";

class LoginBlock extends react.Component {
  constructor(props) {
    super(props);
    this.state = {username: "", password: "", loggedInUsername: "", loginMessage: ""}

    this.handleUsernameChange = this.handleUsernameChange.bind(this);
    this.handlePassChange = this.handlePassChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getLoginForm = this.getLoginForm.bind(this)
    this.getLoginInfo = this.getLoginInfo.bind(this)
    this.getLoginInfoBlock = this.getLoginInfoBlock.bind(this)
    this.handleLogout = this.handleLogout.bind(this)

    this.buttonStyle = {maxWidth: "140px"}

  }

  getLoginInfo() {
    console.log("Getting login info")
    //socket.disconnect()
    //socket.connect()
    //socket.emit("fetchLoginInfo");
    console.log("Getting finished waiting for event ig")
  }

  getLoginInfoBlock() {
    return (
      <div id={"loginInfoBlock"} style={{minWidth: "10px", paddingBlock: "5px"}}>
        Logged in as {this.state.loggedInUsername}!
        <form onSubmit={this.handleLogout}>
          <button style={this.buttonStyle} name={"logout"}>
            Logout
          </button>
        </form>
      </div>
    )
  }

  getLoginForm() {
    console.log("Giving out login form");
    return (
      <div id={"Login"}>
        <form onSubmit={this.handleSubmit} style={{maxWidth: "150px"}}>
          <input name={"username"} type={"text"} placeholder={"Username"} onChange={this.handleUsernameChange}
                 style={this.buttonStyle}/>
          <input name={"password"} type={"password"} placeholder={"Password"} onChange={this.handlePassChange}
                 style={this.buttonStyle}/>
          <button name={"submit"}>
            Submit
          </button>
          {this.state.loginMessage === "" ? "" : <div>{this.state.loginMessage}</div>}
        </form>
      </div>
    )
  }

  handleLogout(event) {
    fetch("/logout", {method: "POST"})
      .then(resp => console.log(resp))
    event.preventDefault();
    this.setState({loggedInUsername: ""})
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
    console.log(this.state);
    const reqOptions = {
      method: "POST",
      cache: 'no-cache',
      credentials: "include",
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({"username": this.state.username, "password": this.state.password}),
    };

    fetch("/login", reqOptions)
      .then(data => {
        console.log(data.headers.get('set-cookie')); // undefined
        console.log(document.cookie); // nope
        return data.text()
      })
      .then(txt => {
        this.setState({loginMessage: txt})
        this.getLoginInfo()
      })
    event.preventDefault();
  }

  componentDidMount() {
    socket.on("login_info", (resp) => {
      console.log("Login info received")
      console.log(resp)
      this.setState({loggedInUsername: resp.user.name})
    });
    this.getLoginInfo();
  }

  render() {
    return (
      <div style={{maxWidth: "150px", overflow: "hidden", float: "right"}}>
        {this.state.loggedInUsername === "" ? this.getLoginForm() : this.getLoginInfoBlock()}
      </div>
    )
  }
}

export default LoginBlock;
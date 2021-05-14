import './static/css/App.css';
import react from "react"
import ChatBlock from "./components/chat"
import LoginBlock from "./components/login";
import LobbyList from "./components/lobby_list"
import LobbyBlock from "./components/game";
import { Route, Switch, Redirect, useLocation } from 'react-router-dom';

function App() {
  return (
    <div className="App">
      <LoginBlock/>
      <h1 className={"App-header"}>
        Secret Hitler (at some point, hopefully)
      </h1>
      <Switch>
        <Route path={"/lobbies"}>
          <table style={{width: "100%", height: "100%"}}>
            <tbody>
            <tr>
              <td>
                <LobbyList/>
              </td>
              <td>
                <ChatBlock roomName={"general"}

                />
              </td>
            </tr>
            </tbody>
          </table>
        </Route>
        <Route path={"/secret"}>
          <Window/>
          This a secret!
          <Redirect to={"/chat"}/>
        </Route>
        <Route path={"/game/*"}>
          <LobbyBlock id={useLocation().pathname.split("/")[useLocation().pathname.split("/").length-1]}/>
        </Route>
        <Route path={"/"}>
          <Redirect to={"/lobbies"}/>
        </Route>
      </Switch>
      <Window/>
      {/*<img src={logo} className="App-logo" alt="logo" />*/}
    </div>
  );
}

class Window extends react.Component{
   render() {
     return(
       <div style={{
         marginLeft: "10%",
         marginBlock: "1px"
       }}>
         This is a window!
       </div>
     )
   }
}

export default App;

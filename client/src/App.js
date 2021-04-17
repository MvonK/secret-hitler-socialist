import './App.css';
import react from "react"
import ChatBlock from "./chat"
import LoginBlock from "./login";
import { BrowserRouter, Route, Switch, Redirect } from 'react-router-dom';

function App() {
  return (
    <div className="App">
      <h1>
        Secret Hitler (at some point, hopefully)!
      </h1>
      <LoginBlock/>
      <BrowserRouter>
        <Switch>
          <Route path={"/chat"}>
            <table style={{width: "100%", height: "100%"}}>
              <tbody>
              <tr>
                <td>
                  Nothing
                </td>
                <td>
                  <ChatBlock roomName={"general"}
                    style={{
                    backgroundColor: "lightblue",
                    minWidth: "550px",
                    minHeight: "350px",
                    maxHeight: "200px",
                    position: "relative",
                  }}
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
          <Route path={"/"}>
            <Redirect to={"/chat"}/>
          </Route>
        </Switch>
        <Window/>
        {/*<img src={logo} className="App-logo" alt="logo" />*/}
      </BrowserRouter>
    </div>
  );
}

class Window extends react.Component{
   render() {
     return(
       <div style={{
         backgroundColor: "lightblue",
         marginLeft: "10%",
         marginBlock: "1px"
       }}>
         This is a window!
       </div>
     )
   }
}

export default App;

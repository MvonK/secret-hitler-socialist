class BetterWebSocket extends WebSocket{
  constructor(url) {
    super(url);
    this.hooks = {}

    this.on = this.on.bind(this)
    this.process_event = this.process_event.bind(this)

    this.onmessage = (event) => {this.process_event(JSON.parse(event))}

    this.onopen = () => {
      this.process_event(["connect", {}])
    }

    this.disconnect = this.close

  }

  process_event(event) {
    const event_name = event[0]
    const event_data = event[1]
    if (this.hooks[event_name] !== undefined){
      const callbacks = this.hooks[event_name]
      callbacks.forEach(cb => cb(event_data))
    }
  }

  on(event, callback) {
    if (this.hooks[event] === undefined){
      this.hooks[event] = []
    }
    this.hooks[event].push(callback)
  }

  emit(name, data) {
    if (this.readyState !== WebSocket.OPEN) {
      this.addEventListener("open", () => {
        this.emit(name, data)
      })
    } else {
      this.send(JSON.stringify([name, data]))
    }
  }


}

export default new BetterWebSocket("ws://" + window.location.hostname + "/")


//export default io("/");
// export default io({ reconnect: false });
class BetterWebSocket {
  constructor(url) {
    this.url = url
    this.new_ws()
    this.hooks = {}

    this.on = this.on.bind(this)
    this.process_event = this.process_event.bind(this)


  }

  new_ws() {
    if (this.ws !== undefined) {
      this.ws.close()
    }
    this.ws = new WebSocket(this.url)
    this.ws.onopen = () => {
      this.process_event(["connect", {}])
    }
    this.disconnect = this.ws.close
    this.ws.onmessage = (event) => {
      this.process_event(JSON.parse(event.data))
    }
  }

  process_event(event) {
    console.log(event)
    const event_name = event[0]
    const event_data = event[1]
    if (this.hooks[event_name] !== undefined) {
      const callbacks = this.hooks[event_name]
      console.log("Calling " + callbacks.length + " hooks for event " + event_name)
      callbacks.forEach(cb => cb(event_data))
    }
  }

  on(event, callback) {
    if (this.hooks[event] === undefined) {
      this.hooks[event] = []
    }
    this.hooks[event].push(callback)

    console.log(this.hooks)
  }

  emit(name, data) {
    if (this.ws.readyState !== WebSocket.OPEN) {
      this.ws.addEventListener("open", () => {
        this.emit(name, data)
      })
    } else {
      this.ws.send(JSON.stringify([name, data]))
    }
  }


}

export default new BetterWebSocket("ws://" + window.location.hostname + (window.location.port ? ':'+window.location.port: '') + "/ws")


//export default io("/");
// export default io({ reconnect: false });
import logging

import flask as fl

log = logging.getLogger("routes")


def setup_routes(app, user_manager, sio_handler):
    @app.route("/")
    def root():
        return fl.send_file("client/build/index.html")

    default_routes = ("/chat", "/secret")
    for r in default_routes:
        app.add_url_rule(r, view_func=root)

    @app.route("/<path:path>")
    def default(path):
        log.debug(f"Serving {path}")
        if path is None:
            path = "index.html"
        return fl.send_from_directory("client/build/", path)

    @app.route("/login", methods=["POST"])
    def login():
        username = fl.request.json.get("username")
        password = fl.request.json.get("password")
        if username and password:
            user = user_manager.get_user(user_manager.get_uid(username))
            if user:
                if user.password == password:
                    log.info(f"User {user.uid} logged in successfully.")
                    fl.session["uid"] = user.uid
                    fl.session.modified = True
                    return fl.Response("Login successful", status=200)
                return fl.Response("Wrong password", status=401)
            return fl.Response("No such user", status=404)
        return fl.Response("Missing username or password", status=400)

    @app.route("/logout", methods=["POST"])
    def logout():
        log.info(f"User {fl.session.get('uid')} logging out")
        uid = fl.session.pop("uid")
        if uid:
            sio_handler.disconnect_user(uid)
            return fl.Response("Logged out", status=200)
        return fl.Response("Wtf lol")

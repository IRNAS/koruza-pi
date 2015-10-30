import flask
import flask_webpack
import gevent
from gevent import select
import geventwebsocket
import nnpy

webpack = flask_webpack.Webpack()
app = flask.Flask(
    __name__,
    static_folder='./build/public',
)
app.config.update({
    'WEBPACK_MANIFEST_PATH': './build/manifest.json',
})
webpack.init_app(app)
clients = []
command_bus = None


@app.route('/')
def webui():
    return flask.render_template('index.html')


@app.route('/ws')
def websocket():
    ws = flask.request.environ.get('wsgi.websocket')
    if not ws:
        flask.abort(400, "Expected WebSocket request.")

    # Register a new client subscription.
    clients.append(ws)
    try:
        while True:
            try:
                message = ws.receive()

                if command_bus is None:
                    continue

                # Send the command.
                wfd = command_bus.getsockopt(nnpy.SOL_SOCKET, nnpy.SNDFD)
                rfd = command_bus.getsockopt(nnpy.SOL_SOCKET, nnpy.RCVFD)
                rl, wl, xl = select.select([], [wfd], [])
                command_bus.send(message)

                # Wait for a response and dispatch it via the web socket.
                rl, wl, xl = select.select([rfd], [], [])
                data = command_bus.recv()
                ws.send('command\x00' + data)
            except ValueError:
                pass
            except geventwebsocket.WebSocketError:
                break
    finally:
        clients.remove(ws)


def router(publisher):
    publisher_rfd = publisher.getsockopt(nnpy.SOL_SOCKET, nnpy.RCVFD)

    while True:
        # Check if we have anything to read.
        rl, wl, xl = select.select([publisher_rfd], [], [])

        if publisher_rfd in rl:
            # Dispatch received message to all subscribed clients.
            try:
                data = publisher.recv()
            except ValueError:
                continue

            for ws in clients[:]:
                try:
                    ws.send(data)
                except geventwebsocket.WebSocketError:
                    clients.remove(ws)

if __name__ == '__main__':
    publisher = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
    publisher.connect('ipc:///tmp/koruza-publish.ipc')
    publisher.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

    command_bus = nnpy.Socket(nnpy.AF_SP, nnpy.REQ)
    command_bus.connect('ipc:///tmp/koruza-command.ipc')

    # Spawn the nanomsg to websocket router.
    gevent.spawn(router, publisher)

    # Start the web socket server.
    server = geventwebsocket.WebSocketServer(('', 8080), app)
    server.serve_forever()

from gevent import monkey
monkey.patch_all()

import flask
import flask_webpack
import gevent
from gevent import select, socket
import geventwebsocket
import nnpy
import json
import spwd
import crypt


class Client(object):
    # Payload types.
    TYPE_COMMAND = 'command'
    TYPE_COMMAND_REPLY = 'cmd_reply'
    TYPE_COMMAND_ERROR = 'cmd_error'

    # Error codes (reused from HTTP).
    ERROR_BAD_REQUEST = 400
    ERROR_NOT_AUTHORIZED = 403
    ERROR_INTERNAL_SERVER_ERROR = 500
    ERROR_NOT_IMPLEMENTED = 501

    def __init__(self, socket, command_bus=None):
        self._command_bus = command_bus
        self._socket = socket
        self._authenticated = False
        self._active = False

        self._send_queue_processor = None
        self._send_queue = []

    def is_active(self):
        return self._active

    def send_queue(self, data):
        if not self._active:
            return

        self._send_queue.append(data)
        if self._send_queue_processor is None:
            self._send_queue_processor = gevent.spawn(self._process_send_queue)

    def _process_send_queue(self):
        while True:
            try:
                self._socket.send(self._send_queue.pop(0))
            except IndexError:
                break
            except geventwebsocket.WebSocketError:
                self._send_queue = []
                self._active = False
                break

        self._send_queue_processor = None

    def start(self):
        self._active = True
        try:
            while True:
                try:
                    message = self._socket.receive()
                    if not message:
                        break

                    try:
                        request = json.loads(message)
                        if request['type'] != Client.TYPE_COMMAND:
                            self.reply_error(Client.ERROR_BAD_REQUEST, "Clients may only send commands.")
                            continue

                        command = request['command']
                    except (ValueError, KeyError):
                        self.reply_error(Client.ERROR_BAD_REQUEST, "Malformed request.")
                        continue

                    if command == 'authenticate':
                        # Authentication request.
                        try:
                            username = request['username']
                            password = request['password']
                        except KeyError:
                            self.reply_error(Client.ERROR_BAD_REQUEST, "Malformed request.")
                            continue

                        if self.authenticate(username, password):
                            self.reply_ok({'authenticated': True})
                        else:
                            self.reply_error(Client.ERROR_NOT_AUTHORIZED, "Authentication failed.")
                    elif command == 'deauthenticate':
                        # Deauthentication request.
                        if self.deauthenticate():
                            self.reply_ok({'authenticated': False})
                        else:
                            self.reply_error(Client.ERROR_NOT_AUTHORIZED, "Deauthentication failed.")
                    elif command == 'get_status':
                        # The 'get_status' command is allowed even when the user is not authenticated.
                        def sanitize_reply(data):
                            if not self._authenticated:
                                # Ensure that private configuration is not sent to unauthenticated clients.
                                data = json.loads(data)
                                for key in data['config'].keys():
                                    if key.startswith('private_'):
                                        del data['config'][key]

                                data = json.dumps(data)

                            return data

                        self._relay_command(message, transform=sanitize_reply)
                    else:
                        if not self._authenticated:
                            self.reply_error(Client.ERROR_NOT_AUTHORIZED, "Not authorized.")
                            continue

                        self._relay_command(message)
                except geventwebsocket.WebSocketError:
                    break
        finally:
            if self._send_queue_processor is not None:
                processor = self._send_queue_processor
                self._send_queue_processor = None
                processor.kill()

            self._send_queue = []
            self._active = False

    def reply(self, data):
        self._socket.send('command@' + json.dumps(data))

    def reply_ok(self, data):
        msg = {
            'type': Client.TYPE_COMMAND_REPLY,
        }
        msg.update(data)
        self.reply(msg)

    def reply_error(self, code, message):
        self.reply({
            'type': Client.TYPE_COMMAND_ERROR,
            'code': code,
            'message': message,
        })

    def authenticate(self, username, password):
        if self._authenticated:
            return True

        try:
            entry = spwd.getspnam(username)
            if entry.sp_pwd in ['LK', '*', 'NP', '!!', '!', '', None]:
                return False

            if crypt.crypt(password, entry.sp_pwd) != entry.sp_pwd:
                return False
        except KeyError:
            return False

        self._authenticated = True
        return True

    def deauthenticate(self):
        self._authenticated = False
        return True

    def _relay_command(self, message, transform=lambda x: x):
        if self._command_bus is None:
            return

        # Send the command.
        wfd = self._command_bus.getsockopt(nnpy.SOL_SOCKET, nnpy.SNDFD)
        rfd = self._command_bus.getsockopt(nnpy.SOL_SOCKET, nnpy.RCVFD)
        rl, wl, xl = select.select([], [wfd], [])
        self._command_bus.send(message)

        # Wait for a response and dispatch it via the web socket.
        rl, wl, xl = select.select([rfd], [], [])
        data = transform(self._command_bus.recv())
        self._socket.send('command@' + data)

    def send_raw(self, data):
        self._socket.send(data)


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
    client = Client(ws, command_bus=command_bus)
    clients.append(client)
    try:
        client.start()
    finally:
        try:
            clients.remove(client)
        except ValueError:
            pass


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

            for client in clients[:]:
                client.send_queue(data)

if __name__ == '__main__':
    publisher = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
    publisher.connect('ipc:///tmp/koruza-publish.ipc')
    publisher.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

    command_bus = nnpy.Socket(nnpy.AF_SP, nnpy.REQ)
    command_bus.connect('ipc:///tmp/koruza-command.ipc')

    # Spawn the nanomsg to websocket router.
    gevent.spawn(router, publisher)

    # Start the web socket server.
    try:
        server = geventwebsocket.WebSocketServer(('', 80), app)
        server.serve_forever()
    except socket.error:
        server = geventwebsocket.WebSocketServer(('', 8080), app)
        server.serve_forever()

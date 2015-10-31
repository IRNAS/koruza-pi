import nnpy
import select
import json
import traceback


class Bus(object):
    def __init__(self):
        self._socket = nnpy.Socket(nnpy.AF_SP, nnpy.REQ)
        self._socket.connect('ipc:///tmp/koruza-command.ipc')

    def command(self, command, **data):
        data.update({
            'type': 'command',
            'command': command,
        })

        self._socket.send(json.dumps(data))
        try:
            return json.loads(self._socket.recv())
        except ValueError:
            return None


class Application(object):
    application_id = None

    def __init__(self):
        self._topic = 'application.%s' % self.application_id

    def start(self):
        # Establish IPC connections.
        publish = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        publish.connect('ipc:///tmp/koruza-publish.ipc')
        publish.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, 'status')
        publish.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, self._topic)

        command_bus = Bus()

        poll = select.poll()
        poll.register(publish.getsockopt(nnpy.SOL_SOCKET, nnpy.RCVFD), select.POLLIN)

        last_state = {}

        while True:
            # Check for incoming updates, block for at most 100 ms.
            fds = poll.poll(100)
            if fds:
                topic, payload = publish.recv().split('\x00')
                try:
                    data = json.loads(payload)
                except ValueError:
                    continue

                try:
                    if topic == self._topic:
                        if data['type'] == 'command':
                            self.on_command(command_bus, data, last_state)
                    elif topic == 'status':
                        last_state[data['type']] = data
                        self.on_status_update(command_bus, data)
                except:
                    traceback.print_exc()

            # Run local processing.
            self.on_idle(command_bus, last_state)

    def on_idle(self, bus):
        pass

    def on_command(self, bus, command):
        pass

    def on_status_update(self, bus, update):
        pass

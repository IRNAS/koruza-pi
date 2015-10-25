Installation
------------

First, prepare an installation package from this repository by running:

```
$ ./make-package.sh
```

This will give you a file `koruza-package.tar.bz2`, which you should copy
to the Raspberry Pi running KORUZA. You can do this by using `scp`. After
the file has been copied, connect to the Raspberry Pi and execute the
following commands:

```
$ sudo tar -xf koruza-package.tar.bz2 -C /
$ sudo /koruza/install
```

And this should install and configure all the needed services.

Debugging the KORUZA IPC bus
----------------------------

The IPC bus has two endpoints:

  * `/tmp/koruza-publish.ipc` is used for publishing status updates
    about all controlled devices.

  * `/tmp/koruza-command.ipc` is used for issuing commands to
    devices.

The following command may be used to inspect the data that is currently
being published by the `koruza-sensors` controller:

```
$ sudo nanocat --sub --connect-ipc /tmp/koruza-publish.ipc --ascii
```

If everything is working correctly, you should see a stream of messages
of the following form:

```json
status.{"type": "motors", "motor": {"current_f": 0, "flash_write_count": 34, "next_x": 150, "next_y": 200, "status_f": 0, "accel": 1000, "command": 0, "empty": 255, "status_y": 16, "status_x": 0, "laser": 0, "next_f": 0, "flash_status": 171, "speed": 1000, "current_y": 210, "current_x": 150}}
status.{"type": "sfp", "sfp": {"150918": {"temperature_c": 44.8671875, "tx_power_mw": 0.5691, "tx_bias_ma": 34.462, "rx_power_mw": 0.0, "vcc_v": 3.2437}}}
process.{"type": "watchdog", "time": 1445805609.989954}
status.{"type": "motors", "motor": {"current_f": 0, "flash_write_count": 34, "next_x": 150, "next_y": 200, "status_f": 0, "accel": 1000, "command": 0, "empty": 255, "status_y": 16, "status_x": 0, "laser": 0, "next_f": 0, "flash_status": 171, "speed": 1000, "current_y": 210, "current_x": 150}}
```

Each message consists of two parts separated by a NULL byte (shown as `.`).
The first part is the topic and the second part is the JSON payload.

To transmit commands you may also leverage the `nanocat` utility by doing
the following:

```
$ sudo nanocat --req --connect-ipc /tmp/koruza-command.ipc --ascii --data '{"type": "command", "command": "motor_move", "next_x": 150, "next_y": 200, "next_f": 0}'
{"status": "ok", "type": "cmd_reply"}
```

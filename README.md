
Installation
------------

From Git repository
===================

To install the latest version directly from the repository do the following on
the Raspberry Pi running KORUZA:

```
$ git clone https://github.com/IRNAS/koruza-pi
$ cd koruza-pi
$ sudo ./install.sh
```

Manual
======

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

Upgrade
-------

To upgrade an existing installation, copy over the package as above and then
run:

```
$ sudo /koruza/upgrade koruza-package.tar.bz2
```

Upgrade to the latest version
-----------------------------

To upgrade an existing installation to the latest version from the GitHub
repository, simply run:

```
$ sudo /koruza/upgrade
```

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
status@{"type": "motors", "motor": {"current_f": 0, "flash_write_count": 34, "next_x": 150, "next_y": 200, "status_f": 0, "accel": 1000, "command": 0, "empty": 255, "status_y": 16, "status_x": 0, "laser": 0, "next_f": 0, "flash_status": 171, "speed": 1000, "current_y": 210, "current_x": 150}}
status@{"type": "sfp", "sfp": {"150918": {"temperature_c": 44.8671875, "tx_power_mw": 0.5691, "tx_bias_ma": 34.462, "rx_power_mw": 0.0, "vcc_v": 3.2437}}}
process@{"type": "watchdog", "time": 1445805609.989954}
status@{"type": "motors", "motor": {"current_f": 0, "flash_write_count": 34, "next_x": 150, "next_y": 200, "status_f": 0, "accel": 1000, "command": 0, "empty": 255, "status_y": 16, "status_x": 0, "laser": 0, "next_f": 0, "flash_status": 171, "speed": 1000, "current_y": 210, "current_x": 150}}
```

Each message consists of two parts separated by an `@` character.
The first part is the topic and the second part is the JSON payload.

To transmit commands you may also leverage the `nanocat` utility by doing
the following:

```
$ sudo nanocat --req --connect-ipc /tmp/koruza-command.ipc --ascii --data '{"type": "command", "command": "motor_move", "next_x": 150, "next_y": 200, "next_f": 0}'
{"status": "ok", "type": "cmd_reply"}
```

---

#### License

All our projects are as usefully open-source as possible.

Hardware including documentation is licensed under [CERN OHL v.1.2. license](http://www.ohwr.org/licenses/cern-ohl/v1.2)

Firmware and software originating from the project is licensed under [GNU GENERAL PUBLIC LICENSE v3](http://www.gnu.org/licenses/gpl-3.0.en.html).

Open data generated by our projects is licensed under [CC0](https://creativecommons.org/publicdomain/zero/1.0/legalcode).

All our websites and additional documentation are licensed under [Creative Commons Attribution-ShareAlike 4 .0 Unported License] (https://creativecommons.org/licenses/by-sa/4.0/legalcode).

What this means is that you can use hardware, firmware, software and documentation without paying a royalty and knowing that you'll be able to use your version forever. You are also free to make changes but if you share these changes then you have to do so on the same conditions that you enjoy.

Koruza, GoodEnoughCNC and IRNAS are all names and marks of Institut IRNAS Rače.
You may use these names and terms only to attribute the appropriate entity as required by the Open Licences referred to above. You may not use them in any other way and in particular you may not use them to imply endorsement or authorization of any hardware that you design, make or sell.

Example controller
------------------

This is an example controller that shows how to write external applications that
use the KORUZA control bus. It is a very dumb controller, which registers itself
with the application identifier `example_controller` and basically performs the
following:

* By default it is in idle state until it receives a `start` command.
* When the `start` command is received, it remembers the current position of the
  motors and transitions into an activated state.
* While in activated state it requests the motor driver to move the X axis
  motor to 0 unless it is already there or it has already acknowledged that
  the next position should be 0.
* When the `stop` command is received, it requests the motor driver to move the
  motors to the pre-start position and transitions into an idle state.

To send commands to the controller via the command line you can use something like
the following (this sends the `start` command, but you can include any JSON
arguments which will be received by the controller):

```
$ sudo nanocat \
    --req --connect-ipc /tmp/koruza-command.ipc --ascii \
    --data '{"type": "command", "command": "call_application", "application_id": "example_controller", "payload": {"type": "command", "command": "start"}}'
```

#!/usr/bin/env python
import koruza
import math


class SpiralScan(koruza.Application):
    # This is the application identifier so that messages may be directed to
    # this specific application on the bus.
    application_id = 'spiral_scan'
    # Current state.
    state = 'idle'
    # Initial position.
    initial_position = None
    # Other variables
    n_points = 1 # Number of points in a line
    angle = 0 # Angle of lines
    # Counters
    i = 0
    j = 0
    # variables updated from GUI
    step = 100 # Step for scanning, can be updated from GUI when in idle state
    threshold = 10 # Threshold for auto stop, can be updated from GUI anytime

    def on_command(self, bus, command, state):
        if command['command'] == 'start' and self.state == 'idle':
            self.state = 'go'
            self.initial_position = state.get('motors', {}).get('motor')

            # Initialize variables.
            self.i = 0
            self.j = 0
            self.angle = 0
            self.n_points = 1

            # Get variables from the command that was sent on the bus.
            self.step = command.get('step', 100)
            self.threshold = command.get('threshold', 10)

            print 'got start command step=%d threshold=%d' % (self.step, self.threshold)
        elif command['command'] == 'stop' and self.state == 'go':
            print 'got stop command'
            self.state = 'idle'

    def on_idle(self, bus, state):
        if self.state == 'go':
            if not state.get('sfp') or not state.get('motors'):
                # Do nothing until we have known last state from SFP and motor drivers.
                return
            # Get last known state for the first SFP module.
            sfp = state['sfp']['sfp'].values()[0]
            # Get last known motor driver state.
            motor = state['motors']['motor']

            # Check if motors stopped moving
            if motor['status_x'] == 0 and motor['status_y'] == 0:

                # Calculate next points
                x = motor['current_x'] + math.cos(self.angle) * self.step
                y = motor['current_y'] + math.sin(self.angle) * self.step

                # Request the motor to move to the next point.
                bus.command('motor_move', next_x=x, next_y=y)
                self.j = self.j + 1 # Increase point count

                # Check if line is finished
                if self.j == self.n_points:
                    self.j = 0 # Reset point count
                    self.angle = self.angle + math.pi / 2 # Rotate for 90
                    self.i = self.i + 1 # Increase line count

                # Check if two lines are scanned
                if self.i == 2:
                    self.i = 0 # Reset line count
                    self.n_points = self.n_points + 1 # Increase nr. of points per line

                # Check if some signal was detected and terminate the movement
                if sfp['rx_power_mw'] > self.threshold:
                    self.state = 'idle'
                    print 'found optical power'

        elif self.state == 'idle':
            pass

SpiralScan().start()

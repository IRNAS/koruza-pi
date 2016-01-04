#!/usr/bin/env python
import koruza
import math
import time


class Alignment(koruza.Application):
    # This is the application identifier so that messages may be directed to
    # this specific application on the bus.
    application_id = 'alignment'
    # Should be true if the application would like to access the remote unit.
    needs_remote = True
    
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
    step = 500 # Step for scanning, can be updated from GUI when in idle state
    min_threshold = 5 # Threshold for auto stop, can be updated from GUI any time
    max_threshold = 22 #Stopping condition

    case = 0 # Current state case of the system

    # Best position
    best_x = 0
    best_y = 0
    best_rx = 0
    wanted_x = 0
    wanted_y = 0

    def on_command(self, bus, command, state, remote_state):
        if command['command'] == 'start' and self.state == 'idle':
            self.state = 'setup'
            self.initial_position = state.get('motors', {}).get('motor')

            # Initialize variables.
            self.i = 0
            self.j = 0
            self.angle = 0
            self.n_points = 2
            self.best_x = 0
            self.best_y = 0
            self.best_rx = 0

            # Get variables from the command that was sent on the bus.
            self.step = command.get('step', 500)
            self.min_threshold = command.get('min_threshold', 5)

            print 'got start command step=%d threshold=%d' % (self.step, self.max_threshold)
        elif command['command'] == 'stop' and self.state == 'go':
            print 'got stop command'
            self.state = 'idle'

    def on_idle(self, bus, state, remote_state):
        if self.state == 'setup':
            #time.sleep(0.1)
            if not state.get('sfp') or not state.get('motors'):
                # Do nothing until we have known last state from SFP and motor drivers.
                return
            # Get last known state for the first SFP module.
            sfp = state['sfp']['sfp'].values()[0]
            # Get last known motor driver state.
            motor = state['motors']['motor']

            self.wanted_x = motor['current_x']
            self.wanted_y = motor['current_y']
            self.state = 'go'

        elif self.state == 'go':
            #time.sleep(0.1)
            if not state.get('sfp') or not state.get('motors') or not remote_state.get('motors'):
                # Do nothing until we have known last state from SFP and motor drivers.
                return
            # Get last known state for the first SFP module.
            sfp = state['sfp']['sfp'].values()[0]
            # Get last known motor driver state.
            motor = state['motors']['motor']
            motor_remote = remote_state['motors']['motor']

            # Check if motors stopped moving i.e. previous step is finished
            if motor['current_x'] == self.wanted_x or motor['current_y'] == self.wanted_y or  motor_remote['status_x'] == 0 and motor_remote['status_y'] == 0:

                print 'State: %d, point: %d, line: %d, X: %f, X-next: %f, XX: %f, Y: %f, Y-next: %f, YY: %f, RX: %f, step: %d' % (self.case, self.j, self.i, motor['current_x'], motor['next_x'], self.wanted_x,  motor['current_y'],  motor['next_y'], self.wanted_y, sfp['rx_power_db'], self.step)
                # STATE 0: initial decision state
                if self.case == 0:
                    # initialise current position to best position
                    self.best_x = motor['current_x'] 
                    self.best_y = motor['current_y']
                    self.best_rx = sfp['rx_power_db']

                    # set angle to 0
                    self.angle = 0
                    self.i = 0
                    self.j = 0

                    if sfp['rx_power_db'] < self.min_threshold:
                        # If some signal is received go to line scan
                        self.case = 5
                        print 'Changed state: %d' % (self.case) 

                    else:
                        # If some signal is received go to line scan
                        self.case = 10
                        print 'Changed state: %d' % (self.case) 

                    
                # STATE 5: SPIRAL SCAN
                elif self.case == 5:
                    # Calculate next points
                    x = motor['current_x'] + math.cos(self.angle) * self.step
                    y = motor['current_y'] + math.sin(self.angle) * self.step
                    #Update variables
                    self.wanted_x = x
                    self.wanted_y = y

                    # Request the motor to move to the next point.
                    bus.command('motor_move', next_x=x, next_y=y)
                    self.j = self.j + 1 # Increase point count

                    # Check if better position was achieved - update values
                    if sfp['rx_power_db'] > self.best_rx:
                        self.best_x = motor['current_x'] 
                        self.best_y = motor['current_y']
                        self.best_rx = sfp['rx_power_db']

                    # Check if line is finished
                    if self.j == self.n_points:
                        self.j = 0 # Reset point count
                        self.angle = self.angle + math.pi / 2 # Rotate for 90
                        self.i = self.i + 1 # Increase line count

                    # Check if two lines are scanned
                    if self.i == 2:
                        self.i = 0 # Reset line count
                        self.n_points = self.n_points + 2 # Increase nr. of points per line
                        print 'Increase points per line: %d'  % (self.n_points)
                    

                    # Check if some signal was detected and terminate the movement
                    if sfp['rx_power_db'] > self.min_threshold:
                        # Go to line scan
                        self.case = 10
                        print 'found optical power, change state: %d'  % (self.case)
                        # Reset counters
                        self.j = 0
                        self.i = 0
                        self.angle = 0

                # STATE 10: LINE SCAN
                elif self.case == 10:
                    # Check if better position was achieved - update values
                    if sfp['rx_power_db'] > self.best_rx:
                        self.best_x = motor['current_x'] 
                        self.best_y = motor['current_y']
                        self.best_rx = sfp['rx_power_db'] 

                    # Check if line if finished
                    if sfp['rx_power_db'] > self.max_threshold:
                        self.state == 'idle'
                        print "Done!"
                        x = 0
                        y = 0
                    elif self.j == 5:
                        # Reset counter 
                        self.j = 0
                        # Increase line counter
                        self.i = self.i + 1
                        # if cross was made terminate the movement
                        if self.i == 8:
                            self.case = 1
                            # go to best point
                            x = self.best_x
                            y = self.best_y
                        # If best position is at the end of the line
                        elif sfp['rx_power_db'] == self.best_rx:
                            # Reset line counter and continue in same direction
                            self.i = 0
                            # Calculate next point
                            x = motor['current_x'] + math.cos(self.angle) * self.step
                            y = motor['current_y'] + math.sin(self.angle) * self.step
                        # else
                        else:
                            # update angle
                            self.angle = self.angle + math.pi / 2 # Rotate for 90
                            # go to best point 
                            x = self.best_x
                            y = self.best_y
                    # if the line scan is not completed yet
                    else:
                        # Calculate next point
                        x = motor['current_x'] + math.cos(self.angle) * self.step
                        y = motor['current_y'] + math.sin(self.angle) * self.step

                    #Update variables
                    self.wanted_x = x
                    self.wanted_y = y
                    # Request the motor to move to the next point.
                    bus.command('motor_move', next_x=x, next_y=y)
                    self.j = self.j + 1 # Increase point count


        elif self.state == 'idle':
            pass
        

Alignment().start()

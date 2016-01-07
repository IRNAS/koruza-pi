#!/usr/bin/env python
import koruza
import math


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
    step = 100 # Step for scanning, can be updated from GUI when in idle state
    min_threshold = 0 # Threshold for auto stop, can be updated from GUI any time
    max_threshold = 25 #Stopping condition

    case = 0 # Current state case of the system
    old_case = 0 # Save previous state

    # Best position
    best_x = 0
    best_y = 0
    best_rx = 0
    # Next wanted position
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
            self.step = command.get('step', 100)
            self.min_threshold = command.get('min_threshold', 5)

            print 'got start command step=%d threshold=%d' % (self.step, self.max_threshold)
        elif command['command'] == 'stop' and self.state == 'go':
            print 'got stop command'
            self.state = 'idle'

    def on_idle(self, bus, state, remote_state):
        if self.state == 'setup':
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
            if not state.get('sfp') or not state.get('motors') or not remote_state.get('motors'):
                # Do nothing until we have known last state from SFP and motor drivers.
                return
            # Get last known state for the first SFP module.
            sfp = state['sfp']['sfp'].values()[0]
            # Get last known motor driver state.
            motor = state['motors']['motor']
            motor_remote = remote_state['motors']['motor']

            # print 'Remote state x: %d, Remote state y: %d, current x: %f, wanted x: %f, current y: %f, wanted y: %f' % (motor_remote['status_x'], motor_remote['status_y'], motor['current_x'], self.wanted_x, motor['current_y'], self.wanted_y )
            # Check if motors stopped moving i.e. previous step is finished
            if motor['current_x'] == self.wanted_x and motor['current_y'] == self.wanted_y: #and  motor_remote['status_x'] == 0 and motor_remote['status_y'] == 0:

                print 'State: %d, old state: %d, line: %d, point: %d, X: %f, Y: %f, , RX: %f' % (self.case, self.old_case, self.i, self.j, motor['current_x'], motor['current_y'], sfp['rx_power_db'])
                # STATE 0: initial decision state
                if self.case == 0:
                    # Publish current state
                    self.publish({'case': 0})
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
                        self.old_case = 5
                        print 'Initialisation done, next state: %d' % (self.old_case)

                    else:
                        # If some signal is received go to line scan
                        self.old_case = 10
                        print 'Initialisation done, next state: %d' % (self.old_case)
                    self.case = 1
                    print 'Go to waiting state 1'

                # STATE 1: waiting state
                elif self.case == 1:
                    # Publish current state
                    self.publish({'case': 1})
                    print 'In waiting state 1, remote state: %s' %(remote_state.get('app_state', {}).get('case'))
                    # Check if other unit has finished movement
                    if remote_state.get('app_state', {}).get('case') == 1 or remote_state.get('app_state', {}).get('case') == None:
                        #Check if next predicted state is not 1
                        if not self.old_case == 1:
                            #Change state
                            self.case = self.old_case
                            print 'Other unit in state 1, go to next state: %d' % (self.old_case)
                        else:
                            # Check if power has declined
                            if sfp['rx_power_db'] < self.max_threshold:
                                self.case = 10
                                print 'Other unit in state 1, power declined, resume scanning.'
                            else:
                                print 'Other unit in state 1, wait in state 1.'

                # STATE 5: SPIRAL SCAN
                elif self.case == 5:
                    # Publish current state
                    self.publish({'case': 5})
                    # Calculate next points
                    self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step
                    self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step

                    # Request the motor to move to the next point.
                    bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
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
                        self.old_case = 10
                        print 'Found optical power, next state: %d'  % (self.case)
                        # Go to waiting state
                        self.case = 1
                        print 'Go to waiting state 1'
                        # Reset counters
                        self.j = 0
                        self.i = 0
                        self.angle = 0

                # STATE 10: LINE SCAN
                elif self.case == 10:
                    # Publish current state
                    self.publish({'case': 10})
                    # Check if better position was achieved - update values
                    if sfp['rx_power_db'] > self.best_rx:
                        self.best_x = motor['current_x'] 
                        self.best_y = motor['current_y']
                        self.best_rx = sfp['rx_power_db'] 

                    # Check if line is finished
                    if sfp['rx_power_db'] > self.max_threshold:
                        print "Done!"
                        # Stay at the current point
                        self.wanted_x = motor['current_x']
                        self.wanted_y = motor['current_y']
                        # Go to waiting state
                        self.case = 1
                        self.old_case = 1
                        print 'Go to waiting state 1'
                        # Reset counters
                        self.j = 0
                        self.i = 0
                        self.angle = 0
                    elif self.j == 5:
                        # Reset counter 
                        self.j = 0
                        # Increase line counter
                        self.i = self.i + 1
                        # Go to waiting state
                        self.case = 1
                        self.old_case = 10
                        print 'Go to waiting state 1'
                        # if cross was made terminate the movement
                        if self.i == 8:
                            # go to best point
                            self.wanted_x = self.best_x
                            self.wanted_y = self.best_y
                            self.i = 0
                            # go to waiting state
                            self.case = 1
                            self.old_case = 1
                        # If best position is at the end of the line
                        elif sfp['rx_power_db'] == self.best_rx:
                            # Reset line counter and continue in same direction
                            self.i = 0
                            # Calculate next point
                            self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step
                            self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step
                        # else
                        else:
                            # update angle
                            self.angle = self.angle + math.pi / 2 # Rotate for 90
                            # go to best point 
                            self.wanted_x = self.best_x
                            self.wanted_y = self.best_y
                    # if the line scan is not completed yet
                    else:
                        # Calculate next point
                        self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step
                        self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step


                    # Request the motor to move to the next point.
                    bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                    self.j = self.j + 1 # Increase point count

        elif self.state == 'idle':
            pass
        

Alignment().start()

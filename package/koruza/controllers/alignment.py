#!/usr/bin/env python
from __future__ import division
import koruza
import math
import time

class Alignment(koruza.Application):
    # This is the application identifier so that messages may be directed to
    # this specific application on the bus.
    application_id = 'alignment'
    needs_remote = True # Should be true if the application would like to access the remote unit.
    state = 'idle' # Current state of application.
    initial_position = None     # Initial position.

    # VARIABLES

    # Counters
    i = 0 # Line counter
    j = 0 # Points counter
    k = 0 # counter - sending, receiving request, synchronising units.
    l = 0 # Line counter
    a = 0 # Angle counter for angle reset
    s = 0 # Counter for extra alignment steps

    # STEP values are recalculated when distance information is obtained
    step = 100  # Step for scanning, can be updated from GUI when in idle state (recalculated)
    step_spiral = 100  # Step for spiral scan, can be larger than normal scan (recalculated)
    step_distance = 3  # Desired step in mm on the unit
    step_distance_spiral = 5  # Desired step in mm on the unit using spiral scann
    step_single = 0.01  # Single step-move in mm (recalculated)
    d = 10  # distance between units in m - updated from the unit

    n_points = 2  # Initial number of points in a spiral scan
    l_points = 5  # Initial number of points in line
    angle = 0  # Angle of lines

    # READINGS
    sfp_reading = 0 # Combined sfp power from both units based on distance and scaling coefficients
    sfp_reading_self = 0 # Sfp power reading just for the unit
    sfp_reading_remote = 0 #Sfp power reading for remote unit
    sfp_avg = 0 # Average power for monitoring in idle state

    k1 = 0.5 # Scalin coefficient local (recalculated based on distance)
    k2 = 0.5 # Scaling coefficient remote (recalculated, based on distance)

    min_threshold = -5  # Threshold for minimal signal recived to go from spiral scan to line scan
    max_threshold = 25  # Stopping condition combined measurement
    max_threshold_self = 25 # Stopping condition self unit measuremnent
    max_threshold_remote = 25 # Stopping condition remote unit measuremnent

    # Best position - combined
    best_x = 0
    best_y = 0
    best_rx = 0
    # Next wanted position
    wanted_x = 0
    wanted_y = 0
    # Start position in spiral scann
    start_x = 0
    start_y = 0

    # Initial limits for range of motion - updated from the units
    lim_min_x = 0
    lim_min_y = 0
    lim_max_x = 35000
    lim_max_y = 35000

    # ALGORITHM CASES and SYNCHRONISING
    case = 0  # Current state case of the system
    remote_case = 0 # State of remote unit
    old_case = 0  # Save previous state
    moving = 0 # Moving variable - is unit at rest (0) or moving (1)
    remote_moving = 0 # Moving variable from remote unit
    req_counter = 0 # Request counter (recieved)
    rec_counter = 0 # Response counter (recieved)
    counter = 0 # Last send counter

    # TIME
    time = 0 # Real time
    wait_time = 0 # Waiting time
    start_time = 0 # Algorithm running time - start time
    max_time = 1800 # Max time before algorithm timeout
    con_timeout = 0 # Connection timeout
    print_time = 0 # printing time

    restart = 0 # Restart spiral scann

    def on_command(self, bus, command, state, remote_state):
        if command['command'] == 'start' and self.state == 'idle':
            self.state = 'setup'
            self.initial_position = state.get('motors', {}).get('motor')

            # Update distance between units
            self.d = self.config.get('distance', 10)
            print 'Distance: %f' % self.d

            # Calculate steps depending on a distance
            self.step_single = (1/1100)*self.d  # single step in mm on other unit
            self.step = self.step_distance/self.step_single  # calculate number of steps in single move
            self.step = int(round(self.step))
            # Calculate step used in spiral scan
            self.step_spiral = self.step_distance_spiral/self.step_single  # calculate number of steps in single move
            self.step_spiral = int(round(self.step_spiral))

            # Calculate scaling coefficients based on a distance
            if self.d > 100:
                self.k1 = 0.2
                self.k2 = 0.8
            else:
                self.k1 = 0.9 - (self.d*0.7)/100
                self.k2 = 1 - self.k1

            # Get variables from the command that was sent on the bus.
            self.min_threshold = command.get('min_threshold', -5)
            self.max_threshold = command.get('max_threshold', 25)
            self.max_threshold_self = self.max_threshold
            self.max_threshold_remote = self.max_threshold

            # Initialize variables.
            # COUNTERS
            self.i = 0
            self.j = 0
            self.k = 0
            self.l = 0
            self.a = 0
            self.s = 0

            self.n_points = 2  # points in spiral scan
            self.l_points = 5  # nr. of points in a line
            self.angle = 0  # angle

            self.best_x = 0
            self.best_y = 0
            self.best_rx = 0
            self.start_x = 0
            self.start_y = 0
            self.wanted_x = 0
            self.wanted_y = 0

            self.case = 0
            self.remote_case = 0
            self.old_case = 0
            self.moving = 0
            self.remote_moving = 0
            self.rec_counter = 0
            self.req_counter = 0
            self.counter = 1

            self.time = time.time()
            self.wait_time = time.time()
            self.start_time = time.time()
            self.max_time = 1800
            self.con_timeout = 0
            self.print_time = time.time()
            self.restart = 0

            print 'Got start command step=%d step-spiral=%d threshold min=%d threshold max=%d scaling local= %f scaling remote= %f' % (self.step, self.step_spiral, self.min_threshold, self.max_threshold, self.k1, self.k2)
        elif command['command'] == 'stop' and self.state == 'go':
            print 'Got stop command.'
            self.state = 'idle'

    def on_idle(self, bus, state, remote_state):
        if self.state == 'setup':
            print 'Got to setup state.'
            if not state.get('sfp') or not state.get('motors'):
                # Do nothing until we have known last state from SFP and motor drivers.
                return
            # Get last known state for the first SFP module.
            sfp = state['sfp']['sfp'].values()[0]
            # Get last known motor driver state.
            motor = state['motors']['motor']

            # Set first wanted position as current
            self.wanted_x = motor['current_x']
            self.wanted_y = motor['current_y']
            # Set best position as current
            self.best_x = motor['current_x']
            self.best_y = motor['current_y']
            self.best_rx = sfp['rx_power_db']
            self.sfp_reading = sfp['rx_power_db']
            self.sfp_reading_self = sfp['rx_power_db']
            self.con_timeout = time.time() # Start time for connection timeout
            self.state = 'go'

        elif self.state == 'go':
            if not state.get('sfp') or not state.get('motors') or not remote_state.get('motors') or not remote_state.get('sfp'):
                # Do nothing until we have known last state from SFP and motor drivers.
                print 'ERROR: No connection!'

            else:
                # Get last known state for the first SFP module.
                sfp = state['sfp']['sfp'].values()[0]
                sfp_remote = remote_state['sfp']['sfp'].values()[0]
                # Get last known motor driver state.
                motor = state['motors']['motor']
                motor_remote = remote_state['motors']['motor']

                # Error loop - catch error when unit stops moving, resend request or change desired position
                if not motor['next_x'] == self.wanted_x or not motor['next_y'] == self.wanted_y:
                    print 'ERROR: Next and wanted position doesnt match.'
                    print 'READING: C: %d, RC: %d, X: %d, nX: %d, wX: %d, Y: %d, nY: %d, wY: %d, SFP: %f' % (self.case, self.remote_case, motor['current_x'], motor['next_x'], self.wanted_x, motor['current_y'], motor['next_y'], self.wanted_y, self.sfp_reading)
                    bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)

                if time.time() - self.print_time > 10:
                    self.print_time = time.time()
                    if not motor['current_x'] == self.wanted_x or not motor['current_y'] == self.wanted_y:
                        print 'ERROR: Current and wanted position doesnt match.'
                        print 'READING: C: %d, RC: %d, X: %d, nX: %d, wX: %d, Y: %d, nY: %d, wY: %d, SFP: %f' % (self.case, self.remote_case, motor['current_x'], motor['next_x'], self.wanted_x, motor['current_y'], motor['next_y'], self.wanted_y, self.sfp_reading)
                        self.wanted_x =  motor['current_x']
                        self.wanted_y = motor['current_y']

                 # CASES - Enter when requested position is reached
                if motor['current_x'] == self.wanted_x and motor['current_y'] == self.wanted_y:

                    # UPDATE DATA FROM REMOTE UNIT: Read status from remote unit, case, moving
                    if not remote_state.get('app_status', {}).get('moving') == None and not remote_state.get('app_status', {}).get('moving') == None:
                        self.remote_case = remote_state['app_status']['case']
                        self.remote_moving = remote_state['app_status']['moving']
                    else:
                        self.remote_case = 0
                        self.remote_moving = 0

                    # Update request status
                    if not remote_state.get('app_status', {}).get('req_counter') == None:
                        self.req_counter = remote_state['app_status']['req_counter']
                    else:
                        self.req_counter = 0

                    # Update recieved status
                    if not remote_state.get('app_status', {}).get('rec_counter') == None:
                        self.rec_counter = remote_state['app_status']['rec_counter']
                    else:
                        self.rec_counter = 0

                    # UPDATE SFP READING
                    self.sfp_reading = self.k1*sfp['rx_power_db'] + self.k2*sfp_remote['rx_power_db']
                    self.sfp_reading_self = sfp['rx_power_db']
                    self.sfp_reading_remote = sfp_remote['rx_power_db']
                    # Re-calculate step size based on power value
                    self.step_distance = 5 -(self.sfp_reading/30)*3
                    self.step = self.step_distance/self.step_single  # calculate number of steps in single move
                    self.step = int(round(self.step))

                    self.k = self.k + 1 # Update loop counter

                    if self.moving == 1 or time.time() - self.print_time > 1:
                        print 'READING: C: %d, RC: %d, X: %d, nX: %d, wX: %d, Y: %d, nY: %d, wY: %d, SFP: %f' % (self.case, self.remote_case, motor['current_x'], motor['next_x'], self.wanted_x, motor['current_y'], motor['next_y'], self.wanted_y, self.sfp_reading)
                        self.print_time = time.time() #Reset printing time

                    # Check if running time exceeded max time - go to hibernation state
                    if self.start_time - time.time() > self.max_time:
                        # Go trough waiting state 100
                        self.case = 100
                        self.old_case = 4
                        # Set wanted position to last best position
                        self.wanted_x = self.best_x
                        self.wanted_y = self.best_y
                        # Request the motor to move to the next point.
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                        # Restart starting time
                        self.start_time = time.time()
                        # Reset stop time
                        self.max_time = 1800
                        print 'Alignment timeout. Go to hibernation state.'

                    # STATES

                    # STATE 0: Initialisation state
                    if self.case == 0:
                        # Update moving state
                        self.moving = 0
                        # initialise current position to best position
                        self.best_x = motor['current_x']
                        self.best_y = motor['current_y']
                        self.best_rx = self.sfp_reading
                        self.start_x = motor['current_x']
                        self.start_y = motor['current_y']

                        # set angle and counters to 0
                        self.angle = 0
                        self.i = 0
                        self.j = 0
                        self.a = 0

                        if self.sfp_reading < self.min_threshold:
                            # If no signal is received go to spiral scan
                            self.old_case = 10

                        else:
                            # If some signal is received go to line scan
                            self.old_case = 20

                        # Wait in initialisation state for a few moments
                        if time.time() - self.wait_time > 3:
                            self.case = 1 # Go to request movment state
                            self.wait_time = time.time()

                    # STATE 1: Request movement state
                    elif self.case == 1:
                        # Update current state
                        self.moving = 0

                        # if remote unit isn't moving, send request to start moving
                        if self.remote_moving == 0:
                            # If next state is known
                            if not self.old_case == 1 or not self.old_case == 0:
                                # Send request counter k
                                self.publish({'req_counter': self.k})
                                self.counter = self.k # Remember requested counter
                                # Proceed to wait in the response state
                                self.case = 2
                                self.wait_time = time.time() # Reset waiting time

                            # If next state is not known, reevaluate current signal and move
                            elif self.sfp_reading < self.max_threshold or self.sfp_reading_self < self.max_threshold_self or self.sfp_reading_remote < self.max_threshold_remote:
                                self.old_case = 20 # Go to line scan
                                # Send request counter k
                                self.publish({'req_counter': self.k})
                                self.counter = self.k # Remember requested counter
                                # Proceed to wait for response state
                                self.case = 2
                                self.wait_time = time.time() # Reset waiting time

                    # STATE 2: Wait for response, wait for request
                    elif self.case == 2:
                        if self.remote_moving == 0:
                            # If request was received, send response in case counter is greater than last sent counter
                            if self.req_counter > self.counter:
                                self.k = self.req_counter # Update your counter
                                self.publish({'rec_counter': self.k})
                                # go to waiting state
                                self.case = 3
                                self.wait_time = time.time() # Reset waiting time

                            # Check if requested counter was returned
                            elif self.rec_counter == self.counter:
                                # Start moving
                                self.case = self.old_case
                                self.moving = 1

                            # Stop waiting for other unit if enough time has passed
                            elif time.time() - self.wait_time > 3:
                                # Start moving
                                self.case = self.old_case
                                self.moving = 1

                            else:
                                print 'No condition met, Counter: %d, REQ: %d, REC: %d, Wait time: %f' % (self.counter, self.req_counter, self.rec_counter, time.time() - self.wait_time)

                        # If remote unit starts moving go to waiting state
                        else:
                            self.case = 3
                            self.wait_time = time.time() # Reset waiting time

                    # STATE 3: Waiting state - wait for other unit to start moving
                    elif self.case == 3:
                        # Wait for other unit to start moving
                        if self.remote_moving == 1:
                            self.case = 1 # Go to sending request state
                        # if other unit doesn't start moving after 5s, resend request
                        elif time.time() - self.wait_time > 5:
                            self.case = 1

                    # STATE 4: Hibernation state - setup
                    elif self.case == 4:
                        self.moving = 0

                        #Reset all variables
                        self.i = 1
                        self.j = 0
                        self.angle = 0
                        self.a = 0
                        self.best_x = motor['current_x']
                        self.best_y = motor['current_y']
                        self.best_rx = self.sfp_reading # Starting sfp for freference
                        self.sfp_avg = self.sfp_reading # reset average reading
                        self.wait_time = time.time() # Reset waiting time
                        self.start_time = time.time() # Reset starting time
                        self.case = 5
                        self.old_case = 5

                    # STATE 5: HIBERNATION STATE
                    elif self.case == 5:
                        self.moving = 0

                        # If request was received, send response in case counter is greater than last sent counter
                        if self.req_counter > self.counter:
                            self.k = self.req_counter # Update your counter
                            self.counter = self.req_counter # Update your counter
                            self.publish({'rec_counter': self.k})

                        # Monitor movement:
                        # Every 0.5 second take reading
                        if time.time() - self.wait_time > 0.5:
                            self.wait_time = time.time() # Reset waiting time
                            self.sfp_avg = self.sfp_avg + self.sfp_reading # Update average value
                            self.i += 1 # increase counter
                        # Every minute re-calculate average
                        if self.i == 100:
                            self.i = 1 # Reset counter
                            self.sfp_avg = self.sfp_avg/100 # Calculate average
                            print 'New average average: %f' %self.sfp_avg

                            # Check if average has drop
                            if self.best_rx - self.sfp_avg > 2:
                                # Restart algorithm - go to line scan
                                self.case = 1
                                self.old_case = 20
                                self.max_time = 1800 # Set timeout to 30 min
                                self.start_time = time.time() # restart starting time

                        # If enough time has passed from hibernation, and KORUZA doesn't have sufiicient power, try again
                        if time.time()-self.start_time > self.max_time and self.sfp_avg < self.max_threshold:
                            self.i = 0 # Reset counter
                            self.sfp_avg = self.sfp_reading
                            self.case = 1
                            self.old_case = 20
                            self.max_time = 1800 # Set timeout to 30 min
                            self.start_time = time.time() # restart starting time
                            print 'Re-align!'

                    # STATE 10: SPIRAL SCAN PREPARATION
                    elif self.case == 10:
                        self.moving = 1

                        self.best_x = motor['current_x']
                        self.best_y = motor['current_y']
                        self.best_rx = self.sfp_reading

                        # Move to starting position
                        self.wanted_x = self.start_x
                        self.wanted_y = self.start_y
                        # Request the motor to move to the next point.
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)

                        # Go to spiral scann
                        self.case = 11
                        self.old_case = 11
                        self.angle = 0

                        # reset number of points
                        self.n_points = 2  # points in spiral scan

                    # STATE 11: SPIRAL SCAN
                    elif self.case == 11:
                        self.moving = 1
                        # Calculate next points
                        self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step_spiral
                        self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step_spiral

                        # Check if desired movement is in the allowed range
                        if self.wanted_x < self.lim_min_x:
                            self.wanted_x = self.lim_min_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_x > self.lim_max_x:
                            self.wanted_x = self.lim_max_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_y < self.lim_min_y:
                            self.wanted_y = self.lim_min_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_y > self.lim_max_y:
                            self.wanted_y = self.lim_max_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count

                        # Request the motor to move to the next point.
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                        self.j += 1 # Increase point count


                        # Check if better position was achieved - update values
                        if self.sfp_reading > self.best_rx:
                            self.best_x = motor['current_x']
                            self.best_y = motor['current_y']
                            self.best_rx = self.sfp_reading

                        # Check if line is finished
                        if self.j == self.n_points:
                            self.j = 0 # Reset point count
                            self.angle += math.pi / 2 # Rotate for 90
                            self.i += 1 # Increase line count

                        # Check if two lines are scanned
                        if self.i == 2:
                            self.i = 0 # Reset line count
                            self.a += 2 # Increase angle count
                            # If other unit is performing spiral scan increase number of points, otherwise not
                            self.n_points += 5 # Increase nr. of points per line

                        # Check if the whole circle was scanned, reset angle
                        if self.a == 4:
                            self.a = 0 # Reset angle counter
                            self.angle = 0 # Reset angle
                            self.l += 1  # Increase circle counter

                        # Check if 5 circles were made
                        if self.l >= 6:
                            self.l = 0
                            # Go to start position and wait for other unit
                            self.wanted_x = self.start_x
                            self.wanted_y = self.start_y
                            bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                            print 'No power detected, let other unit scan.'
                            # Wait for other unit to repeat
                            self.old_case = 10
                            self.case = 100

                        # Check if some signal was detected and terminate the movement
                        # Combined reading - go to line scan:
                        if self.sfp_reading > self.min_threshold:
                            # Go to line scan
                            self.old_case = 20
                            # Go to waiting state
                            self.case = 100
                            # Reset counters
                            self.j = 0
                            self.i = 0
                            self.angle = 0
                            self.a = 0
                            self.l = 0

                        self.wait_time = time.time() # reset waiting counter

                    # STATE 20: LINE SCAN
                    elif self.case == 20:
                        # Publish current moving state
                        self.moving = 1
                        # If starting new line make starting point best position
                        # Check if better position was achieved - update values
                        if self.sfp_reading > self.best_rx or self.j == 0:
                            self.best_x = motor['current_x']
                            self.best_y = motor['current_y']
                            self.best_rx = self.sfp_reading

                        # Check if enough signal was found
                        if self.sfp_reading > self.max_threshold and self.sfp_reading_self > self.max_threshold_self and self.sfp_reading_remote > self.max_threshold_remote:
                            print "Done!"
                            # Stay at the current point
                            self.wanted_x = motor['current_x']
                            self.wanted_y = motor['current_y']
                            # Go to waiting state
                            self.case = 100
                            self.old_case = 4
                            # Reset counters
                            self.j = 0
                            self.i = 0
                            self.angle = 0
                            self.s = 0

                        # Check if line has been scanned
                        elif self.j == self.l_points:
                            # Reset counter
                            self.j = 0
                            # Increase line counter
                            self.i = self.i + 1
                            # Go to waiting state
                            self.case = 100
                            self.old_case = 20

                            # If 16 lines were scanned go to the square scan state
                            if self.i >= 16 and self.s == 0:
                                # go to best point
                                self.wanted_x = self.best_x
                                self.wanted_y = self.best_y
                                self.i = 0
                                self.j = 5
                                # go to square scan
                                self.case = 100
                                self.old_case = 22
                                # Reset angle
                                self.angle = 0

                            # If best position is at the end of the line
                            elif self.sfp_reading >= self.best_rx:
                                # Reset line counter and continue in same direction
                                self.i = 0
                                self.l_points = 5 # reset number of points in a line
                                # Calculate next point
                                self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step
                                self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step

                            # If line is scanned go to the best position on the line
                            else:
                                # update angle
                                self.angle += math.pi / 2 # Rotate for 90
                                # go to best point
                                self.wanted_x = self.best_x
                                self.wanted_y = self.best_y

                        # if the line scan is not completed yet
                        else:
                            # Calculate next point on the line
                            self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step
                            self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step


                        # Check if desired movement is in the range
                        if self.wanted_x < self.lim_min_x:
                            self.wanted_x = self.lim_min_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                            self.angle += math.pi / 2 # Rotate for 90
                        elif self.wanted_x > self.lim_max_x:
                            self.wanted_x = self.lim_max_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                            self.angle += math.pi / 2 # Rotate for 90
                        elif self.wanted_y < self.lim_min_y:
                            self.wanted_y = self.lim_min_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                            self.angle += math.pi / 2 # Rotate for 90
                        elif self.wanted_y > self.lim_max_y:
                            self.wanted_y = self.lim_max_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                            self.angle += math.pi / 2 # Rotate for 90

                        # Request the motor to move to the next point.
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                        self.j = self.j + 1 # Increase point count
                        self.wait_time = time.time() # reset waiting counter

                    # STATE 22: Square scan state
                    elif self.case == 22:
                        # Publish current moving state
                        self.moving = 1
                        # Calculate next points
                        self.wanted_x = motor['current_x'] + math.cos(self.angle) * self.step_spiral
                        self.wanted_y = motor['current_y'] + math.sin(self.angle) * self.step_spiral

                        # Check if desired movement is in the range
                        if self.wanted_x < self.lim_min_x:
                            self.wanted_x = self.lim_min_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_x > self.lim_max_x:
                            self.wanted_x = self.lim_max_x
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_y < self.lim_min_y:
                            self.wanted_y = self.lim_min_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count
                        elif self.wanted_y > self.lim_max_y:
                            self.wanted_y = self.lim_max_y
                            self.j = 0  # Go to next line
                            self.i = self.i + 1  # Increase line count

                        # Request the motor to move to the next point.
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                        self.j = self.j + 1 # Increase point count

                        # Check if better position was achieved - update values
                        if self.sfp_reading > self.best_rx:
                            self.best_x = motor['current_x']
                            self.best_y = motor['current_y']
                            self.best_rx = self.sfp_reading

                        # Check if line is finished
                        if self.j == self.l_points*2:
                            self.j = 0 # Reset point count
                            self.angle += math.pi / 2 # Rotate for 90
                            self.i += 1 # Increase line count

                        # Check if square is scanned
                        if self.i == 5:
                            self.i = 0 # Reset line count
                            self.j = 0
                            self.angle = 0

                            # Go to best position in next state
                            self.old_case = 23
                            self.case = 23

                    # STATE 23: Go to best position
                    elif self.case == 23:
                        # Publish current moving state
                        self.moving = 1
                        # Request the motor to move to the next point.
                        self.wanted_x = self.best_x
                        self.wanted_y = self.best_y
                        bus.command('motor_move', next_x = self.wanted_x, next_y = self.wanted_y)
                        #print 'Moved to best position'
                        self.case = 100
                        self.old_case = 20
                        self.wait_time = time.time() # reset waiting counter

                    # STATE 100: Waiting state - Wait for data to be send
                    elif self.case == 100:
                        # Publish current state
                        self.moving = 0

                        if time.time() - self.wait_time > 1:
                            self.case = 1
                            self.wait_time = time.time()

                    # Publish status every 0.2 seconds
                    if time.time() - self.time > 0.3:
                        self.time = time.time()
                        self.publish({'case': self.case})
                        self.publish({'moving': self.moving})

        elif self.state == 'idle':
            pass


Alignment().start()





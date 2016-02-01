#!/usr/bin/env python
from __future__ import division
import koruza
import math
import time

class Test(koruza.Application):
    # This is the application identifier so that messages may be directed to
    # this specific application on the bus.
    application_id = 'test'
    # Should be true if the application would like to access the remote unit.
    needs_remote = True
    
    # Current state.
    state = 'idle'
    # Initial position.
    initial_position = None
    # Other variables
    # Counters
    i = 0

    case = 0  # Current state case of the system

    def on_command(self, bus, command, state, remote_state):
        if command['command'] == 'start' and self.state == 'idle':
            self.state = 'setup'
            self.initial_position = state.get('motors', {}).get('motor')


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

            self.state = 'go'

        elif self.state == 'go':

            self.case = self.case + 1
            self.i = self.i+1
            self.publish({'case': self.i})

            if not remote_state.get('app_status', {}).get('case') == None:
                print 'My: %d Remote: %d' % (self.case, remote_state.get('app_status', {}).get('case'))
            else:
                print 'My: %d Remote: None' % (self.case)

            #time.sleep(1)




        elif self.state == 'idle':
            pass
        

Test().start()

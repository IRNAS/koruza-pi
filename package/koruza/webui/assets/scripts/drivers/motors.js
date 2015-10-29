import React from 'react';
import Avatar from 'material-ui/lib/avatar';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import LinearProgress from 'material-ui/lib/linear-progress';
import Toggle from 'material-ui/lib/toggle';
import Snackbar from 'material-ui/lib/snackbar';

import _ from 'underscore';

class MotorController extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            next_x: this.props.readings.next_x,
            next_y: this.props.readings.next_y,
            next_f: this.props.readings.next_f
        }

        this._onControlEnabledToggled = this._onControlEnabledToggled.bind(this);
        this._onKeydown = this._onKeydown.bind(this);
        this._requestMove = _.throttle(this._requestMove.bind(this), 100);
    }

    _onControlEnabledToggled(event, toggled) {
        if (toggled) {
            this.refs.snackbar.show();
        } else {
            this.refs.snackbar.dismiss();
        }
    }

    _onKeydown(event) {
        let keymap = {
            65: (state) => { state.next_x--; },
            68: (state) => { state.next_x++; },
            83: (state) => { state.next_y--; },
            87: (state) => { state.next_y++; },
        }
        if (!keymap[event.keyCode])
            return;

        let state = _.clone(this.state);
        keymap[event.keyCode](state);

        this.setState(state);
        this._requestMove();
    }

    _requestMove() {
        let bus = this.props.bus;
        bus.command('motor_move', {
            next_x: this.state.next_x,
            next_y: this.state.next_y,
            next_f: this.state.next_f,
        });
    }

    componentDidMount() {
        window.addEventListener('keydown', this._onKeydown);
    }

    componentWillUnmount() {
        window.removeEventListener('keydown', this._onKeydown);
    }

    render() {
        let styles = {
            controller: {
                width: '300px',
            },
            snackbar: {
                zIndex: 20,
            }
        }

        return (
            <div style={styles.controller}>
                <Snackbar
                    ref="snackbar"
                    message="Keyboard motor control is enabled."
                    style={styles.snackbar}
                />

                <Toggle
                    ref="controlEnabled"
                    label="Enable keyboard motor control"
                    onToggle={this._onControlEnabledToggled}
                />
            </div>
        )
    }
}

export default class StatusMotors extends React.Component {
    constructor() {
        super();

        this.state = {
            // Motor metadata.
            metadata: {},
            // Motor readings.
            readings: {},
        }
    }

    componentWillMount() {
        let bus = this.props.bus;
        // TODO: If there are no readings for some time, clear state.
        this._subscription = bus.subscribe('status', ['motors'], _.throttle((message) => {
            this.setState({
                metadata: message.metadata,
                readings: message.motor,
            });
        }, 300));
    }

    componentWillUnmount() {
        this._subscription.stop();
    }

    render() {
        let readings, controller;
        if (_.isEmpty(this.state.readings)) {
            readings = (
                <div>
                    Waiting for readings from the motor driver…
                    <br/><br/>
                    <LinearProgress mode="indeterminate"  />
                </div>
            )
        } else {
            readings = (
                <div>
                    Current position: X: {this.state.readings.current_x}, Y: {this.state.readings.current_y}, F: {this.state.readings.current_f}<br/>
                    Requested position: X: {this.state.readings.next_x}, Y: {this.state.readings.next_y}, F: {this.state.readings.next_f}<br/>
                </div>
            )

            controller = <MotorController bus={this.props.bus} readings={this.state.readings} />
        }

        return (
            <Card initiallyExpanded={true}>
                <CardHeader
                    title="Motor status"
                    subtitle="Status of motors as reported by the motor driver"
                    avatar={<Avatar>M</Avatar>}
                    actAsExpander={true}
                    showExpandableButton={true}
                />

                <CardText expandable={true}>
                    {readings}
                    {controller}
                </CardText>
            </Card>
        )
    }
}

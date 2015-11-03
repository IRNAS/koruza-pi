import React from 'react';
import Avatar from 'material-ui/lib/avatar';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import LinearProgress from 'material-ui/lib/linear-progress';
import Toggle from 'material-ui/lib/toggle';
import Snackbar from 'material-ui/lib/snackbar';
import Slider from 'material-ui/lib/slider';
import RaisedButton from 'material-ui/lib/raised-button';
import TextField from 'material-ui/lib/text-field';

import _ from 'underscore';

import 'flexboxgrid';

class MotorController extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            controlEnabled: false,
            steps: 1,
            nextX: this.props.readings.next_x,
            nextY: this.props.readings.next_y,
            nextF: this.props.readings.next_f,
            nextState: null
        }

        this._onControlEnabledToggled = this._onControlEnabledToggled.bind(this);
        this._onGreenLaserToggled = this._onGreenLaserToggled.bind(this);
        this._onKeydown = this._onKeydown.bind(this);
        this._onKeyup = this._onKeyup.bind(this);
        this._onHomeXClicked = this._onHomeXClicked.bind(this);
        this._onHomeYClicked = this._onHomeYClicked.bind(this);
        this._onStopClicked = this._onStopClicked.bind(this);
        this._onStartScanClicked = this._onStartScanClicked.bind(this);
        this._onStopScanClicked = this._onStopScanClicked.bind(this);
    }

    _onControlEnabledToggled(event, toggled) {
        if (toggled) {
            this.refs.snackbarMotorControl.show();
        } else {
            this.refs.snackbarMotorControl.dismiss();
        }

        this.setState({controlEnabled: toggled});
    }

    _onGreenLaserToggled(event, toggled) {
        this.props.bus.command('motor_configure', {laser: toggled});
    }

    _onKeydown(event) {
        if (!this.state.controlEnabled)
            return;

        let steps = this.refs.steps.getValue();
        let keymap = {
            // A.
            65: (state) => { state.nextX = Math.max(0, state.nextX - steps); },
            // D.
            68: (state) => { state.nextX = Math.min(70000, state.nextX + steps); },
            // S.
            83: (state) => { state.nextY = Math.max(0, state.nextY - steps); },
            // W.
            87: (state) => { state.nextY = Math.min(70000, state.nextY + steps); },
            // V.
            86: (state) => { state.nextF = Math.max(0, state.nextF - steps); },
            // F.
            70: (state) => { state.nextF = Math.min(20000, state.nextF + steps); },
        }
        if (!keymap[event.keyCode])
            return;

        let nextState;
        if (!this.state.nextState)
            nextState = _.pick(this.state, 'nextX', 'nextY', 'nextF');
        else
            nextState = this.state.nextState;

        keymap[event.keyCode](nextState);
        this.setState({nextState: nextState});
    }

    _onKeyup(event) {
        if (!this.state.controlEnabled || !this.state.nextState)
            return;

        let nextState = this.state.nextState;
        this.setState({
            nextX: nextState.nextX,
            nextY: nextState.nextY,
            nextF: nextState.nextF,
            nextState: null
        });

        this.props.bus.command('motor_move', {
            next_x: nextState.nextX,
            next_y: nextState.nextY,
            next_f: nextState.nextF,
        });
    }

    _onHomeXClicked() {
        this.props.bus.command('motor_configure', {'motor_command': 2});
        this.refs.snackbarHomeX.show();
        this.setState({nextX: 0});
    }

    _onHomeYClicked() {
        this.props.bus.command('motor_configure', {'motor_command': 3});
        this.refs.snackbarHomeY.show();
        this.setState({nextY: 0});
    }

    _onStopClicked() {
        this.props.bus.command('motor_configure', {'motor_command': 1});
        this.refs.snackbarStop.show();
    }

    _onStartScanClicked() {
        let steps = parseInt(this.refs.scanSteps.getValue());
        let threshold = parseInt(this.refs.scanThreshold.getValue());
        if (isNaN(steps) || isNaN(threshold))
            return;

        this.props.bus.command('call_application', {
            'application_id': 'spiral_scan',
            'payload': {
                'type': 'command',
                'command': 'start',
                'step': steps,
                'threshold': threshold,
            }
        });
        this.refs.snackbarStartScan.show();
    }

    _onStopScanClicked() {
        this.props.bus.command('call_application', {
            'application_id': 'spiral_scan',
            'payload': {
                'type': 'command',
                'command': 'stop',
            }
        });
        this.refs.snackbarStopScan.show();
    }

    componentDidMount() {
        window.addEventListener('keydown', this._onKeydown);
        window.addEventListener('keyup', this._onKeyup);
    }

    componentWillUnmount() {
        window.removeEventListener('keydown', this._onKeydown);
        window.removeEventListener('keyup', this._onKeyup);
    }

    componentWillReceiveProps(props) {
        this.setState({
            nextX: props.readings.next_x,
            nextY: props.readings.next_y,
            nextF: props.readings.next_f
        });
    }

    render() {
        let styles = {
            snackbar: {
                zIndex: 20,
            }
        }

        let nextPosition;
        if (this.state.nextState) {
            nextPosition = (
                <div>
                    Release key to set position to:<br/>
                    X: {this.state.nextState.nextX}, Y: {this.state.nextState.nextY}, F: {this.state.nextState.nextF}
                </div>
            );
        }

        return (
            <div>
                <Snackbar
                    ref="snackbarMotorControl"
                    message="Keyboard motor control is enabled."
                    style={styles.snackbar}
                />

                <Snackbar
                    ref="snackbarHomeX"
                    message="Requested homing on X axis."
                    autoHideDuration={1000}
                    style={styles.snackbar}
                />

                <Snackbar
                    ref="snackbarHomeY"
                    message="Requested homing on Y axis."
                    autoHideDuration={1000}
                    style={styles.snackbar}
                />

                <Snackbar
                    ref="snackbarStop"
                    message="Requested to stop all motion."
                    autoHideDuration={1000}
                    style={styles.snackbar}
                />

                <Snackbar
                    ref="snackbarStartScan"
                    message="Requested to start scan."
                    autoHideDuration={1000}
                    style={styles.snackbar}
                />

                <Snackbar
                    ref="snackbarStopScan"
                    message="Requested to stop scan."
                    autoHideDuration={1000}
                    style={styles.snackbar}
                />

                <div className="row">
                    <div className="col-md-6">
                        <Toggle
                            ref="controlEnabled"
                            label="Keyboard motor control enabled"
                            onToggle={this._onControlEnabledToggled}
                        />
                        <br/>

                        Number of steps:
                        <Slider
                            name="steps"
                            ref="steps"
                            min={1}
                            max={300}
                            step={1}
                            defaultValue={1}
                            disabled={!this.state.controlEnabled}
                        />

                        {nextPosition}
                    </div>

                    <div className="col-md-6">
                        <Toggle
                            label="Green laser enabled"
                            onToggle={this._onGreenLaserToggled}
                            defaultToggled={this.props.readings.laser == 1}
                        />
                        <br/>

                        <RaisedButton
                            label="Home X"
                            onTouchTap={this._onHomeXClicked}
                        />
                        &nbsp;
                        <RaisedButton
                            label="Home Y"
                            onTouchTap={this._onHomeYClicked}
                        />
                        &nbsp;
                        <RaisedButton
                            label="Stop"
                            onTouchTap={this._onStopClicked}
                        />
                        <br/><br/>

                        <TextField
                            ref="scanSteps"
                            floatingLabelText="Scan steps"
                            defaultValue={100}
                        />
                        <TextField
                            ref="scanThreshold"
                            floatingLabelText="Scan threshold"
                            defaultValue={10}
                        />
                        <br/><br/>

                        <RaisedButton
                            label="Start scan"
                            onTouchTap={this._onStartScanClicked}
                        />
                        &nbsp;
                        <RaisedButton
                            label="Stop scan"
                            onTouchTap={this._onStopScanClicked}
                        />
                    </div>
                </div>
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
                    <br/>
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

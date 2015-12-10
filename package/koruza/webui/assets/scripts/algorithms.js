import React from 'react';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import Avatar from 'material-ui/lib/avatar';
import Snackbar from 'material-ui/lib/snackbar';
import RaisedButton from 'material-ui/lib/raised-button';
import TextField from 'material-ui/lib/text-field';

import _ from 'underscore';

import Bus from './bus';

export default class Algorithms extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            // Authentication status.
            authenticated: Bus.isAuthenticated(),
        }

        this._onAuthenticated = this._onAuthenticated.bind(this);
        this._onStartScanClicked = this._onStartScanClicked.bind(this);
        this._onStopScanClicked = this._onStopScanClicked.bind(this);
    }

    componentWillMount() {
        Bus.addAuthenticationListener(this._onAuthenticated);
    }

    componentWillUnmount() {
        Bus.removeAuthenticationListener(this._onAuthenticated);
    }

    _onAuthenticated() {
        this.setState({
            authenticated: Bus.isAuthenticated()
        });
    }

    _onStartScanClicked() {
        let steps = parseInt(this.refs.scanSteps.getValue());
        let threshold = parseInt(this.refs.scanThreshold.getValue());
        if (isNaN(steps) || isNaN(threshold))
            return;

        Bus.command('call_application', {
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
        Bus.command('call_application', {
            'application_id': 'spiral_scan',
            'payload': {
                'type': 'command',
                'command': 'stop',
            }
        });
        this.refs.snackbarStopScan.show();
    }

    render() {
        let styles = {
            snackbar: {
                zIndex: 20,
            }
        }

        if (!this.state.authenticated) {
            return (
                <div></div>
            )
        }

        return (
            <Card>
                <CardHeader
                    title="Algorithms"
                    subtitle="Supported algorithms"
                    avatar={<Avatar>A</Avatar>}
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

                <CardText>
                    <TextField
                        ref="scanSteps"
                        floatingLabelText="Scan steps"
                        defaultValue={100}
                    />
                    &nbsp;
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
                </CardText>
            </Card>
        )
    }
}

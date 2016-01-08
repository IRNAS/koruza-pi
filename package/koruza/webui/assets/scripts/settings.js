import React from 'react';
import ClearFix from 'material-ui/lib/clearfix';
import Paper from 'material-ui/lib/paper';
import TextField from 'material-ui/lib/text-field';
import RaisedButton from 'material-ui/lib/raised-button';
import Dialog from 'material-ui/lib/dialog';

import 'flexboxgrid';

import _ from 'underscore';

import Bus from './bus';

export default class SettingsPage extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            // Authentication status.
            authenticated: Bus.isAuthenticated(),
            // Current settings.
            settings: {},
        }

        this.configurationOptions = [
            {key: 'name', name: 'Unit Name'},
            {key: 'motor_max_x', name: 'Motor Max X'},
            {key: 'motor_max_y', name: 'Motor Max Y'},
            {key: 'motor_max_f', name: 'Motor Max F'},
            {key: 'distance', name: 'Distance'},
            {key: 'remote_ip', name: 'Remote Unit IP'},
            {key: 'data_measurement_host', name: 'Network Measurement Host'},
        ]

        this._onAuthenticated = this._onAuthenticated.bind(this);
        this._onApplyChangesClicked = this._onApplyChangesClicked.bind(this);
        this._onRebootClicked = this._onRebootClicked.bind(this);
    }

    componentWillMount() {
        Bus.addAuthenticationListener(this._onAuthenticated);
        Bus.command('get_status', {}, (status) => {
            this.setState({settings: status.config});
        });
    }

    componentWillUnmount() {
        Bus.removeAuthenticationListener(this._onAuthenticated);
    }

    _onAuthenticated() {
        this.setState({
            authenticated: Bus.isAuthenticated()
        });
    }

    _onApplyChangesClicked() {
        let config = {};
        for (let option of this.configurationOptions) {
            let value = this.refs[option.key].getValue();
            // TODO: Validation.
            config[option.key] = value;
        }

        Bus.command('set_config', {config: config}, (status) => {
            this.setState({settings: status.config});
        });
    }

    _onRebootClicked() {
        this.refs.rebootingDialog.show();
        Bus.command('reboot', {});
    }

    _onOptionChanged(optionKey, event) {
        let settings = this.state.settings;
        settings[optionKey] = event.target.value;
        this.setState({settings: settings});
    }

    render() {
        let styles = {
            settings: {
                marginTop: '5px',
                padding: '5px',
            },
            option: {
                padding: '2px',
            },
            optionName: {
                textAlign: 'right',
            },
            buttons: {
                textAlign: 'center',
            }
        }

        let optionWidgets = [];
        for (let option of this.configurationOptions) {
            let value;
            if (_.isUndefined(this.state.settings[option.key]))
                value = '';
            else
                value = '' + this.state.settings[option.key];

            optionWidgets.push(
                <div className="row middle-xs" key={option.key} style={styles.option}>
                    <div className="col-md-6" style={styles.optionName}>
                        <b>{option.name}</b>
                    </div>
                    <div className="col-md-6">
                        <TextField
                            hintText={option.name}
                            value={value}
                            ref={option.key}
                            disabled={!this.state.authenticated}
                            onChange={this._onOptionChanged.bind(this, option.key)}
                        />
                    </div>
                </div>
            );
        }

        return (
            <ClearFix>
                <h2>Settings</h2>

                <Paper zDepth={1} style={styles.settings}>
                    {optionWidgets}

                    <div className="row" style={styles.option}>
                        <div className="col-md-12" style={styles.buttons}>
                            <br/>
                            <RaisedButton
                                label="Apply changes"
                                disabled={!this.state.authenticated}
                                onTouchTap={this._onApplyChangesClicked}
                            />
                            &nbsp;
                            <RaisedButton
                                label="Reboot device"
                                disabled={!this.state.authenticated}
                                onTouchTap={this._onRebootClicked}
                            />
                        </div>
                    </div>
                </Paper>

                <Dialog
                    title="Rebooting"
                    modal={true}
                    ref="rebootingDialog">

                    Device is rebooting, please wait and reload the page.
                </Dialog>
            </ClearFix>
        );
    }
}
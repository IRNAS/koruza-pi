import React from 'react';
import Dialog from 'material-ui/lib/dialog';
import TextField from 'material-ui/lib/text-field';
import Paper from 'material-ui/lib/paper';

import _ from 'underscore';

import Bus from './bus';

export default class LoginDialog extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            authenticationFailed: false
        }

        this._onLogin = this._onLogin.bind(this);
    }

    show() {
        this.setState({
            authenticationFailed: false
        });

        this.refs.dialog.show();
    }

    dismiss() {
        this.refs.dialog.dismiss();
    }

    _onLogin() {
        Bus.authenticate(
            this.refs.username.getValue(),
            this.refs.password.getValue(),
            (authenticated) => {
                this.setState({
                    authenticationFailed: !authenticated
                });

                if (authenticated) {
                    this.dismiss();
                }
            }
        )
    }

    render() {
        let actions = [
            {'text': "Cancel"},
            {'text': "Login", onTouchTap: this._onLogin, 'ref': 'login'},
        ];

        let styles = {
            dialog: {
                zIndex: 20
            },
            error: {
                marginTop: '5px',
                padding: '5px',
                backgroundColor: '#C27474',
                color: 'white',
            }
        }

        let error;
        if (this.state.authenticationFailed) {
            error = (
                <Paper zDepth={1} style={styles.error}>
                    Authentication failed. Please check your username and password.
                </Paper>
            )
        }

        return (
            <Dialog
                title="Login"
                actions={actions}
                actionFocus="login"
                modal={true}
                style={styles.dialog}
                ref="dialog">

                Please provide your authentication credentials.<br />

                {error}

                <TextField
                    floatingLabelText="Username"
                    ref="username"
                />
                <br/>

                <TextField
                    floatingLabelText="Password"
                    type="password"
                    ref="password"
                />
            </Dialog>
        )
    }
}

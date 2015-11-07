// React.
import React from 'react';
import ReactDOM from 'react-dom';
import {Router, Route, IndexRoute, History} from 'react-router';

// Material UI widgets.
import Styles from 'material-ui/lib/styles';
import AppCanvas from 'material-ui/lib/app-canvas';
import LeftNav from 'material-ui/lib/left-nav';
import ClearFix from 'material-ui/lib/clearfix';
import RaisedButton from 'material-ui/lib/raised-button';

import injectTapEventPlugin from 'react-tap-event-plugin';

import Bus from './bus';
import StatusMotors from './drivers/motors';
import StatusSFP from './drivers/sfp';
import StatusGraph from './graph';
import UnitInformation from './info';
import LoginDialog from './login';

class Status extends React.Component {
    render() {
        return (
            <ClearFix>
                <h2>Status</h2>

                <UnitInformation /><br/>
                <StatusGraph /><br/>
                <StatusMotors /><br/>
                <StatusSFP /><br/>
            </ClearFix>
        );
    }
}

class About extends React.Component {
    render() {
        return (
            <ClearFix>
                <h2>About</h2>

                KORUZA controller web interface.
            </ClearFix>
        );
    }
}

class Dashboard extends React.Component {
    constructor() {
        super();

        this.menuItems = [
            { route: '/status', text: 'Status' },
            { route: '/about', text: 'About' },
        ];

        this.state = {
            authenticated: Bus.isAuthenticated(),
        }

        this._onAuthenticated = this._onAuthenticated.bind(this);
        this._onLoginClicked = this._onLoginClicked.bind(this);
        this._onLogoutClicked = this._onLogoutClicked.bind(this);
    }

    _getSelectedIndex() {
        let currentItem;
        let history = this.props.history;

        for (let i = this.menuItems.length - 1; i >= 0; i--) {
            currentItem = this.menuItems[i];
            if (currentItem.route && history.isActive(currentItem.route)) {
                return i;
            }
        }
    }

    _onNavigationChanged(event, key, payload) {
        this.props.history.pushState(null, payload.route);
    }

    componentWillMount() {
        // Listen for authentication events.
        Bus.addAuthenticationListener(this._onAuthenticated);
    }

    _onAuthenticated() {
        this.setState({
            authenticated: Bus.isAuthenticated()
        });
    }

    componentWillUnmount() {
        Bus.removeAuthenticationListener(this._onAuthenticated);
    }

    _onLoginClicked() {
        this.refs.loginDialog.show();
    }

    _onLogoutClicked() {
        Bus.deauthenticate();
    }

    render() {
        let styles = {
            content: {
                marginLeft: '270px',
            },
            login: {
                float: 'right',
            }
        };

        let loginLogout;
        if (this.state.authenticated) {
            loginLogout = (
                <ClearFix>
                    <RaisedButton
                        label="Logout"
                        onTouchTap={this._onLogoutClicked}
                    />
                </ClearFix>
            );
        } else {
            loginLogout = (
                <ClearFix>
                    <LoginDialog ref="loginDialog" />
                    <RaisedButton
                        label="Login"
                        onTouchTap={this._onLoginClicked}
                    />
                </ClearFix>
            );
        }

        return (
            <AppCanvas>
                <div style={styles.content}>
                    <div style={styles.login}>
                        {loginLogout}
                    </div>

                    {this.props.children}
                </div>
                <LeftNav
                    menuItems={this.menuItems}
                    selectedIndex={this._getSelectedIndex()}
                    onChange={this._onNavigationChanged.bind(this)}
                />
            </AppCanvas>
        );
    }
}

// Route configuration.
const AppRoutes = (
    <Route path="/" component={Dashboard}>
        <Route path="status" component={Status} />
        <Route path="about" component={About} />

        <IndexRoute component={Status}/>
    </Route>
);

// Render root component.
injectTapEventPlugin();
ReactDOM.render(<Router>{AppRoutes}</Router>, document.getElementById('app'));

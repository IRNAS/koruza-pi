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
import EnhancedButton from 'material-ui/lib/enhanced-button';
import Paper from 'material-ui/lib/paper';
import {Tab, Tabs} from 'material-ui/lib/tabs';

const {Colors, Spacing, Typography} = Styles;

import injectTapEventPlugin from 'react-tap-event-plugin';

import Bus from './bus';
import StatusMotors from './drivers/motors';
import StatusSFP from './drivers/sfp';
import StatusGraph from './graph';
import UnitInformation from './info';
import Algorithms from './algorithms';
import LoginDialog from './login';
import SettingsPage from './settings';

class StatusPage extends React.Component {
    render() {
        return (
            <ClearFix>
                <h2>Status</h2>

                <UnitInformation /><br/>
                <StatusSFP /><br/>
                <StatusMotors /><br/>
                <StatusGraph /><br/>
                <Algorithms /><br/>
            </ClearFix>
        );
    }
}

class AboutPage extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            version: null,
        }
    }

    componentWillMount() {
        Bus.command('get_status', {}, (status) => {
            this.setState({
                version: status.version,
            });
        });
    }

    render() {
        let style = {
            version: {
                fontFamily: 'Courier'
            }
        };

        let version = this.state.version ? this.state.version : "unknown";

        return (
            <ClearFix>
                <h2>About</h2>

                KORUZA controller web interface version <span style={style.version}>{version}</span>.
            </ClearFix>
        );
    }
}

class Dashboard extends React.Component {
    constructor() {
        super();

        this.state = {
            authenticated: Bus.isAuthenticated(),
        }

        this._onAuthenticated = this._onAuthenticated.bind(this);
        this._onLoginClicked = this._onLoginClicked.bind(this);
        this._onLogoutClicked = this._onLogoutClicked.bind(this);
        this._onNavigationChanged = this._onNavigationChanged.bind(this);
    }

    _getSelectedIndex() {
        return this.props.history.isActive('/status') ? '1' :
                this.props.history.isActive('/settings') ? '2' :
                this.props.history.isActive('/about') ? '3' : '1';
    }

    _onNavigationChanged(value, event, tab) {
        this.props.history.pushState(null, tab.props.route);
        this.setState({tabIndex: this._getSelectedIndex()});
    }

    componentWillMount() {
        // Listen for authentication events.
        Bus.addAuthenticationListener(this._onAuthenticated);

        this.setState({tabIndex: this._getSelectedIndex()});
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
            root: {
                backgroundColor: Colors.grey900,
                position: 'fixed',
                height: 64,
                top: 0,
                right: 0,
                zIndex: 15,
                width: '100%',
            },
            container: {
                position: 'absolute',
                right: (Spacing.desktopGutter / 2) + 48,
                bottom: 0,
            },
            span: {
                color: Colors.white,
                fontWeight: Typography.fontWeightLight,
                left: 135,
                top: 22,
                position: 'absolute',
                fontSize: 26,
            },
            logoContainer: {
                position: 'fixed',
                width: 300,
                left: Spacing.desktopGutter,
            },
            logo: {
                width: 115,
                backgroundColor: Colors.grey900,
                position: 'absolute',
                top: 8,
            },
            tabs: {
                width: 425,
                bottom: 0,
            },
            tab: {
                height: 64,
                backgroundColor: Colors.grey900,
            },
            login: {
                float: 'right',
            },
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
                <div>
                    <br/><br/><br/><br/>
                    <div style={styles.login}>
                        {loginLogout}
                    </div>

                    {this.props.children}
                </div>
                <div>
                    <Paper
                        zDepth={0}
                        rounded={false}
                        style={styles.root}
                    >
                        <EnhancedButton
                            style={styles.logoContainer}
                            linkButton={true}
                            href="/#/status"
                        >
                            <img style={styles.logo} src="/public/logo.png" />
                            <span style={styles.span}>Controller</span>
                        </EnhancedButton>
                        <div style={styles.container}>
                            <Tabs
                                style={styles.tabs}
                                value={this.state.tabIndex}
                                onChange={this._onNavigationChanged}
                            >
                                <Tab
                                    value="1"
                                    label="STATUS"
                                    style={styles.tab}
                                    route="/status" />
                                <Tab
                                    value="2"
                                    label="SETTINGS"
                                    style={styles.tab}
                                    route="/settings" />
                                <Tab
                                    value="3"
                                    label="ABOUT"
                                    style={styles.tab}
                                    route="/about"/>
                            </Tabs>
                        </div>
                    </Paper>
                </div>
            </AppCanvas>
        );
    }
}

// Route configuration.
const AppRoutes = (
    <Route path="/" component={Dashboard}>
        <Route path="status" component={StatusPage} />
        <Route path="settings" component={SettingsPage} />
        <Route path="about" component={AboutPage} />

        <IndexRoute component={StatusPage}/>
    </Route>
);

// Render root component.
injectTapEventPlugin();
ReactDOM.render(<Router>{AppRoutes}</Router>, document.getElementById('app'));

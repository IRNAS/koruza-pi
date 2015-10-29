import React from 'react';
import Avatar from 'material-ui/lib/avatar';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import ClearFix from 'material-ui/lib/clearfix';

import _ from 'underscore';

class SFPModule extends React.Component {
    render() {
        return (
            <div>
                <Card initiallyExpanded={true}>
                    <CardHeader
                        title="SFP status"
                        subtitle={`Status of the SFP module ${this.props.metadata.model} (${this.props.metadata.serial})`}
                        avatar={<Avatar>S</Avatar>}
                        actAsExpander={true}
                        showExpandableButton={true}
                    />

                    <CardText expandable={true}>
                        Temperature: {this.props.readings.temperature_c} °C<br/>
                        VCC: {this.props.readings.vcc_v} V<br/>
                        TX bias: {this.props.readings.tx_bias_ma} mA<br/>
                        TX power: {this.props.readings.tx_power_mw} mW<br/>
                        RX power: {this.props.readings.rx_power_mw} mW<br/>
                    </CardText>
                </Card>
            </div>
        )
    }
}

export default class StatusSFP extends React.Component {
    constructor() {
        super();

        this.state = {
            // A list of SFP module metadata.
            modules: [],
            // Last sensor readings for each module.
            readings: {},
        }
    }

    componentWillMount() {
        let bus = this.props.bus;
        this._subscription = bus.subscribe('status', ['sfp'], _.throttle((message) => {
            this.setState({
                modules: message.metadata,
                readings: message.sfp,
            });
        }, 300));
    }

    componentWillUnmount() {
        this._subscription.stop();
    }

    render() {
        return (
            <ClearFix>
                {this.state.modules.map((value) => {
                    return <SFPModule
                        key={value.serial}
                        metadata={value}
                        readings={this.state.readings[value.serial]}
                    />
                })}
            </ClearFix>
        )
    }
}

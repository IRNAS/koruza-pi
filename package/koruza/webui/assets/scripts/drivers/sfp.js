import React from 'react';
import Avatar from 'material-ui/lib/avatar';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import ClearFix from 'material-ui/lib/clearfix';

import _ from 'underscore';

import Bus from '../bus';

class SFPModule extends React.Component {
    render() {
        let readings = _.clone(this.props.readings);
        let readingKeys2 = [
            'temperature_c', 'vcc_v',
            'tx_bias_ma'
        ];
        let readingKeys4 = [
            'tx_power_mw', 'tx_power_db',
            'rx_power_mw', 'rx_power_db'
        ];

        for (let key of readingKeys2) {
            readings[key] = readings[key].toFixed(2);
        }
        for (let key of readingKeys4) {
            readings[key] = readings[key].toFixed(4);
        }

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
                        Temperature: {readings.temperature_c} °C<br/>
                        VCC: {readings.vcc_v} V<br/>
                        TX bias: {readings.tx_bias_ma} mA<br/>
                        TX power: {readings.tx_power_mw} mW ({readings.tx_power_db} dB)<br/>
                        RX power: {readings.rx_power_mw} mW ({readings.rx_power_db} dB)<br/>
                    </CardText>
                </Card>
            </div>
        )
    }
}

export default class StatusSFP extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            // A list of SFP module metadata.
            modules: [],
            // Last sensor readings for each module.
            readings: {},
        }
    }

    componentWillMount() {
        this._subscription = Bus.subscribe('status', ['sfp'], _.throttle((message) => {
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

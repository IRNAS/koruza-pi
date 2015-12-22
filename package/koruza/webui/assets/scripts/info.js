import React from 'react';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import Avatar from 'material-ui/lib/avatar';

import _ from 'underscore';

import Bus from './bus';

export default class UnitInformation extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            uuid: null,
            unitName: null,
            ipAddress: null,
            netmeasure: null,
        }
    }

    componentWillMount() {
        Bus.command('get_status', {}, (status) => {
            this.setState({
                uuid: status.uuid,
                ipAddress: status.ip,
                unitName: status.config.name,
            });
        });

        this._subscription = Bus.subscribe('status', ['netmeasure'], _.throttle((message) => {
            this.setState({
                netmeasure: {
                    packetLoss: message.packet_loss,
                    packetsSent: message.packets_sent,
                    packetsRcvd: message.packets_rcvd,
                }
            });
        }, 300));
    }

    componentWillUnmount() {
        this._subscription.stop();
    }

    render() {
        let unitName = this.state.unitName;
        if (!unitName)
            unitName = <i>(not configured)</i>
        let ipAddress = this.state.ipAddress;
        if (!ipAddress)
            ipAddress = <i>(not configured)</i>

        let packetLoss = null;
        if (this.state.netmeasure) {
            packetLoss = this.state.netmeasure.packetLoss + '%'
        } else {
            packetLoss = <i>(not reported)</i>
        }

        return (
            <Card>
                <CardHeader
                    title="Unit information"
                    subtitle="General information about the KORUZA unit"
                    avatar={<Avatar>K</Avatar>}
                />

                <CardText>
                    UUID: {this.state.uuid}<br/>
                    Name: {unitName}<br/>
                    IP: {ipAddress}<br/>
                    Reported link packet loss: {packetLoss}
                </CardText>
            </Card>
        )
    }
}

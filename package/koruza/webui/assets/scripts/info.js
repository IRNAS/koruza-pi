import React from 'react';
import {Card, CardHeader, CardTitle, CardText} from 'material-ui/lib/card';
import Avatar from 'material-ui/lib/avatar';

import _ from 'underscore';

import Bus from './bus';

export default class UnitInformation extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            uuid: null
        }
    }

    componentWillMount() {
        Bus.command('get_status', {}, (status) => {
            this.setState({uuid: status.uuid});
        });
    }

    render() {
        return (
            <Card>
                <CardHeader
                    title="Unit information"
                    subtitle="General information about the KORUZA unit"
                    avatar={<Avatar>K</Avatar>}
                />

                <CardText>
                    UUID: {this.state.uuid}
                </CardText>
            </Card>
        )
    }
}

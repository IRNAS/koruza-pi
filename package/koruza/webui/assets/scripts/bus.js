import _ from 'underscore';

class Subscription {
    constructor(bus, topic, types, handler) {
        this.bus = bus;
        this.topic = topic;
        this.types = types;
        this.handler = handler;
    }

    deliver(data) {
        if (!this.types.filter((typ) => typ == data.type).length)
            return;

        this.handler(data);
    }

    stop() {
        this.bus.unsubscribe(this);
    }
}

class Bus {
    constructor() {
        let location = window.location;
        this._url = `ws://${location.host}/ws`;
        this._socket = new WebSocket(this._url);
        this._socket.onmessage = (event) => {this._messageReceived(event)};
        this._socket.onopen = (event) => {this._processCommandQueue()};
        this._subscribers = {};
        this._commandQueue = [];
    }

    subscribe(topic, types, handler) {
        if (!this._subscribers[topic]) {
            this._subscribers[topic] = [];
        }

        let subscription = new Subscription(this, topic, types, handler);
        this._subscribers[topic].push(subscription);
        return subscription;
    }

    unsubscribe(subscription) {
        let subscriptions = this._subscribers[subscription.topic];
        let index = subscriptions.indexOf(subscription);
        if (index > -1) {
            subscriptions.splice(index, 1);
        }
    }

    _processCommandQueue() {
        if (!this._commandQueue.length)
            return;

        if (this._socket.readyState == WebSocket.OPEN) {
            this._socket.send(JSON.stringify(this._commandQueue[0].data));
        }
    }

    command(command, data, callback) {
        this._commandQueue.push({
            data: _.extend({type: 'command', 'command': command}, data),
            callback: callback,
        });

        if (this._commandQueue.length == 1) {
            this._processCommandQueue();
        }
    }

    _messageReceived(event) {
        let [topic, data] = event.data.split('\x00');
        if (topic == 'command') {
            if (!this._commandQueue.length)
                return;

            let command = this._commandQueue[0];
            if (_.isFunction(command.callback)) {
                command.callback(JSON.parse(data));
            }

            this._commandQueue.shift();
            this._processCommandQueue();
            return;
        }

        let subscribers = this._subscribers[topic];
        if (!subscribers || !subscribers.length)
            return;

        data = JSON.parse(data);
        for (let subscription of subscribers) {
            subscription.deliver(data);
        }
    }
}

// Create the default bus.
export default new Bus();

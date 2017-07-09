import Vue from 'vue'
import Bus from 'python-can-remote'
import throttle from 'lodash/throttle'

import 'bootstrap/dist/css/bootstrap.css'
import './style.css'


function onConnect(bus) {
    // Do some experimentation here
    setInterval(function () {
        bus.send({
            arbitration_id: 0x456,
            data: [1, 2, 3, 4, 5]
        });
    }, 1000);

    bus.send_periodic({
        arbitration_id: 0x123,
        data: [0xff, 0xfe, 0xfd]
    }, 0.005);
/*
    bus.send({
        arbitration_id: 0x123,
        extended_id: false,
        data: [0x100, 0xfe, 0xfd]
    });
*/
    bus.send({
        arbitration_id: 0x6ef,
        extended_id: false,
        is_remote_frame: true,
        dlc: 8
    });

    bus.send({
        arbitration_id: 0xabcdef,
        is_error_frame: true
    });
}

// Temporary array of messages as they are received
var unprocessedMessages = [];

// Update app.messages with messages from unprocessedMessages[]
function updateMessages() {
    var messages = app.messages;
    while (unprocessedMessages.length > 0) {
        // Get first unprocessed message in queue
        var msg = unprocessedMessages.shift();
        // Search for an existing message in the table
        var msgFound = false;
        for (var i = messages.length - 1; i >= 0; i--) {
            var table_msg = messages[i];
            if ((table_msg.arbitration_id == msg.arbitration_id) &&
                (table_msg.extended_id == msg.extended_id) &&
                (table_msg.is_error_frame == msg.is_error_frame) &&
                (table_msg.is_remote_frame == msg.is_remote_frame)) {
                // Calculate time since last message
                msg.delta_time = msg.timestamp - table_msg.timestamp;
                if (app.allMessages) {
                    // Add message as a new row
                    messages.push(msg);
                } else {
                    // Update existing row
                    Vue.set(messages, i, msg);
                }
                msgFound = true;
                break;
            }
        }
        if (!msgFound) {
            // Got a new message
            msg.delta_time = 0;
            messages.push(msg);
        }
    }
}

// Throttled function for updating message view in order to reduce the number
// of DOM updates
var updateMessagesThrottled = throttle(
    updateMessages, 100, {leading: true, trailing: true});

var app = new Vue({
    el: '#app',
    data: {
        url: document.URL.replace(/^http/i, 'ws'),
        bus: null,
        connected: false,
        absoluteTime: false,
        allMessages: false,
        showConfig: false,
        bitrate: '500000',
        channelInfo: '',
        messages: [],
        error: null
    },
    methods: {
        connect: function () {
            this.clear();
            var config = {
                bitrate: parseInt(this.bitrate),
                receive_own_messages: true
            };
            var bus = this.bus = new Bus(this.url, config);

            bus.on('connect', function (bus) {
                app.connected = true;
                app.channelInfo = bus.channelInfo;
                if (process.env.NODE_ENV !== 'production') {
                    onConnect(bus);
                }
            });

            bus.on('message', function (msg) {
                unprocessedMessages.push(msg);
                updateMessagesThrottled();
            });

            bus.on('error', function (error) {
                console.error(error);
                app.error = error;
            });

            bus.on('close', function () {
                app.connected = false;
                app.bus = null;
            });
        },
        disconnect: function () {
            this.bus.shutdown();
        },
        clear: function () {
            this.messages = [];
            this.error = null;
        },
        sortByTime: function () {
            this.messages.sort(function (a, b) {
                return a.timestamp - b.timestamp;
            });
        },
        sortById: function () {
            this.messages.sort(function (a, b) {
                return a.arbitration_id - b.arbitration_id;
            });
        }
    },
    filters: {
        formatData: function (data) {
            var hexData = new Array(data.length);
            for (var i = 0; i < data.length; i++) {
                var hex = data[i].toString(16).toUpperCase();
                if (hex.length < 2) {
                    hex = '0' + hex;
                }
                hexData[i] = hex;
            }
            return hexData.join(' ');
        }
    }
});

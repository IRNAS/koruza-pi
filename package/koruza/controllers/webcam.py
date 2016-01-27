#!/usr/bin/env python
import koruza
import base64
import imgurpython
import time
import requests


class WebCam(koruza.Application):
    application_id = 'webcam'

    # Last photo upload event.
    last_photo_upload = 0
    # Last time the RX power was nominal.
    nominal_rx_power = None
    last_rx_power_nominal = 0

    def on_idle(self, bus, state, remote_state):
        now = time.time()

        # In case a photo hasn't been uploaded for more than 30 minutes, do it now.
        if now - self.last_photo_upload > 1800:
            self.take_photo(bus)

        try:
            rx_power = state['sfp']['sfp'].values()[0]['rx_power_db']
            if self.nominal_rx_power is None or rx_power > self.nominal_rx_power:
                self.nominal_rx_power = rx_power

            if self.nominal_rx_power - rx_power < 6:
                self.last_rx_power_nominal = now
        except (IndexError, KeyError):
            return

        # If the power hasn't been nominal for more than 5 minutes.
        if now - self.last_rx_power_nominal > 300:
            self.take_photo(bus)
            self.nominal_rx_power = None
            self.last_rx_power_nominal = now

    def take_photo(self, bus):
        self.last_photo_upload = time.time()

        # Get flickr configuration.
        try:
            config = bus.command('get_status')['config']
            webcam_host = config['data_measurement_host']
            api = imgurpython.ImgurClient(config['private_imgur_id'], config['private_imgur_secret'])
        except KeyError:
            return

        album_id = config.get('private_imgur_album', None)
        if album_id is None:
            response = api.create_album({
                'title': "KORUZA",
                'privacy': 'public',
                'layout': 'grid',
            })

            # Store album identifier.
            bus.command('set_config', config={
                'imgur_album': response['id'],
                'private_imgur_album': response['deletehash'],
            })
            album_id = response['deletehash']

        try:
            data = requests.get('http://%s:8080/?action=snapshot' % webcam_host).content
        except (requests.HTTPError, requests.ConnectionError):
            return

        api.make_request(
            'POST',
            'upload',
            data={
                'type': 'base64',
                'image': base64.b64encode(data),
                'name': 'koruza',
                'title': "KORUZA Snapshot",
                'album': album_id,
            },
            force_anon=True,
        )

WebCam().start()

# -*- coding: utf-8 -*-

import json
import paho.mqtt.client as mqtt
from smartcard.System import readers
from smartcard.scard import SCARD_SHARE_SHARED, SCARD_PROTOCOL_ANY
from smartcard.util import toHexString


def read_mifare_block_0(connection):
    auth_apdu = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x00, 0x60, 0x00]
    read_apdu = [0xFF, 0xB0, 0x00, 0x00, 0x10]

    data, sw1, sw2 = connection.transmit(auth_apdu)

    if hex(sw1) != hex(144):
        raise Exception('Authorization failed')

    data, sw1, sw2 = connection.transmit(read_apdu)

    if hex(sw1) != hex(144):
        raise Exception('Unable to read block')

    return data


class App:
    def __init__(self, config):
        self.__mqtt = mqtt.Client()
        self.__config = config
        self.__current_card_id = None
        r = readers()

        if len(r):
            self.__connection = r[int(self.__config['SENSOR_NUMBER'])].createConnection()

        else:
            raise Exception('No readers found')

    def handle_card(self):
        payload = {
            'kind': '',
            'args': {}
        }

        try:
            self.__connection.connect(mode=SCARD_SHARE_SHARED, protocol=SCARD_PROTOCOL_ANY)
            bloc_data = read_mifare_block_0(self.__connection)
            card_id = bloc_data[0:4]

            if self.__current_card_id != card_id:
                payload['kind'] = 'card_inserted'
                self.__current_card_id = card_id

            elif self.__current_card_id is not None:
                payload['kind'] = 'current_card'

            payload['args']['id'] = toHexString(self.__current_card_id)

            self.__mqtt.publish('epsi_iot/sensor/sensor01/from_device', json.dumps(payload))

        except Exception as ex:
            print(ex)
            self.__current_card_id = None

    def on_message(self, userdata, msg):
        parts = msg.topic.split('/')
        print(parts)

    def on_connect(self, userdata, flags, rc):
        if rc == 4:
            raise Exception('Invalid username or password')

        if rc != 0:
            raise Exception('Unable to connect to mqtt service')

        print('MQTT connected')

        self.__mqtt.subscribe('epsi_iot/sensor/sensor01/from_clients')

    def start(self):
        def on_mqtt_message(client, userdata, msg):
            nonlocal self
            self.on_message(userdata, msg)

        def on_mqtt_connect(client, userdata, flags, rc):
            nonlocal self
            self.on_connect(userdata, flags, rc)

        self.__mqtt.username_pw_set(self.__config['MQTT_USERNAME'], self.__config['MQTT_PASSWORD'])
        self.__mqtt.on_message = on_mqtt_message
        self.__mqtt.on_connect = on_mqtt_connect
        self.__mqtt.connect(self.__config['MQTT_SERVER'], int(self.__config['MQTT_PORT']),
                            int(self.__config['MQTT_KEEP_ALIVE']))

    def stop(self):
        self.__mqtt.disconnect()

    def loop(self):
        self.__mqtt.loop()
        self.handle_card()

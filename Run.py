from CommandProcessor import CommandProcessor
import paho.mqtt.client as mqtt
import json
import apiai
import uuid
import os

CLIENT_ACCESS_TOKEN = os.getenv('DIALOGFLOW_TOKEN')
MQTT_PORT = int(os.getenv('MQTT_PORT', "1883"))
MQTT_HOST = os.getenv('MQTT_HOST', "10.10.0.137")

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("commandprocessor/process")


def on_message(client, userdata, msg):
    try:
        request = ai.text_request()
        request.lang = 'de'
        request.session_id = uuid.uuid4().hex
        request.query = str(msg.payload, "iso-8859-1")
        response = request.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        processor = CommandProcessor(client)
        processor.process(data)
    except Exception as a:
        print("error occured", a)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    client.loop_forever()


if __name__ == '__main__':
    main()

from CommandProcessor import CommandProcessor
import paho.mqtt.client as mqtt
import json
import apiai
import uuid

CLIENT_ACCESS_TOKEN = os.getenv('DIALOGFLOW_TOKEN')

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
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
    except:
      print("error occured")


def main():

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("10.10.0.137", 1883, 60)

    client.loop_forever()


if __name__ == '__main__':
    main()

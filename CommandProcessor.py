from urllib.request import Request
import urllib.request, urllib.parse
import json
from time import gmtime, strftime
from datetime import datetime
from pytz import timezone


OPENHAB_URL = "http://10.10.0.137:8080/rest/"
SAY_TOPIC = "raspi-1/speak"


class Base:
    artikel = ""
    preposition = ""

    def get_key(self):
        return ""

    def parse(self, text, data):
        for attr, value in data:
            text = text.replace("$" + attr, value)
        return text


class Item(Base):
    def __init__(self, label, keyword, artikel="", preposition=""):
        self.label = label
        self.keyword = keyword
        self.preposition = preposition
        self.artikel = artikel

    def get_key(self):
        return self.keyword


class SwitchDevice(Base):
    def __init__(self, location, device, action):
        self.location = location
        self.device = device
        self.action = action

    def get_key(self):
        return "SwitchDevice/" + self.location.get_key() + "/" + self.device.get_key() + "/" + self.action.get_key()

    def create_key(intent, params):
        if intent != "SwitchDevice":
            return None
        return "SwitchDevice/" + params['location'] + "/" + params['device'] + "/" + params['action']

    def process(self, text, command_processor):
        try:
            url = OPENHAB_URL + "items/" + self.location.label + "_" + self.device.label
            data = bytes(self.action.label, "utf-8")
            q = Request(url)
            q.add_header("Content-Type", "text/plain")
            q.add_header("Accept", "application/json")
            urllib.request.urlopen(q, data).read()
            command_processor.say(self.parse(text, {
                ("location_preposition", self.location.preposition),
                ("location_artikel", self.location.artikel),
                ("device_preposition", self.device.preposition),
                ("device_artikel", self.device.artikel)
            }))
            return
        except Exception as e:
            print(e)
        print("error occured")
        command_processor.say("Es ist ein Fehler aufgetreten")


class Sensors(Base):
    def __init__(self, location, device):
        self.location = location
        self.device = device

    def get_key(self):
        return "Sensors/" + self.location.get_key() + "/" + self.device.get_key()

    def create_key(intent, params):
        if intent != "Sensors":
            return None
        return "Sensors/" + params['sensor_location'] + "/" + params['sensor_types']

    def process(self, text, command_processor):
        try:
            url = OPENHAB_URL + "items/" + self.device.label + "_" + self.location.label
            result = urllib.request.urlopen(url).read()
            value = json.loads(result.decode("utf-8"))['state']
            command_processor.say(self.parse(text, {
                ("location_preposition", self.location.preposition),
                ("location_artikel", self.location.artikel),
                ("device_preposition", self.device.preposition),
                ("device_artikel", self.device.artikel),
                ("value", value.replace('.', ',') + " Grad Celsius")
            }))
            return
        except Exception as e:
            print(e)
        command_processor.say("dieser sensor scheint nicht aktiv zu sein")


class Common(Base):
    def __init__(self):
        pass

    def get_key(self):
        return "Common"

    def create_key(intent, params):
        if intent != "Common":
            return None
        return "Common"

    def process(self, text, command_processor):
        try:
            if text == "uhrzeit":
                t = timezone('Europe/Berlin')
                _str = datetime.now(t).strftime("es ist gerade %H Uhr %M")
                command_processor.say(_str)
            if text == "datum":
                t = timezone('Europe/Berlin')
                _str = datetime.now(t).strftime("heute ist der %d.%m.")
                command_processor.say(_str)
            if text == "wetter":
                url = "http://dataservice.accuweather.com/currentconditions/v1/129842_PC?apikey=Lqm0HAtqCrGJwmZmTvfv38YS02F7tFki&language=de-de&details=false"
                result = urllib.request.urlopen(url).read()
                value = json.loads(result.decode("utf-8"))
                result = "hier das aktuelle Wetter: " + value[0]['WeatherText'] + " bei " + str(value[0]['Temperature']['Metric']['Value']) + " Grad Celsius"
                command_processor.say(result)
            if text == "wettervorhersage":
                url = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/129842_PC?apikey=Lqm0HAtqCrGJwmZmTvfv38YS02F7tFki&language=de-de&metric=true"
                result = urllib.request.urlopen(url).read()
                value = json.loads(result.decode("utf-8"))
                result = "so wird das Wetter heute: " + value['Headline']['Text'] + " bei temperaturen von " + str(value['DailyForecasts'][0]['Temperature']['Minimum']['Value']).replace(".", ",") + " bis " + str(value['DailyForecasts'][0]['Temperature']['Maximum']['Value']).replace('.', ',') + " Grad Celsius"
                command_processor.say(result)

            return
        except Exception as e:
            print(e)
        command_processor.say("die Frage kann ich aktuell nicht beantworten, weil ein Fehler aufgetreten ist")


class CommandProcessor:
    intents = [
        SwitchDevice,
        Sensors,
        Common
    ]
    devices = {}

    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        ######################################################
        # switches
        ######################################################
        sw_lamp = Item("Lamp", "licht", "das")
        sw_dimmer = Item("Dimmer", "licht", "das")

        sw_on = Item("ON", "an")
        sw_off = Item("OFF", "aus")
        sw_0 = Item("0", "aus")
        sw_100 = Item("100", "an")

        sw_livingroom = Item("LivingRoom", "wohnzimmer", "das", "im")
        sw_floor = Item("Floor", "flur", "den", "im")
        sw_sleeproom = Item("SleepRoom", "schlafzimmer", "das", "im")
        sw_kitchen = Item("Kitchen", "küche", "die", "in der")
        sw_workroom = Item("WorkRoom", "arbeitszimmer", "das", "im")

        self.add(SwitchDevice(sw_livingroom, sw_lamp, sw_on))
        self.add(SwitchDevice(sw_livingroom, sw_lamp, sw_off))

        self.add(SwitchDevice(sw_floor, sw_lamp, sw_on))
        self.add(SwitchDevice(sw_floor, sw_lamp, sw_off))

        self.add(SwitchDevice(sw_sleeproom, sw_lamp, sw_on))
        self.add(SwitchDevice(sw_sleeproom, sw_lamp, sw_off))

        self.add(SwitchDevice(sw_kitchen, sw_lamp, sw_on))
        self.add(SwitchDevice(sw_kitchen, sw_lamp, sw_off))

        self.add(SwitchDevice(sw_workroom, sw_dimmer, sw_100))
        self.add(SwitchDevice(sw_workroom, sw_dimmer, sw_0))
        ######################################################
        ######################################################

        ######################################################
        # sensors
        ######################################################
        sen_outside = Item("Outside", "draußen")
        sen_livingroom = Item("LivingRoom", "wohnzimmer", "das", "im")
        sen_kitchen = Item("Kitchen", "küche", "die", "in der")
        sen_floor = Item("Floor", "flur", "den", "im")
        sen_sleeproom = Item("SleepRoom", "schlafzimmer", "das", "im")
        sen_workroom = Item("WorkRoom", "arbeitszimmer", "das", "im")

        sen_temperature = Item("Temperature", "temperatur", "die")

        self.add(Sensors(sen_outside, sen_temperature))
        self.add(Sensors(sen_livingroom, sen_temperature))
        self.add(Sensors(sen_kitchen, sen_temperature))
        self.add(Sensors(sen_floor, sen_temperature))
        self.add(Sensors(sen_sleeproom, sen_temperature))
        self.add(Sensors(sen_workroom, sen_temperature))
        ######################################################
        ######################################################

        ######################################################
        # common
        ######################################################
        self.add(Common())
        ######################################################
        ######################################################

    def add(self, intent):
        self.devices[intent.get_key()] = intent

    def handle_error(self, data):
        self.say("diese Frage kann ich aktuell nicht beantworten!")
        print("error occoured", data)
        pass

    def process(self, data):
        try:
            result = False
            incomplete = data['result']['actionIncomplete']
            text = data['result']['fulfillment']['speech']
            intent_name = data['result']['metadata']['intentName']
            parameters = data['result']['parameters']
            if not incomplete:
                for intent in self.intents:
                    key = intent.create_key(intent_name, parameters)
                    if key is not None:
                        if key in self.devices:
                            self.devices[key].process(text, self)
                            result = True
            if not result:
                self.handle_error("no result")
        except Exception as e:
            print(e)
            self.handle_error(data)
        pass

    def say(self, text):
        print("say: " + text)
        self.mqtt_client.publish(SAY_TOPIC, text.encode('iso-8859-1'))

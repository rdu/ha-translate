from urllib.request import Request
import urllib.request, urllib.parse
import json
from datetime import datetime
from pytz import timezone
import os
import random

OPENHAB_URL = os.getenv('OPENHAB_URL', "http://10.10.0.137:8080/rest/")
SAY_TOPIC = os.getenv('SAY_TOPIC', "raspi-1/speak")


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


class Heater(Base):
    def __init__(self, location, action):
        self.location = location
        self.action = action

    def get_key(self):
        rv = "Heater/" + self.location.get_key() + "/" + self.action.get_key()
        return rv

    def create_key(intent, params):
        if intent != "Heater":
            return None
        rv = "Heater/" + params['location'] + "/" + params['heater_actions']
        return rv

    def process(self, text, command_processor, parameters):
        if parameters['heater_actions'] == 'setze temperatur':
            url = OPENHAB_URL + "items/" + self.location.label + "_Setpoint"
            data = bytes(parameters['temperatures'], "utf-8")
            q = Request(url)
            q.add_header("Content-Type", "text/plain")
            q.add_header("Accept", "application/json")
            urllib.request.urlopen(q, data).read()
            command_processor.say(self.parse("Ok, ich habe die Temperatur $prep $location auf $value gesetzt", {
                ("prep", self.location.preposition),
                ("location", self.location.get_key()),
                ("value", str(round(float(parameters['temperatures']), 2)).replace('.', ',')),
            }))

        if parameters['heater_actions'] == 'temperatur':
            url = OPENHAB_URL + "items/" + self.location.label + "_Setpoint"
            result = urllib.request.urlopen(url).read()
            value = json.loads(result.decode("utf-8"))['state']
            command_processor.say(self.parse("$loc_preposition $location ist die Heizung aktuell auf $value grad "
                                             "celsius eingestellt.", {
                                                 ("loc_preposition", self.location.preposition),
                                                 ("location", self.location.get_key()),
                                                 ("value", value),
                                             }))
        if parameters['heater_actions'] == 'status':
            url = OPENHAB_URL + "items/" + self.location.label + "_Setpoint"
            result = urllib.request.urlopen(url).read()
            value = json.loads(result.decode("utf-8"))['state']
            url = OPENHAB_URL + "items/" + self.location.label + "_Temperature"
            result = urllib.request.urlopen(url).read()
            value2 = json.loads(result.decode("utf-8"))['state']
            url = OPENHAB_URL + "items/" + self.location.label + "_Valve"
            result = urllib.request.urlopen(url).read()
            value3 = json.loads(result.decode("utf-8"))['state']
            if value3 == "ON":
                value3 = "eingeschaltet"
            elif value3 == "OFF":
                value3 = "ausgeschaltet"
            else:
                value = "nicht definiert"
            command_processor.say(self.parse("$loc_preposition $location ist die Heizung aktuell auf $value grad "
                                             "celsius eingestellt. Die Temperatur beträgt dort gerade $val2 grad "
                                             "celsius. Das Ventil ist $val3", {
                                                 ("loc_preposition", self.location.preposition),
                                                 ("location", self.location.get_key()),
                                                 ("value", str(round(float(value), 2)).replace('.', ',')),
                                                 ("val2", str(round(float(value2), 2)).replace('.', ',')),
                                                 ("val3", value3),
                                             }))
        pass


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

    def process(self, text, command_processor, parameters):
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

    def process(self, text, command_processor, parameters):
        try:
            url = OPENHAB_URL + "items/" + self.location.label + "_" + self.device.label
            result = urllib.request.urlopen(url).read()
            value = json.loads(result.decode("utf-8"))['state']
            command_processor.say(self.parse(text, {
                ("location_preposition", self.location.preposition),
                ("location_artikel", self.location.artikel),
                ("device_preposition", self.device.preposition),
                ("device_artikel", self.device.artikel),
                ("value", str(round(float(value), 2)).replace('.', ',') + " Grad Celsius")
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

    def process(self, text, command_processor, parameters):
        try:
            if text == "uhrzeit":
                t = timezone('Europe/Berlin')
                _str = datetime.now(t).strftime("es ist gerade %H Uhr %M").lstrip("0").replace(" 0", " ")
                command_processor.say(_str)
            if text == "datum":
                t = timezone('Europe/Berlin')
                _str = datetime.now(t).strftime("heute ist der %d.%m.").lstrip("0").replace(" 0", " ")
                command_processor.say(_str)
            if text == "wetter":
                url = "http://dataservice.accuweather.com/currentconditions/v1/129842_PC?apikey" \
                      "=Lqm0HAtqCrGJwmZmTvfv38YS02F7tFki&language=de-de&details=false "
                result = urllib.request.urlopen(url).read()
                value = json.loads(result.decode("utf-8"))
                result = "hier das aktuelle Wetter: " + value[0]['WeatherText'] + " bei " + str(
                    value[0]['Temperature']['Metric']['Value']).replace(".", ",") + " Grad Celsius"
                command_processor.say(result)
            if text == "wettervorhersage":
                url = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/129842_PC?apikey" \
                      "=Lqm0HAtqCrGJwmZmTvfv38YS02F7tFki&language=de-de&metric=true "
                result = urllib.request.urlopen(url).read()
                value = json.loads(result.decode("utf-8"))
                result = "so wird das Wetter: " + value['Headline']['Text'] + " bei temperaturen von " + str(
                    value['DailyForecasts'][0]['Temperature']['Minimum']['Value']).replace(".", ",") + " bis " + str(
                    value['DailyForecasts'][0]['Temperature']['Maximum']['Value']).replace('.', ',') + " Grad Celsius"
                command_processor.say(result)
            if text == "anziehen":
                url = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/129842_PC?apikey" \
                      "=Lqm0HAtqCrGJwmZmTvfv38YS02F7tFki&language=de-de&metric=true "
                result = urllib.request.urlopen(url).read()
                value = json.loads(result.decode("utf-8"))
                _min = value['DailyForecasts'][0]['Temperature']['Minimum']['Value']
                _max = value['DailyForecasts'][0]['Temperature']['Minimum']['Value']
                median = (_min + _max) / 2
                text = []
                additional_texts = []
                if _max >= 30:
                    text.append("Heute wird es so warm, da müsstest Du eigentlich gar nix anziehen!")
                    text.append("Das wird so heiß heute - da brauchst Du eigentlich gar nix")
                    additional_texts.append("Das ist natürlich ein Scherz, Du kannst ja nicht ohne Klamotten raus!")
                elif _max >= 28:
                    text.append("Mann, wird das heute warm - zieh so wenig wie möglich an!")
                    text.append("Richtiges Schwitzwetter - viel anziehen musst Du nicht!")
                    additional_texts.append("Was genau, fragst Du am besten Deine Eltern")
                elif _max >= 26:
                    text.append("Sehr warm wird es heute - zieh dünne kurze Sachen an!")
                    text.append("Bei so hohen Temperaturen ziehst Du am besten kurze, dünne Sachen an!")
                elif _max >= 24:
                    text.append("Angenehm warme Temperaturen sind heute zu erwarten, zieh dünne Sachen an!")
                    text.append("Zieh dünne Sachen an!")
                    text.append("Heute dünne Sachen bitte!")
                elif _max >= 20:
                    text.append("Zieh dünne lange Sachen an!")
                    text.append("Heute dünne lange Sachen bitte!")
                    text.append("Heute wird es einigermaßen warm - ziehe bitte dünne, aber lange Sachen an!")
                elif _max >= 16:
                    text.append("Heute lange Sachen bitte!")
                    text.append("Heute wird nicht so sehr warm - ziehe bitte lange Sachen an!")
                elif _max >= 10:
                    text.append("Bitte lange warme Sachen anziehen!")
                    text.append("Heute ist es recht kalt, bitte lange warme Sachen anziehen")
                elif _min >= 5:
                    text.append("Bitte lange warme Sachen anziehen, es wird ganz schön kalt!")
                    text.append("Heute ist es ganz schön kalt, bitte lange warme Sachen anziehen")
                elif _min >= 0:
                    text.append("Bitte lange warme Sachen anziehen, es wird sehr kalt draußen!")
                    text.append("Heute ist es sehr kalt, bitte lange warme Sachen anziehen")
                elif _min >= -5:
                    text.append("Bitte lange warme Sachen anziehen, es wird verdammt kalt draußen!")
                    text.append("Heute ist richtig kalt, bitte lange warme Sachen anziehen")
                elif _min >= -10:
                    text.append("Bitte lange warme Sachen anziehen, es wird bitterkalt draußen!")
                    text.append("Heute ist es richtig doll kalt, bitte lange warme Sachen anziehen")
                elif _min >= -20:
                    text.append("Heute ist es so kalt, da solltest Du besser zu Hause bleiben!")
                    text.append("Arktische kälte ist heute draußen, bleib zu Hause")
                    additional_texts.append("Das ist natürlich ein Scherz, Frag Deine Eltern!")
                _str = random.choice(text)
                if len(additional_texts) > 0:
                    _str = _str + " " + random.choice(additional_texts)
                command_processor.say(_str)
                pass
            return
        except Exception as e:
            print(e)
        command_processor.say("die Frage kann ich aktuell nicht beantworten, weil ein Fehler aufgetreten ist")


class CommandProcessor:
    intents = [
        SwitchDevice,
        Sensors,
        Common,
        Heater
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
        sw_sleeproom = Item("Sleeping_Room", "schlafzimmer", "das", "im")
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
        sen_floor = Item("Heater_Floor", "flur", "den", "im")
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
        # heater
        ######################################################
        heat_floor = Item("Heater_Floor", "flur", "den", "im")
        heat_sleepingroom = Item("SleepingRoom", "schlafzimmer", "das", "im")
        heat_livingroom = Item("LivingRoom", "wohnzimmer", "das", "im")
        heat_kitchen = Item("Kitchen", "küche", "die", "in der")
        heat_workroom = Item("WorkRoom", "arbeitszimmer", "das", "im")

        heat_action_temperature = Item("temperature", "temperatur")
        heat_action_set_temperature = Item("set_temperature", "setze temperatur")
        heat_action_state = Item("state", "status")

        self.add(Heater(heat_floor, heat_action_temperature))
        self.add(Heater(heat_floor, heat_action_set_temperature))
        self.add(Heater(heat_floor, heat_action_state))

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
                            self.devices[key].process(text, self, parameters)
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

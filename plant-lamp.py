#!/bin/python
import RPi.GPIO as GPIO
from datetime import datetime
import time
import ConfigParser
from HTMLParser import HTMLParser
import urllib
import re

Config = ConfigParser.ConfigParser()
LAMP_ONE = 7
ON_WEEKDAY = "7:30"
OFF_WEEKDAY = "17:30"
ON_WEEKEND = "9:30"
OFF_WEEKEND = "19:30"
MODE = "Automatic"
LAMP_ON = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)


def checktime(time):
    return datetime.today().time() > time.time()


class PageGetter(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.output = False
        connection = urllib.urlopen("http://www.timeanddate.com/worldclock/city.html?n=268")
        encoding = connection.headers.getparam('charset')
        page = connection.read().decode(encoding)
        self.pattern = re.compile("([01]?[0-9]|2[0-3]):[0-5][0-9]")
        self.start = None
        self.stop = None
        self.feed(page)

    def handle_data(self, data):
        if (data == "Civil twilight"):
            self.output = True
        if (data == "Nautical twilight"):
            self.output = False
        if (self.output):
            match = self.pattern.match(data)
            if (match is not None):
                if (self.start is None):
                    self.start = match.group()
                else:
                    self.stop = match.group()


def read_from_web():
    global ON_WEEKDAY, ON_WEEKEND, OFF_WEEKDAY, OFF_WEEKEND
    t = PageGetter()
    if datetime.today().weekday() > 4:
        start = datetime.strptime(t.start, "%H:%M")
        stop = datetime.strptime(t.stop, "%H:%M")
        ON_WEEKDAY = start.time().replace(start.hour + 2).strftime("%H:%M")
        OFF_WEEKDAY = stop.time().replace(stop.hour + 2).strftime("%H:%M")
    else:
        ON_WEEKDAY = t.start
        OFF_WEEKDAY = t.stop


def readConfig():
    Config.read("config.ini")
    global LAMP_ONE, ON_WEEKDAY, ON_WEEKEND, OFF_WEEKDAY, OFF_WEEKEND, LAMP_ON, MODE
    if (MODE == "Web"):
        read_from_web()
    else:
        ON_WEEKDAY = Config.get("Weekday", 'turn_on').replace("\"", "")
        OFF_WEEKDAY = Config.get("Weekday", 'turn_off').replace("\"", "")
        ON_WEEKEND = Config.get("Weekend", 'turn_on').replace("\"", "")
        OFF_WEEKEND = Config.get("Weekend", 'turn_off').replace("\"", "")
    MODE = Config.get("Others", "mode").replace("\"", "")
    LAMP_ON = Config.getboolean("Others", "status")
    LAMP_ONE = 7


def toggle_lamp(LAMP):
    global LAMP_ON
    if LAMP_ON:
        GPIO.output(LAMP, GPIO.LOW)
        LAMP_ON = False
        Config.set("Others", "Status", 0)
    else:
        GPIO.output(LAMP, GPIO.HIGH)
        LAMP_ON = True
        Config.set("Others", "Status", 1)
    Config.write(open("config.ini", 'w'))


def restore_state(LAMP):
    global LAMP_ON
    if LAMP_ON:
        GPIO.output(LAMP, GPIO.HIGH)
    else:
        GPIO.output(LAMP, GPIO.LOW)

readConfig()
restore_state(LAMP_ONE)
while True:
    readConfig()
    if MODE == "Automatic":
        if datetime.today().weekday() > 4:
            if LAMP_ON:
                if checktime(datetime.strptime(OFF_WEEKEND, "%H:%M")):
                    toggle_lamp(LAMP_ONE)
            else:
                if checktime(datetime.strptime(ON_WEEKEND, "%H:%M")) and not checktime(datetime.strptime(OFF_WEEKEND, "%H:%M")):
                    toggle_lamp(LAMP_ONE)
        else:
            if LAMP_ON:
                if checktime(datetime.strptime(OFF_WEEKDAY, "%H:%M")):
                    toggle_lamp(LAMP_ONE)
            else:
                if checktime(datetime.strptime(ON_WEEKDAY, "%H:%M")) and not checktime(datetime.strptime(OFF_WEEKDAY, "%H:%M")):
                    toggle_lamp(LAMP_ONE)
    elif MODE == "Web":
        if LAMP_ON:
            if checktime(datetime.strptime(OFF_WEEKDAY, "%H:%M")):
                toggle_lamp(LAMP_ONE)
            else:
                if checktime(datetime.strptime(ON_WEEKDAY, "%H:%M")) and not checktime(datetime.strptime(OFF_WEEKDAY, "%H:%M")):
                    toggle_lamp(LAMP_ONE)
    elif MODE == "On":
        GPIO.output(LAMP_ONE, GPIO.HIGH)
        LAMP_ON = True
        Config.set("Others", "Status", 1)
    elif MODE == "Off":
        GPIO.output(LAMP_ONE, GPIO.LOW)
        LAMP_ON = False
        Config.set("Others", "Status", 0)
    Config.write(open("config.ini", 'w'))
    time.sleep(1)

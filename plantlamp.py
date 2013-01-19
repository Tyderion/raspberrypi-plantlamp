#!/bin/python

from datetime import datetime
import time
import ConfigParser
from HTMLParser import HTMLParser
import urllib
import os
import re

Config = ConfigParser.ConfigParser()
LAMP_ONE = 7
ON_WEEKDAY = "7:30"
OFF_WEEKDAY = "17:30"
ON_WEEKEND = "9:30"
OFF_WEEKEND = "19:30"
ON_TODAY = ""
OFF_TODAY = ""
WEEKEND_OFFSET = 2
MODE = "Automatic"
LOGFILE = "plant.log"
LAST_UPDATE = None
LAMP_ON = False
RPI_ON = False
LOGGER = None


def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True


def __init__():
    global RPI_ON, LAMP_ONE, LOGGER
    RPI_ON = module_exists("RPi")
    LAMP_ONE = Lamp(LAMP_ONE, RPI_ON)
    LOGGER = Logger(LOGFILE, "Main")
    if RPI_ON:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(7, GPIO.OUT)
    else:
        print "NO RPI Present"


def print_conf():
    string = """
    LAMP_ONE = {0}
    ON_WEEKDAY = {1}
    OFF_WEEKDAY = {2}
    ON_WEEKEND = {3}
    OFF_WEEKEND = {4}
    ON_TODAY = {5}
    OFF_TODAY = {6}
    WEEKEND_OFFSET = {7}
    """.format(
        LAMP_ONE, ON_WEEKDAY, OFF_WEEKDAY, ON_WEEKEND,
        OFF_WEEKEND, ON_TODAY, OFF_TODAY, WEEKEND_OFFSET)
    print string

def weekend():
    return datetime.today().weekday() > 4


class Logger:
    def __init__(self, logfile_path, prefix):
        self.logfile_path = logfile_path
        self.prefix = prefix

    def _last_line(self):
        stdin, stdout = os.popen2("tail -n 1 {0}".format(self.logfile_path))
        stdin.close()
        line = stdout.readline()
        stdout.close()
        return line

    def log(self, string):
        last_line = self._last_line().split("]:")
        if last_line[0] != "":
            last_log = datetime.strptime(last_line[0][1:], "%d.%m.%y %H:%M")
        if last_line[0] == "" or not last_line[1].strip().startswith(self.prefix) or (datetime.today() - last_log).total_seconds() > 600:
                with open(self.logfile_path, "a") as logfile:
                    logfile.write("[{0}]: {1} {2}".format(
                        datetime.today().strftime("%d.%m.%y %H:%M"),
                        self.prefix, string))


class Lamp:
    def __init__(self, pin, rpi_present=True):
        global LOGFILE
        self.logger = Logger(LOGFILE, "Lamp{0}".format(pin))
        self.pin = pin
        self.rpi_present = rpi_present

    def _set(self,output):
        if self.rpi_present:
            self.logger.log("was set {1\n".format( self.pin, output))
            GPIO.output(self.pin, output)

    def state(self):
        if self.rpi_present:
            return GPIO.input(self.pin)
        else:
            return False

    def set_on(self):
        if not self.state():
            self._set(GPIO.HIGH)

    def set_off(self):
        if self.state():
            self._set(GPIO.LOW)

    def toggle(self):
        if self.state():
            self.set_on()
        else:
            self.set_off()



class PageGetter(HTMLParser):
    def __init__(self):
        global  LOGFILE
        HTMLParser.__init__(self)
        self.output = False
        connection = urllib.urlopen("http://www.timeanddate.com/worldclock/city.html?n=268")
        encoding = connection.headers.getparam('charset')
        page = connection.read().decode(encoding)
        self.pattern = re.compile("([01]?[0-9]|2[0-3]):[0-5][0-9]")
        self.start = None
        self.stop = None
        self.logger = Logger(LOGFILE, "PageGetter")
        self.feed(page)


    def handle_data(self, data):
        global ON_TODAY, OFF_TODAY,WEEKEND_OFFSET
        if (data == "Civil twilight"):
            self.output = True
        if (data == "Nautical twilight"):
            self.output = False
        if (self.output):
            match = self.pattern.match(data)
            if (match is not None):
                if (self.start is None):
                    self.start = "not None"
                    ON_TODAY  = datetime.strptime(match.group(), "%H:%M").time()
                    if weekend():
                        ON_TODAY = ON_TODAY.replace(ON_TODAY.hour + WEEKEND_OFFSET)
                else:
                    OFF_TODAY  = datetime.strptime(match.group(), "%H:%M").time()
                    self.start = None
                    if weekend():
                        OFF_TODAY = OFF_TODAY.replace(OFF_TODAY.hour + WEEKEND_OFFSET)
                self.logger.log("Today is {0} Weekend. ON-Time is: {1}, OFF-Time is: {2}\n".format("a" if weekend() else "no",ON_TODAY, OFF_TODAY))


def read_from_web():
    PageGetter()

def due_state(time_on, time_off):
    return datetime.today().time() > time_on and datetime.today().time() < time_off

def update_lamp_state(lamp):
    global LOGGER
    read_conf()
    what_to_set = lamp.state()
    LOGGER.log("\n")
    if MODE == "Automatic":
        LOGGER.log("Mode: Automatic")
        if weekend():
            LOGGER.log(" on a Weekend")
            what_to_set =  due_state(ON_WEEKEND, OFF_WEEKEND)
        else:
            LOGGER.log(" on a Weekday")
            what_to_set =   due_state(ON_WEEKDAY, OFF_WEEKDAY)
    elif MODE == "Web":
        LOGGER.log("Mode: Twilight")
        what_to_set =  due_state(ON_TODAY, OFF_TODAY)
    elif MODE == "On":
        LOGGER.log("Mode: On")
        what_to_set =  True
    elif MODE == "Off":
        LOGGER.log("Mode: Off")
        what_to_set =  False
    if what_to_set:
        lamp.set_on()
    else:
        lamp.set_off()


def read_conf():
    Config.read("config.ini")
    global LAMP_ONE, ON_WEEKDAY, ON_WEEKEND, OFF_WEEKDAY, OFF_WEEKEND, LAMP_ON, MODE,LAST_UPDATE
    if LAST_UPDATE is None or (datetime.today()-LAST_UPDATE).total_seconds() > 5*3600:
        read_from_web()
        LAST_UPDATE = datetime.today()
    ON_WEEKDAY = datetime.strptime(Config.get("Weekday", 'turn_on').replace("\"", ""), "%H:%M").time()
    OFF_WEEKDAY = datetime.strptime(Config.get("Weekday", 'turn_off').replace("\"", ""), "%H:%M").time()
    ON_WEEKEND = datetime.strptime(Config.get("Weekend", 'turn_on').replace("\"", ""), "%H:%M").time()
    OFF_WEEKEND = datetime.strptime(Config.get("Weekend", 'turn_off').replace("\"", ""), "%H:%M").time()
    MODE = Config.get("Others", "mode").replace("\"", "")
    LAMP_ON = Config.getboolean("Others", "status")
    LAMP_ONE = 7


__init__()
if __name__ == '__main__':
    while True:
        read_conf()
        update_lamp_state(LAMP_ONE)
        time.sleep(1)

#!/usr/bin/env python
#  Copyright (C) 2012 Michael Clemens
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import RPi.GPIO as GPIO
import os
import pyudev

from mpd import (MPDClient, CommandError)
from socket import error as SocketError
from time import sleep

# Configure MPD connection settings
HOST = 'localhost'
PORT = '6600'
CON_ID = {'host':HOST, 'port':PORT}

# Configure IO ports
BUTTON = 17
LED = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN)
GPIO.setup(LED, GPIO.OUT)

## Some functions
def mpdConnect(client, con_id):
        """
        Simple wrapper to connect MPD.
        """
        try:
                client.connect(**con_id)
        except SocketError:
                return False
        return True

def loadMusic(client, con_id, device):
        print ("0/9 mount")
        os.system("mount "+device+" /music/usb")
        print ("0.5/9 mpc clear")
        os.system("mpc clear")
        print ("1/9 mpd stop")
        os.system("/etc/init.d/mpd stop")
        print ("2/9 rm mp3")
        os.system("rm /music/mp3/*")
        print ("3/9 cp")
        os.system("cp -v /music/usb/* /music/mp3/")
        print ("4/9 umount")
        os.system("umount /music/usb")
        print ("5/9 clear tag cache")
        os.system("rm /music/mpd/tag_cache")
        print ("6/9 mpd start")
        os.system("/etc/init.d/mpd start")
        print ("7/9 mpc clear")
        os.system("mpc clear")
        print ("8/9 mpc add")
        os.system("mpc ls | sort | mpc add")
        print ("9/9 mpd restart")
        os.system("/etc/init.d/mpd restart")
        print ("*** done ****")
#
def flashLED(speed, time):
        for x in range(0, time):
                GPIO.output(LED, GPIO.LOW)
                sleep(speed)
                GPIO.output(LED, GPIO.HIGH)
                sleep(speed)

def updateLED(client):
        # adjust LED to actual state
        if client.status()["state"] == "play":
                GPIO.output(LED, GPIO.LOW)
        else:
                GPIO.output(LED, GPIO.HIGH)

def checkForUSBDevice(name):
        res = ""
        context = pyudev.Context()
        for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
#                print (device.get('ID_FS_LABEL'))
                if device.get('ID_FS_LABEL') == name:
                        res = device.device_node
        return res

def main():
        ## MPD object instance
        client = MPDClient()
        mpdConnect(client, CON_ID)

        status = client.status()
        print (status)

        timebuttonisstillpressed = 0

        flashLED(0.1, 5)
        updateLED(client)

        while True:
                client.ping ()
                device = checkForUSBDevice("1GB") # 1GB is the name of my thumb drive
                if device != "":
                        # USB thumb drive has been inserted, new music will be copied
                        flashLED(0.1, 5)
                        client.disconnect()
                        loadMusic(client, CON_ID, device)
                        mpdConnect(client, CON_ID)
                        print (client.status())
                        flashLED(0.1, 5)
                        # wait until thumb drive is umplugged again
                        while checkForUSBDevice("1GB") == device:
                                sleep(1.0)
                        flashLED(0.1, 5)
                if GPIO.input(BUTTON) == True:
                        if timebuttonisstillpressed == 0:
                                # button has been pressed, pause or unpause now
                                if client.status()["state"] == "stop":
                                        client.setvol(60)
                                        client.play()
                                else:
                                        client.pause()
                                updateLED(client)
                        elif timebuttonisstillpressed > 4:
                                # go back one track if button is pressed > 4 secs
                                client.previous()
                                flashLED(0.1, 5)
                                timebuttonisstillpressed = 0
                        timebuttonisstillpressed = timebuttonisstillpressed + 0.1
                else:
                        timebuttonisstillpressed = 0

                sleep(0.1)

# Script starts here
if __name__ == "__main__":
    main()

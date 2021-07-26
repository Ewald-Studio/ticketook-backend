#!/home/pi/ticketook/backend/env/bin/python

import os
import requests
import datetime
from time import sleep
from gpiozero import Button
from escpos.printer import Usb
from PIL import Image, ImageDraw, ImageFont


API_URL = 'http://local.ticketook.ru/api/'
ACCESS_KEY = '123'
B1_PORT = 2
B2_PORT = 3


class Printer:
    printer = None

    def __init__(self):
        self.connect()

    def connect(self):
        print("Connecting to printer")
        try:
            self.printer = Usb(0x0FE6, 0x811E, 0, 0x81, 0x01)
            self.printer.charcode('ru')
            #self.printer.set(font='a', align=u'center', height=6, width=8, text_type='B')
            print("Connected!")
        except:
            print("Could not connect to printer")

    def print_check(self, msg):
        tries = 0
        while tries < 3:
            try:
                self.printer.set(font='a', align=u'center', height=1, width=2)
                self.printer.text(datetime.datetime.now().strftime("%d.%m.%Y"))
                self.printer.set(font='a', align=u'center', height=6, width=8, text_type='B')
                self.printer.text("\n\n" + msg + "\n\n\n\n\n")
                self.printer.cut()
                break
            except:
                print("error, reconnecting to printer...")
                sleep(0.3)
                self.connect()
                tries += 1


def print_check(msg):
    try:
        PRINTER = Usb(0x0FE6, 0x811E, 0, 0x81, 0x01)
        PRINTER.charcode('ru')
        PRINTER.set(font='a', align=u'center', height=6, width=8, text_type='B')
        PRINTER.text(msg + "\n\n\n")
        PRINTER.cut()
    except:
        print('woohoo')


def print_check_old(msg):
    print('creating image')
    W, H = (600,400)
    im = Image.new("RGBA",(W,H),"white")
    draw = ImageDraw.Draw(im)
    myFont = ImageFont.truetype("DejaVuSans-Bold.ttf", 200)
    w, h = draw.textsize(msg, font=myFont)
    ratio = 500.0 / w
    new_font_size = 200 * ratio
    myFont = ImageFont.truetype("DejaVuSans-Bold.ttf", int(new_font_size))
    w, h = draw.textsize(msg, font=myFont)
    draw.text(((W-w)/2,(H-h)/2), msg, fill="black", font=myFont)
    im.save("check.png", "PNG")
    print('printing')
    os.system('lp check.png')
    print('done')

active_session_id = None

while active_session_id is None:
    try:
        r = requests.get(API_URL + 'zone/1/info/')
        zone_info = r.json()
        active_session_id = zone_info['active_session_id']
    except:
        sleep(5)

print('Active session id:', active_session_id)

button_1 = Button(B1_PORT)
button_2 = Button(B2_PORT)

button_1_state = False
button_2_state = False

counter = 0
printer = Printer()

while True:

    if button_1.is_pressed and button_1_state == False:
        print('B1 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', json={ "access_key": ACCESS_KEY, "service_slug": "first", "session_id": active_session_id })
            printer.print_check(r.json()['ticket']['full_number'])
            sleep(2)
        except:
            pass
        button_1_state = True
    if not button_1.is_pressed and button_1_state == True:
        button_1_state = False

    if button_2.is_pressed and button_2_state == False:
        print('B2 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', json={ "access_key": ACCESS_KEY, "service_slug": "second", "session_id": active_session_id })
            printer.print_check(r.json()['ticket']['full_number'])
            sleep(2)
        except:
            pass
        button_2_state = True
    if not button_2.is_pressed and button_2_state == True:
        button_2_state = False


    counter += 1

    if counter == 300:
        try:
            r = requests.get(API_URL + 'zone/1/info/')
            zone_info = r.json()
            active_session_id = zone_info['active_session_id']
        except:
            pass
        counter = 0

    sleep(0.05)


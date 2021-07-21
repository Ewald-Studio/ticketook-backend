#!/home/pi/ticketook/backend/env/bin/python

import os
from gpiozero import Button
from time import sleep
import requests
from PIL import Image, ImageDraw, ImageFont


API_URL = 'http://local.ticketook.ru/api/'
ACCESS_KEY = '123'
B1_PORT = 2
B2_PORT = 3


def print_check(msg):
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

while True:

    if button_1.is_pressed and button_1_state == False:
        print('B1 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', json={ "access_key": ACCESS_KEY, "service_slug": "first", "session_id": active_session_id })
            print_check(r.json()['ticket']['full_number'])
            sleep(3)
        except:
            pass
        button_1_state = True
    if not button_1.is_pressed and button_1_state == True:
        button_1_state = False

    if button_2.is_pressed and button_2_state == False:
        print('B2 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', json={ "access_key": ACCESS_KEY, "service_slug": "second", "session_id": active_session_id })
            print_check(r.json()['ticket']['full_number'])
            sleep(3)
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


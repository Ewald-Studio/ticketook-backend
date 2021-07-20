import os
from gpiozero import Button
from time import sleep
import requests
from PIL import Image, ImageDraw, ImageFont

API_URL = 'http://192.168.0.48:8000/api/'
ACCESS_KEY = '123'

def print_check(msg):
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
    os.system('lp check.png')


r = requests.get(API_URL + 'zone/1/info/')
zone_info = r.json()
active_session_id = zone_info['active_session_id']

button_1 = Button(1)
button_2 = Button(2)

button_1_state = False
button_2_state = False

counter = 0

while True:

    print('tick')

    if button_1.is_pressed and button_1_state == False:
        print('B1 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', data={ "access_key": ACCESS_KEY, "service_slug": "first", "session_id": active_session_id })
            print_check(r.json()['ticket']['full_number'])
        except:
            pass
        button_1_state = True
    else:
        button_1_state = False
    
    if button_2.is_pressed and button_2_state == False:
        print('B2 pressed!')
        try:
            r = requests.post(API_URL + 'ticket/', data={ "access_key": ACCESS_KEY, "service_slug": "second", "session_id": active_session_id })
            print_check(r.json()['ticket']['full_number'])
        except:
            pass
        button_2_state = True
    else:
        button_2_state = False

    counter += 1

    if counter == 15:
        r = requests.get(API_URL + 'zone/1/info/')
        zone_info = r.json()
        active_session_id = zone_info['active_session_id']
        counter = 0

    sleep(1)

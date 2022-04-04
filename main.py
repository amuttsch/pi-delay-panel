#!/usr/bin/python
# -*- coding:utf-8 -*-

import math
import time
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont

import epd2in9
import epd2in9b

E_INK_RED = False

font16_mono = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', 16)
font13_sans = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 13)
font16_bold = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf', 16)

now = datetime.now().replace(1900, 1, 1)  # Default date as the time in json does not contain a date

access_id = 'foo'

def print_delay_information(drawblack, drawred, offset, ext_id, f, q='', direction=''):
    print("Getting delay information for " + ext_id)
    tries = 0

    r = requests.get("https://www.rmv.de/hapi/departureBoard?accessId=" + access_id + "&extId=" + ext_id + "&format=json" + q)

    while tries < 3 and 'Departure' not in r.json():
        time.sleep(1)
        tries += 1
        r = requests.get("https://www.rmv.de/hapi/departureBoard?accessId=" + access_id + "&extId=" + ext_id + "&format=json" + q)

    if 'Departure' not in r.json():
        print(r.text)
        drawred.text((0, offset + 0), r.text, font=font16_bold, fill=0)
        drawblack.text((0, offset + 17), ext_id, font=font16_mono, fill=0)
        return

    root = r.json()['Departure']

    trains = list(filter(f, root))
    
    station = trains[0]['stop'].replace('Frankfurt (Main) ', '')
    drawred.text((0, offset + 0), station, font = font16_bold, fill = 0)
    
    trains = trains[:3]
    trains.sort(key=lambda t: t['rtTime'] if 'rtTime' in t else t['time'])
    
    for i, t in enumerate(trains):
        track = ''
        if 'track' in t:
            track = t['rtTrack'] if 'rtTrack' in t else t['track']
        time_str = t['rtTime'] if 'rtTime' in t else t['time']
        time = datetime.strptime(time_str, '%H:%M:%S')
        time_diff = str(math.ceil((time-now).seconds / 60)) if time > now else '0'
        drawblack.text((0, offset + (i+1)*17), t['name'].strip() + ': ' + time_diff + 'm', font = font16_mono, fill = 0)
        if len(track) == 2:
            drawred.text((110, offset + (i+1)*17), track, font = font16_bold, fill = 0)
        else:
            drawred.text((118, offset + (i+1)*17), track, font = font16_bold, fill = 0)

    drawblack.text((0, offset + 70), 'nach ' + direction, font = font13_sans, fill = 0)


print("Starting delay inf")

# Drawing on the Vertical image
LBlackimage = Image.new('1', (epd2in9b.EPD_WIDTH, epd2in9b.EPD_HEIGHT), 255)  # 126*298
if E_INK_RED:
    LRedimage = Image.new('1', (epd2in9b.EPD_WIDTH, epd2in9b.EPD_HEIGHT), 255)  # 126*298
else:
    LRedimage = LBlackimage
# Vertical
drawblack = ImageDraw.Draw(LBlackimage)
drawred = ImageDraw.Draw(LRedimage)

print_delay_information(drawblack, drawred, 0, "003001974", lambda d: d['direction'] == "Frankfurt (Main) Neu-Isenburg Stadtgrenze", direction='Frankfurt HBf')
drawblack.line((0, 90, 128, 90), fill = 0)

print_delay_information(drawblack, drawred, 95, "003001204", lambda d: 'track' in d and d['track'] in ['2', '3'], direction='Frankfurt HBf')
drawblack.line((0, 185, 128, 185), fill = 0)

print_delay_information(drawblack, drawred, 190, "003000010", lambda d: d, "&lines=RB68,RB67,RE60", direction='Darmstadt')

font_sans = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 12)
drawblack.text((95, 285), now.strftime("%H:%M"), font = font_sans, fill = 0)

print("Start printing information")
if E_INK_RED:
    epd = epd2in9b.EPD()
    epd.init()
    epd.display(epd.getbuffer(LBlackimage), epd.getbuffer(LRedimage))
else:
    epd = epd2in9.EPD()
    if now.minute % 5 == 0:
        print("Full update")
        epd.init(epd.lut_full_update)
    else:
        print("partial update")
        epd.init(epd.lut_partial_update)
    epd.display(epd.getbuffer(LBlackimage))

time.sleep(1)

epd.sleep()
print("Done")


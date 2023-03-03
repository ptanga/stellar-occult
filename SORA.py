## SORA package
# from sora import Occultation, Body, Star, LightCurve, Observer
# from sora.prediction import prediction
# from sora.extra import draw_ellipse

## Other main packages
from astropy.time import Time
import astropy.units as u
# import astropy.io
from astropy.coordinates import SkyCoord

## Usual packages
import numpy as np
import matplotlib.pylab as pl
import os
import datetime
from datetime import datetime
import csv

MAX_DISTANCE = 15
CSV_FILENAME = "coordinates_csv_test.csv"
HEADER = ['name', 'ra', 'dec', 'start', 'duration', 'mag']

directory = "/home/pi/CSVFiles/"
if not os.path.exists(directory):
    os.makedirs(directory)

def createCSV(star_name):
    exists = False
    # GETTING THE PREDICTION TABLE
    ## First, let's consider an Solar System Body
    # chariklo = Body(name='Chariklo',
    #                 ephem=['guidelines/input/bsp/Chariklo.bsp', 'guidelines/input/bsp/de438_small.bsp'])
    # print(chariklo)

    # pred = prediction(body=chariklo, time_beg='2017-06-20',time_end='2017-06-27',mag_lim=16)
    pred = {'Epoch' : ["2023-05-02 13:45:59", "2023-06-02 01:45:59", "2023-07-02 13:48:59"],
            'ICRS Star Coord at Epoch' : ['00 42 30 +41 12 00', '05 50 30 +10 12 00', '01 22 30 +70 12 00'],
            'G' : [13, 8, 9],
            'Dist' : [12, 20, 4]}

#     for i in range(len(pred)):
    for i in range(len(pred['G'])):
        epoch_str = pred['Epoch'][i]
        epoch = datetime.strptime(epoch_str, "%Y-%m-%d %H:%M:%S")
        if epoch.hour < 12 :
            day_before = epoch.day - 1
            if day_before < 10:
                day_before = '0' + str(day_before)
            print(epoch_str)
            epoch_str = epoch_str[:8] +  str(day_before) + epoch_str[10:]
            print(epoch_str)
            epoch_before = datetime.strptime(epoch_str, "%Y-%m-%d %H:%M:%S")
            path = directory + "all_coordinates_" + epoch_before.strftime("%Y_%m_%d") + '.csv'
        else :
            path = directory + "all_coordinates_" + epoch.strftime("%Y_%m_%d") + '.csv'
            
        if os.path.exists(path):
            exists = True
        
        file = open(path, 'a+', newline='')
        writer = csv.writer(file)
        if not exists:
            writer.writerow(HEADER)
        
        
        epoch = datetime.isoformat(epoch)

        coord = pred['ICRS Star Coord at Epoch'][i]
        c = SkyCoord(coord, unit=(u.hourangle, u.deg))
        ra = c.ra.degree
        dec = c.dec.degree
        
        mag = pred['G'][i]
        
        dist = pred['Dist'][i]
        if dist > MAX_DISTANCE:
            duration = 10*60
        else :
            duration = 4*60

        writer.writerow([star_name + str(i), ra, dec, epoch, duration, mag])

        file.close()

    
# pred est un objet astropy.table
# def writeCSV(star_name):
#     
#     file = open(CSV_FILENAME, 'a', newline='')
#     writer = csv.writer(file)
# 
# #     for i in range(len(pred)):
#     for i in range(len(pred['G'])):
#         epoch = pred['Epoch'][i]
#         epoch = datetime.isoformat(datetime.strptime(epoch, "%Y-%m-%d %H:%M:%S"))
#         
#         coord = pred['ICRS Star Coord at Epoch'][i]
#         c = SkyCoord(coord, unit=(u.hourangle, u.deg))
#         ra = c.ra.degree
#         dec = c.dec.degree
#         
#         mag = pred['G'][i]
#         
#         dist = pred['Dist'][i]
#         if dist > MAX_DISTANCE:
#             duration = 10*60
#         else :
#             duration = 4*60
# 
#         writer.writerow([star_name + str(i), ra, dec, epoch, duration, mag])
# 
#     file.close()
    
createCSV('test_name')

## REPLACE IN CLIENT START BY EPOCH
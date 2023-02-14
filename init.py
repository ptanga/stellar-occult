import PyIndi
import PyIndi
import os
import time
import datetime
from datetime import date, datetime
import sched
import sys
import threading
import matplotlib.pyplot as plt
import astropy.io
from astropy.io import fits
from astroplan import Observer, FixedTarget
import astropy.units as u
from astropy.time import Time
import astrometry
from astropy.coordinates import SkyCoord
from astropy.table import Table
from ast import literal_eval

# creating a log file to keep track of the program
import logging
logname = datetime.now().strftime("%Y_%m_%dT%H")
logging.basicConfig(filename = logname,
                    filemode = 'a',
                    format = '%(asctime)s, %(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt = '%H:%M:%S',
                    level = logging.DEBUG)

import pandas as pd


# Constants
SET_TIME = True
SET_COORD = False

CSV_FILENAME = 'all_coordinates_CSV.csv'
TXT_FILENAME = 'all_coordinates_TXT.txt'

DELAY = 300 # number of seconds to start-time to start calibrating
LATITUDE = 43.78944444
LONGITUDE = 7.26298334
ELEVATION = 369.0
OCA = Observer(longitude=LONGITUDE*u.deg, latitude=LATITUDE*u.deg, elevation=ELEVATION*u.m, name = "OCA", timezone="Europe/Paris")
visible = True


# initializing the client
class IndiClient(PyIndi.BaseClient):
    def __init__(self) :
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass
    
    def newProperty(self, p):
#         print("New ", p.getType(), " property ", p.getName(), " for device ", p.getDeviceName())
#         if p.getType()==PyIndi.INDI_SWITCH:
#             tpy=p.getSwitch()
#             for t in tpy:
#                 print("       "+t.name+"("+t.label+")= ")
#         elif p.getType()==PyIndi.INDI_LIGHT:
#             tpy=p.getLight()
#             for t in tpy:
#                 print("       "+t.name+"("+t.label+")= ")
#         if p.getType()==PyIndi.INDI_TEXT:
#             tpy=p.getText()
#             for t in tpy:
#                 print("       "+t.name+"("+t.label+")= "+t.text)
#         if p.getType()==PyIndi.INDI_NUMBER:
#             tpy=p.getNumber()
#             for t in tpy:
#                 print("       "+t.name+"("+t.label+")= "+str(t.value))

        pass
        
    def removeProperty(self, p):
        pass

    def newBLOB(self, bp):
        global blobEvent
        print("new BLOB ", bp.name)
        blobEvent.set()
        pass

    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass


## connecting the indiserver
# os.popen('indiserver -v indi_qhy_ccd indi_synscan_telescope')

indiclient = IndiClient()
indiclient.setServer("localhost", 7624)
# indiclient.watchDevice("Telescope Simulator")
indiclient.watchDevice("SynScan")
# indiclient.watchDevice("QHY CCD QHY174M-7a6fbf4")
indiclient.watchDevice("CCD Simulator")

if not indiclient.connectServer():            # if no indiserver is detected
# if not indiclient.isServerConnected():            # if no indiserver is detected
    print("No indiserver running on " + indiclient.getHost() + " : " + str(indiclient.getPort()) + " - Try to run")
    print("indiserver indi_synscan_telescope indi_qhy_ccd")
#     sys.exit(1)            # why ?

logging.info('Server connected')
  
# setting up the telescope (see client.py)

## connecting the telescope
# telescope ="Telescope Simulator"
telescope = "SynScan"           # change name of telescope if needed
device_telescope = None
telescope_connect = None

# getting the telescope device (wait for the telescope name to be defined)
device_telescope = indiclient.getDevice(telescope)
while not device_telescope:               # if the name of the telescope has not been returned yet
    time.sleep(0.5)
    device_telescope = indiclient.getDevice(telescope)

# waiting until the CONNECTION property is defined (with the def*) by the telescope
telescope_connect = device_telescope.getSwitch("CONNECTION")    # here, the property CONNECTION contains switches, so we need to use "getSwitch"
while not telescope_connect :
    time.sleep(0.5)
    telescope_connect = device_telescope.getSwitch("CONNECTION")

# connection of the telescope device (this would be an example of STEP THREE : editing a property)
if not device_telescope.isConnected():          # no use in connecting it if it is already connected
    telescope_connect[0].s = PyIndi.ISS_ON      # the first item of the CONNECTION property array is the CONNECT switch, which needs to be ON
    telescope_connect[1].s = PyIndi.ISS_OFF     # the second item of the CONNECTION property array is the DISCONNECT switch, which needs to be OFF
    indiclient.sendNewSwitch(telescope_connect) # the device will now receive the new values of its property CONNECTION

print('telescope connected')
logging.info('Telescope connected')

# setting the correct date
if SET_TIME:
    time_utc = device_telescope.getText("TIME_UTC")
    while not time_utc:
        time.sleep(0.5)
        time_utc = device_telescope.getText("TIME_UTC")
    time_utc[0].text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    time_utc[1].text = '1'
    indiclient.sendNewText(time_utc)
    logging.info('Date set')

# setting the telescope coordinates
if SET_COORD:
    geographic_coord = device_telescope.getNumber("GEOGRAPHIC_COORD")
    while not geographic_coord:
        time.sleep(0.5)
        geographic_coord = device_telescope.getNumber("GEOGRAPHIC_COORD")
    geographic_coord[0].value = LATITUDE
    geographic_coord[1].value = LONGITUDE
    geographic_coord[2].value = ELEVATION
    indiclient.sendNewNumber(geographic_coord)
    logging.info('Teslecope coordinates set')

# connecting the CCD
# ccd = "QHY CCD QHY174M-7a6fbf4"
ccd = "CCD Simulator"
device_ccd = None
ccd_connect = None

# getting the CCD device (wait for the CCD name to be defined)
device_ccd = indiclient.getDevice(ccd)
while not device_ccd:
    time.sleep(0.5)
    device_ccd = indiclient.getDevice(ccd)
    print('restart the server or plug the camera back in')
    logging.warning('Unable to see the camera')
# lp = device_ccd.getProperties()
# for p in lp:
#     print("   > "+p.getName())
#     if p.getType()==PyIndi.INDI_TEXT:
#         tpy=p.getText()
#         for t in tpy:
#             print("       "+t.name+"("+t.label+")= "+t.text)
#     elif p.getType()==PyIndi.INDI_NUMBER:
#         tpy=p.getNumber()
#         for t in tpy:
#             print("       "+t.name+"("+t.label+")= "+str(t.value))
#     elif p.getType()==PyIndi.INDI_SWITCH:
#         tpy=p.getSwitch()
#         for t in tpy:
#             print("       "+t.name+"("+t.label+")= "+strISState(t.s))
#     elif p.getType()==PyIndi.INDI_LIGHT:
#         tpy=p.getLight()
#         for t in tpy:
#             print("       "+t.name+"("+t.label+")= "+strIPState(t.s))
#     elif p.getType()==PyIndi.INDI_BLOB:
#         tpy=p.getBLOB()
#         for t in tpy:
#             print("       "+t.name+"("+t.label+")= <blob "+str(t.size)+" bytes>")

# waiting until the CONNECTION property is defined (with the def*) by the CCD
ccd_connect = device_ccd.getSwitch("CONNECTION")
while not ccd_connect :
    time.sleep(0.5)
    ccd_connect = device_ccd.getSwitch("CONNECTION")
    print('Make sure camera is plugged in, and indi_qhy_ccd is running')
    logging.warning('Unable to connect to the camera')


# connection of the CCD device
if not device_ccd.isConnected():          # no use in connecting it if it is already connected
    ccd_connect[0].s = PyIndi.ISS_ON      # the first item of the CONNECTION property array is the CONNECT switch, which needs to be ON
    ccd_connect[1].s = PyIndi.ISS_OFF     # the second item of the CONNECTION property array is the DISCONNECT switch, which needs to be OFF
    indiclient.sendNewSwitch(ccd_connect) # the device will now receive the new values of its property CONNECTION

print('camera connected')
logging.info('Camera connected')

# once the CCD is connected, it needs to be cooled down
# setting the temperature we want
ccd_temperature = device_ccd.getNumber("CCD_TEMPERATURE")
while not ccd_temperature:
    time.sleep(0.5)
    ccd_temperature = device_ccd.getNumber("CCD_TEMPERATURE")
ccd_temperature[0].value = -10
indiclient.sendNewNumber(ccd_temperature)

# switching the cooler on
ccd_cooler = device_ccd.getSwitch("CCD_COOLER")
while not ccd_cooler:
    time.sleep(0.5)
    ccd_cooler = device_ccd.getSwitch("CCD_COOLER")
ccd_cooler[0].s = PyIndi.ISS_ON       # this is the COOLER_ON switch
ccd_cooler[1].s = PyIndi.ISS_OFF      # this is the COOLER_OFF switch
indiclient.sendNewSwitch(ccd_cooler)

logging.info('Camera is cooling down')

# linking the CCD and the telescope together
ccd_active_devices = device_ccd.getText("ACTIVE_DEVICES")
while not ccd_active_devices:
    time.sleep(0.5)
    ccd_active_devices = device_ccd.getText("ACTIVE_DEVICES")
# ccd_active_devices[0].text = "Telescope Simulator"
ccd_active_devices[0].text = "SynScan"
# ccd_active_devices[5].text = "GPS Simulator"
indiclient.sendNewText(ccd_active_devices)

print('ccd ok')
logging.info('Camera and Telescope linked')

# getting the GPS ready

# # turning the LED off
# led_calibration = device_ccd.getSwitch("LED_CALIBRATION")
# while not led_calibration:
#     time.sleep(0.5)
#     led_calibration = device_ccd.getSwitch("LED_CALIBRATION")
# led_calibration[0].s = PyIndi.ISS_OFF       # this is the LED_ON switch
# led_calibration[1].s = PyIndi.ISS_ON        # this is the LED_OFF switch
# indiclient.sendNewSwitch(led_calibration)
# 
# logging.info('LED turned off')
# 
# # making sure the GPS is in master
# slaving_mode = device_ccd.getSwitch("SLAVING_MODE")
# while not slaving_mode:
#     time.sleep(0.5)
#     slaving_mode = device_ccd.getSwitch("SLAVING_MODE")
# slaving_mode[0].s = PyIndi.ISS_ON        # this is the MASTER switch
# slaving_mode[1].s = PyIndi.ISS_OFF       # this is the SLAVE switch
# indiclient.sendNewSwitch(slaving_mode)
# 
# logging.info('GPS Master mode activated')
# 
# # enabling the GPS Header
# gps_header = device_ccd.getText("GPS_DATA_HEADER")
# while not gps_header:
#     time.sleep(0.5)
#     gps_header = device_ccd.getText("GPS_DATA_HEADER")
# gps_header[0].text = "something"
# gps_header[1].text = "something"
# indiclient.sendNewText(gps_header)
# 
# logging.info('GPS header set')
# 
# # starting test Stream for the GPS to lock
ccd_video_stream = device_ccd.getSwitch("CCD_VIDEO_STREAM")
while not ccd_video_stream:
    time.sleep(0.5)
    ccd_video_stream = device_ccd.getSwitch("CCD_VIDEO_STREAM")
# ccd_video_stream[0].s = PyIndi.ISS_ON       # this is the STREAM_ON switch
# ccd_video_stream[1].s = PyIndi.ISS_OFF       # this is the STREAM_OFF switch
# indiclient.sendNewSwitch(ccd_video_stream)
# 
# # making sure the GPS is locked 
# gps_state = device_ccd.getLight("GPS_STATE")
# while not gps_state:
#     time.sleep(0.5)
#     gps_state = device_ccd.getLight("GPS_STATE")
# while not (gps_state[0].s == PyIndi.IPS_IDLE and gps_state[1].s == PyIndi.IPS_IDLE and gps_state[2].s == PyIndi.IPS_IDLE and gps_state[3].s == PyIndi.IPS_BUSY) : # these are the POWERED, SEARCHING, LOCKING, LOCKED lights
#     time.sleep(1)
# 
# # turning the stream off
# ccd_video_stream[0].s = PyIndi.ISS_OFF      # this is the STREAM_ON switch
# ccd_video_stream[1].s = PyIndi.ISS_ON       # this is the STREAM_OFF switch
# indiclient.sendNewSwitch(ccd_video_stream)
# 
# print("gps ok")
# logging.info('GPS locked')

# unparking telescope
telescope_park = device_telescope.getSwitch("TELESCOPE_PARK")
while not telescope_park:
    time.sleep(0.5)
    telescope_park = device_telescope.getSwitch("TELESCOPE_PARK")
telescope_park[0].s = PyIndi.ISS_OFF  # this is the PARK switch
telescope_park[1].s = PyIndi.ISS_ON   # this is the UNPARK switch
indiclient.sendNewSwitch(telescope_park)
logging.info('Telescope unparked')


# enabling tracking of a star in the property ON_COORD_SET
telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")
while not telescope_on_coord_set:
    time.sleep(0.5)
    telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")
# the ON_COORD_SET property is a vector composed of 3 values in the following order : SLEW, TRACK, SYNC (cf Standard Properties)
telescope_on_coord_set[0].s = PyIndi.ISS_ON # this is the SLEW switch
telescope_on_coord_set[1].s = PyIndi.ISS_OFF  # this is the TRACK switch, which we want to activate
telescope_on_coord_set[2].s = PyIndi.ISS_OFF # this is the SYNC switch
indiclient.sendNewSwitch(telescope_on_coord_set)

logging.info('Telescope in track mode, telescope ready')

# linking to CCD1 blob 
indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")      # putting the BLOB in ALSO, meaning it can be used along another if needed
ccd_ccd1 = device_ccd.getBLOB("CCD1")
while not ccd_ccd1 :
    time.sleep(0.5)
    ccd_ccd1 = device_ccd.getBLOB("CCD1")
    
ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
while not ccd_exposure:
    time.sleep(0.5)
    ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
    
# making sure that the cooling temperature is reached before moving on to taking pictures
# while ccd_temperature[0].value > -9.5 :
#     print('waiting for cool')
#     time.sleep(2)
    
logging.info('Target temperature reached, camera ready')
    
blobEvent = threading.Event()

print('set up ok')

def MagnitudeToExposure(magnitude):
    m0 = 9
    e0 = 5
    return e0 * ( 10**((m0 - magnitude)/2.5) )


### GIVING NEW COORDINATES TO EXPLORE
# note : the coordinates ra and dec are respectively given in decimal hours and degrees)

# setting the coordinates of a desired star
def EnterNewCoordinates(star): # where star is a dictionnary composed of a 'ra' value and a 'dec' valu
    telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
    while not telescope_radec:
        time.sleep(0.5)
        telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
    # the EQUATORIAL_EOD_COORD property is a vector composed of 2 values in the following order : RA in decimal hours, DEC in degrees (cf Standard Properties)
    telescope_radec[0].value = star['ra']
    telescope_radec[1].value = star['dec']
    indiclient.sendNewNumber(telescope_radec)
    logging.info('Telescope moving to RA ' + str(star['ra']) + ' DEC ' + str(star['dec']))

    # the telescope will then move so we have to wait for it to have stopped moving to continue
    # while it is moving, the property state will be BUSY
    while telescope_radec.getState() == PyIndi.IPS_BUSY:
        print("Scope moving to ", telescope_radec[0].value, telescope_radec[1].value)
        time.sleep(5)
        
    logging.info('Telescope pointing RA ' + str(star['ra']) + ' DEC '+ str(star['dec']))
   
#     telescope_radec[0].value = 5
#     telescope_radec[1].value = 80
#     indiclient.sendNewNumber(telescope_radec)
#     while telescope_radec.getState() == PyIndi.IPS_BUSY:
#         print("2222Scope moving to ", telescope_radec[0].value, telescope_radec[1].value)
#         time.sleep(5)
#    
   # GIVING NEW EXPOSURE TIMES FOR IT TO TAKE PICTURES OF WHAT THE TELESCOPE IS POINTING TO

def CapturePictures(star, exposures, message = ""):
#     EnterNewCoordinates(star)
#     ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
#     while not ccd_exposure:
#         time.sleep(0.5)
#         ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
#     
    paths = []

    # initiating first picture
    blobEvent.clear()
    ccd_exposure[0].value = exposures[0]
    indiclient.sendNewNumber(ccd_exposure)
    print('exposure set')

    # taking the next pictures
    for i in range(len(exposures)):
        blobEvent.wait()        # wait until the previous exposure is done
        logging.info('New picture taken with exposure ' + str(exposures[i]) + ' s')

        # start the next exposure
        if i+1 < len(exposures):
            ccd_exposure[0].value = exposures[i+1]
            blobEvent.clear()
            indiclient.sendNewNumber(ccd_exposure)
        
        # process the received exposure
        for blob in ccd_ccd1:

            # access to the contents of the blob (byte array in Python)
            img = blob.getblobdata()
            timestamp = str(time.time())
            temp = timestamp.rsplit('.')
            ts = ''.join(temp)
            today = date.today()
            directory = "/home/pi/captures" + str(today) + "/"
            if not os.path.exists(directory):
               os.makedirs(directory)
            filename = "capture_" + message + star['name'] + "_" + ts + ".fits"
            path = directory + filename
            
            with open(path, "wb") as f:
                f.write(img)
        
        paths.append(path)
        logging.info('Picture saved to file : ' + path)
        
    return paths


def CaptureStream(**star):
    global blobEvent
    blobEvent.clear()

    exposure = MagnitudeToExposure(star['mag'])
    duration = star['duration'] # duration in seconds (float)
        
    # initiating the stream
    ccd_video_stream = device_ccd.getSwitch("CCD_VIDEO_STREAM")
    while not ccd_video_stream:
        time.sleep(0.5)
        ccd_video_stream = device_ccd.getSwitch("CCD_VIDEO_STREAM")
    ccd_video_stream[0].s = PyIndi.ISS_ON       # this is the STREAM_ON switch
    ccd_video_stream[1].s = PyIndi.ISS_OFF       # this is the STREAM_OFF switch
    indiclient.sendNewSwitch(ccd_video_stream)

    logging.info('Stream beginning')

    # configurating the exposure time for the stream
    ccd_streaming_exposure = device_ccd.getNumber("STREAMING_EXPOSURE")
    while not ccd_streaming_exposure:
        time.sleep(0.5)
        ccd_streaming_exposure = device_ccd.getNumber("STREAMING_EXPOSURE")
    ccd_streaming_exposure[0].value = exposure
    indiclient.sendNewNumber(ccd_streaming_exposure)
    print('waiting here')
    blobEvent.wait()
    
    print("stream ready")
    logging.info('Stream exposure set to ' + str(exposure))

    # recording options : duration and file
    # ccd_record_file = device_ccd.getText("RECORD_FILE")
    # while not ccd_record_file:
    #     time.sleep(0.5)
    #     ccd_record_file = device_ccd.getText("RECORD_FILE")
    # ccd_record_file[0].text = "$HOME/indi__D_"          # this is the default directory of the file, the _D_ will translate to the date
    # ccd_record_file[1].text = "indi_record__T_"         # this is the default name of the file, the _T_ will translate to the timestamp
    # indiclient.sendNewText(ccd_record_file)

    ccd_record_options = device_ccd.getNumber("RECORD_OPTIONS")
    l =0
    while not ccd_record_options:
        time.sleep(0.5)
        l+=1
        ccd_record_options = device_ccd.getNumber("RECORD_OPTIONS")
    ccd_record_options[0].s = PyIndi.ISS_ON             # RECORD_DURATION in seconds
    ccd_record_options[0].value = duration              # duration in seconds
    ccd_record_options[1].s = PyIndi.ISS_OFF            # RECORD_FRAME_TOTAL in number of frames
    indiclient.sendNewNumber(ccd_record_options)

    print("ready to record")
    
    # starting the recording of the stream
    ccd_record_stream = device_ccd.getSwitch("RECORD_STREAM")
    while not ccd_record_stream:
        time.sleep(0.5)
        ccd_record_stream = device_ccd.getSwitch("RECORD_STREAM")
    ccd_record_stream[0].s = PyIndi.ISS_OFF            # RECORD_ON records until turned off
    ccd_record_stream[1].s = PyIndi.ISS_ON             # RECORD_DURATION_ON until duration set has elapsed
    ccd_record_stream[2].s = PyIndi.ISS_OFF            # RECORD_FRAME_ON until number of frames set has been captured
    ccd_record_stream[3].s = PyIndi.ISS_OFF            # RECORD_OFF stops recording
    t = time.time()
    indiclient.sendNewSwitch(ccd_record_stream)
    print('here ok')
    
    logging.info('Recording started, for a duration of ' + str(duration) + ' seconds')
    
    # Stop the stream
    while time.time() < t + duration :
        time.sleep(5)
        print('still recording')
    time.sleep(3)     # to make sure the recording has indeed stopped)
    logging.info('Recording ended and saved as indi_record__T_')
    ccd_video_stream[0].s = PyIndi.ISS_OFF       # this is the STREAM_ON switch
    ccd_video_stream[1].s = PyIndi.ISS_ON        # this is the STREAM_OFF switch
    indiclient.sendNewSwitch(ccd_video_stream)
    logging.info('Stream turned off')
        
    blobEvent.clear()
    print("recording OK")


def CalibrateTelescope(**star):
    print("Calibration starting")
    
    # is the star visible right now ?
    star_coord = SkyCoord(ra = star['ra']*u.deg, dec = star['dec']*u.deg)
    print(star['ra'], star['dec'])
    print(star_coord)
    print(OCA)
    target = FixedTarget(coord = star_coord)
    time = Time(datetime.now())
    print(time)
    h = OCA.altaz(time, target).alt
    print(h)
    global visible
    if h.dms[0] < 10 :
        visible = True
        print(h.dms[0])
        print("ERROR : star not visible, check start time")
        print("Moving on to next star")
        logging.warning('ERROR : star not visible, check start time -- Moving on to next star')
#         return
    else:
        print(h.dms[0])
        visible = True
        logging.info('Star visible')
    
    # pointing to star
    if telescope_park[0].s == PyIndi.ISS_ON :
        telescope_park[0].s = PyIndi.ISS_OFF  # this is the PARK switch
        telescope_park[1].s = PyIndi.ISS_ON   # this is the UNPARK switch
        indiclient.sendNewSwitch(telescope_park)
        logging.info('Telescope unparked')
        print('unparked')

    telescope_on_coord_set[0].s = PyIndi.ISS_ON # this is the SLEW switch
    telescope_on_coord_set[1].s = PyIndi.ISS_OFF  # this is the TRACK switch, which we want to activate
    telescope_on_coord_set[2].s = PyIndi.ISS_OFF # this is the SYNC switch
    indiclient.sendNewSwitch(telescope_on_coord_set)
    logging.info('Telescope in tracking mode')
    
    EnterNewCoordinates(star)
    print('coord entered')
#     EnterNewCoordinates({'ra' : 25, 'dec' : 30})


    # checking the accuracy of the telescope aim
    # test picture
    exposure = MagnitudeToExposure(star['mag'])
    print(exposure)
    img_path = CapturePictures(star, [exposure], "foranalysis_")[0]
#     img_path = '/home/pi/captures2023-01-18/capture_star8_16740536844930549.fits'

    logging.info('Analysis picture captured')
    
    # analysis of the picture
    print('Analysing image')
    
#     reply = os.popen('solve-field --ra ' + str(star['ra']*360.0/24.0) + ' --dec ' + str(star['dec']) + ' --radius 10 ' + img_path + ' --overwrite')
#     output = reply.read()
#     if "Field center: (RA,Dec)" in output :
#         coordinates_str = output.split("Field center: (RA,Dec) = (",1)[1]
#         coordinates_cpl = coordinates_str.split(")")[0]
#         alpha0 = float(coordinates_cpl.split(", ")[0]) * 24.0/360.0
#         delta0 = float(coordinates_cpl.split(", ")[1]) * 24.0/360.0
#         logging.info('Stars recognized, coordinates found are (' + str(alpha0) + ', ' + str(delta0) + ')')
#     else :
#         print("Stars are not recognizable - ignoring calibration")
#         logging.warning('Stars are not recognizable - ignoring calibration')
#         alpha0 = star['ra']
#         delta0 = star['dec']*24.0/360.0
    alpha0 = star['ra']
    delta0 = star['dec']*24.0/360.0
    
    # evaluating the error
    if abs(star['ra'] - alpha0) > 2 * 1/900 or abs(star['dec']*24.0/360.0 - delta0) > 2 * 1/900 :
        print("Calibrating telescope...")
        logging.info('Calibrating telescope to (' + str(alpha0) + ', ' + str(delta0) + ')')
        
        # turning SYNC mode on
        telescope_on_coord_set[0].s = PyIndi.ISS_ON # this is the SLEW switch
        telescope_on_coord_set[1].s = PyIndi.ISS_OFF # this is the TRACK switch
        telescope_on_coord_set[2].s = PyIndi.ISS_ON  # this is the SYNC switch, which we want to activate to calibrate the telescope
        indiclient.sendNewSwitch(telescope_on_coord_set)
        
        # syncing the telescope and its actual coordinates
        EnterNewCoordinates({'ra' : alpha0, 'dec' : delta0*360.0/24.0}) # since the option chosen is SYNC, this will not make the telescope move but simply understand where it is
        
        # going back to TRACK mode
        telescope_on_coord_set[0].s = PyIndi.ISS_ON # this is the SLEW switch
        telescope_on_coord_set[1].s = PyIndi.ISS_OFF  # this is the TRACK switch, which we want to activate
        telescope_on_coord_set[2].s = PyIndi.ISS_OFF # this is the SYNC switch
        indiclient.sendNewSwitch(telescope_on_coord_set)
        print("Teslecope calibrated")
        logging.info('Telescope calibrated')
        
        # second time pointing to the star
        EnterNewCoordinates(star)    
    
    else :
        print('telescope already calibrated')
        logging.info('No need to calibrate telescope')
    
    # capturing the control image
#     CapturePictures(star, [exposure], "control_")
    print('control image taken')
    logging.info('Control image captured')
  
  
def CSV_to_TXT(csv_filename, txt_filename):
    df = pd.read_csv(csv_filename,
                     header = 'infer',
                     index_col = False)

    items = df.to_dict('records')
    file = open(txt_filename, 'w')
    for item in items :
        item['ra'] = item['ra'] * 24.0/360.0
        item['start'] = datetime.fromisoformat(item['start']).timestamp()
        file.write(str(item) + "\n")
    file.close()


def main(csv_filename = CSV_FILENAME, txt_filename = TXT_FILENAME):
    CSV_to_TXT(csv_filename, txt_filename)
    
    file = open(txt_filename, 'r')     # the file all_coordinates.txt has to be in the same folder as client.py and have this exact name
    lines = file.readlines()
    
    for line in lines:
        star = literal_eval(line)
        logging.info('Star parameters: ' + str(star))
#     for i in range(1):
#         {'name': 'star2', 'ra': 14.893333333333334, 'dec': 26.2, 'start': 1358543730.0, 'duration': 200, 'mag': 20.0}
#         while not CCDisConnected() :
#             setupCCD()
        
        # wait for five minutes to 'start' time before calibrating
        print("waiting for ", star['start'], " - 5 min")
        logging.info('waiting for T' + ' - ' + str(DELAY) + 'seconds')
        s = sched.scheduler(time.time)
        s.enterabs(star['start'] - DELAY, 1, CalibrateTelescope, kwargs = (star))
        s.run()
        # move on to next star is it is not visible
        if not visible:
            print("not visible")
            continue
            
        # wait for the 'start' time to come to capture the stream
        logging.info('waiting for T' + ' - ' + str(DELAY) + 'seconds')        
        print("waiting for ", star['start'])
        s2 = sched.scheduler(time.time)
        s2.enterabs(star['start'], 1, CaptureStream, kwargs = (star))
        s2.run()
        print(star['name'], " captured")
        
        logging.info(star['name'] + ' captured')
        
        # parking the telescope before next task
#         EnterNewCoordinates({'ra' : ALPHA_PARK, 'dec' : DELTA_PARK})
#         print("Telescope parked to ", ALPHA_PARK, " - ", DELTA_PARK)
#         logging.info("Telescope parked to " + str(ALPHA_PARK) + " - " + str(DELTA_PARK))
#         
#         # deactivate tracking        
#         telescope_on_coord_set[0].s = PyIndi.ISS_OFF # this is the SLEW switch
#         telescope_on_coord_set[1].s = PyIndi.ISS_OFF # this is the TRACK switch
#         telescope_on_coord_set[2].s = PyIndi.ISS_OFF # this is the SYNC switch, which we want to activate to calibrate the telescope
#         indiclient.sendNewSwitch(telescope_on_coord_set)
#         logging.info('Track mode disabled')
        
        
        telescope_park[0].s = PyIndi.ISS_ON  # this is the PARK switch
        telescope_park[1].s = PyIndi.ISS_OFF # this is the UNPARK switch
        indiclient.sendNewSwitch(telescope_park)
        while telescope_park.getState() == PyIndi.IPS_BUSY:
            time.sleep(2)
            print('Telescope parking')
        logging.info("Telescope parked")
        
        telescope_track_state = device_telescope.getSwitch("TELESCOPE_TRACK_STATE")
        print(telescope_track_state[0].s == PyIndi.ISS_ON)
#         
    print("All tasks done, disconnecting server")
    
main()
# indiclient.disconnectServer()

# turning cooling off
# ccd_cooler = device_ccd.getSwitch("CCD_COOLER")
# while not ccd_cooler:
#     time.sleep(0.5)
#     ccd_cooler = device_ccd.getSwitch("CCD_COOLER")
# ccd_cooler[0].s = PyIndi.ISS_OFF     # this is the COOLER_ON switch
# ccd_cooler[1].s = PyIndi.ISS_ON      # this is the COOLER_OFF switch
# indiclient.sendNewSwitch(ccd_cooler)
# 
# # disconnecting the CCD
# ccd_connect = device_ccd.getSwitch("CONNECTION")    # here, the property CONNECTION contains switches, so we need to use "getSwitch"
# while not ccd_connect :
#     time.sleep(0.5)
#     ccd_connect = device_ccd.getSwitch("CONNECTION")
# if not device_ccd.isConnected():          # no use in connecting it if it is already connected
#     ccd_connect[0].s = PyIndi.ISS_OFF      # the first item of the CONNECTION property array is the CONNECT switch, which needs to be ON
#     ccd_connect[1].s = PyIndi.ISS_ON     # the second item of the CONNECTION property array is the DISCONNECT switch, which needs to be OFF
#     indiclient.sendNewSwitch(ccd_connect) # the device will now receive the new values of its property CONNECTION
# 
# # laisser allumer et changer la temp cible 
# 
# 
# # disconnecting the telescope
# telescope_connect = device_telescope.getSwitch("CONNECTION")    # here, the property CONNECTION contains switches, so we need to use "getSwitch"
# while not telescope_connect :
#     time.sleep(0.5)
#     telescope_connect = device_telescope.getSwitch("CONNECTION")
# if device_telescope.isConnected():          # no use in connecting it if it is already connected
#     telescope_connect[0].s = PyIndi.ISS_OFF      # the first item of the CONNECTION property array is the CONNECT switch, which needs to be ON
#     telescope_connect[1].s = PyIndi.ISS_ON     # the second item of the CONNECTION property array is the DISCONNECT switch, which needs to be OFF
#     indiclient.sendNewSwitch(telescope_connect) # the device will now receive the new values of its property CONNECTION
# 
# # killing the indiserver
# os.popen('touch /tmp/noindi')
# os.popen('sudo pkill indiserver')

# to restart everything
# os.popen('rm -f /tmp/noindi')

# shutting down the raspberry
# os.popen('sudo shutdown -h now')
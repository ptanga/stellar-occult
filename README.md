The purpose of this program is to schedule streaming of several stars through the night to automatically capture stellar occultations by asteroids. 
It uses INDI drivers and follows the INDI Protocol to control a mount and a CCD camera from a RaspberryPi computer. Before executing the code, the RaspberryPi must be turned on, and physically connected to the camera and the mount. Also, INDI has to be installed on the RaspberryPi (it can be downloaded [here](https://indilib.org/get-indi.html?start=5)), as well as a few python modules like PyIndi, astropy.io, astroplan and astrometry.net.

### The architecture of the INDI Protocol

<img width="900" alt="INDIarchitecture" src="https://user-images.githubusercontent.com/105792791/218797218-626ab47b-a6e5-4d77-a010-176f20ef06e7.PNG">

source: https://www.frontiersin.org/articles/10.3389/fspas.2022.895732/full


### Physical connections

Before setting up the network and internal connections of the INDI Protocol, which are taken care of in the program, the physical connections must be established. In our installation, we use a RaspberryPi 4, a CCD camera, and a mount. The CCD camera and the telescope are connected to a hub, itself connected to the RaspberryPi, and powered by a battery. The RaspberryPi is also connected to a power source. The CCD camera we use has a GPS antenna, which is useful to get exact timestamps. The antenna is connected to the CCD camera. Below is how the installation looks like when operational. 

<img width="700" src="https://user-images.githubusercontent.com/105792791/221595782-110f001b-c82d-4191-8409-f3ab34ce0668.jpg" alt="connections">


### Structure of the installation
![structure](https://user-images.githubusercontent.com/105792791/218798228-31a61e17-e6e3-4f57-b9dc-e143fa339678.jpg)


Here is how the program works.

1. initialization of the indi server and the indiclient
2. setup of the devices and their properties
3. running of the main function :
    - calibration of the telescope
    	- control of the star's visibility
     	- control of the telescope's accuracy
     	- capture of a control picture
    - capture of a stream
     	 - setup of the stream parameters
     	 - recording of the telescope
    - parking of the telescope
4. disconnection of the devices 
5. termination of the server


# I/ Setting up the installation
  ## 1. initializing the server and client
	
  This code is using the open source software INDI to control the telescope orientation and camera trigger. So before anything else, an INDI server needs to be launched and an INDI client needs to be initialized: the server will run the commands, and the client will control the devices from the server.
	
  To initialize the server, the command 'indiserver' has to be run in a terminal, followed by the initialization of the devices that we want to control. In this case, we are using a QHY CCD camera, and a SynScan telescope, so the full command to run is as follows:
  
``` indiserver -v indi_qhy_ccd indi_synscan_telescope ```

  To initialize the client, we need to create a subclass to the original INDI class responsible for creating clients : BaseClient. The subclass (called IndiClient) inherits the properties and methods of BaseClient (e.g. *newDevice()* etc). None of the methods need to be overridden in theory, but overriding the *newBLOB()* method enables the use of Python module threading, which will prove useful to be able to continue capturing new data while processing data that has just been captured. The *newProperty()* method can also be overridden to display all properties for all devices (see [commented lines](https://github.com/jdescloitres/stellar-occult/blob/8d35b0a24db68d4415e321e34fa352013d766600/client.py#L56) in client.py). 
  
``` 
class IndiClient(PyIndi.BaseClient):
    def __init__(self) :
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass   
    def newProperty(self, p):
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
``` 

  Once the client subclass has been created, we need to create an instance of IndiClient, and link it to the server. Once the client is connected to the server, the set up of the devices can begin.
  
``` 
indiclient = IndiClient()
indiclient.setServer("localhost", 7624)
```

 ## 2. setting up the devices
	
  To be able to control the doings of the telescope and the camera, they first have to be recognized by the client. Here is the example for the camera.

``` 
ccd = "QHY CCD QHY174M-7a6fbf4" 
device_ccd = indiclient.getDevice(ccd)
``` 
 Once they are, they have to be connected to the server, after which all properties will be controllable through the server with predefined commands.

```
ccd_connect = device_ccd.getSwitch("CONNECTION")
if not device_ccd.isConnected():
    ccd_connect[0].s = PyIndi.ISS_ON      # this is the CONNECT switch
    ccd_connect[1].s = PyIndi.ISS_OFF     # this is the DISCONNECT switch
    indiclient.sendNewSwitch(ccd_connect)
```

  Here is how setting the properties works, illustrated by the example of the CCD's temperature property.

``` 
ccd_temperature = device_ccd.getNumber("CCD_TEMPERATURE")
while not ccd_temperature:
    time.sleep(0.5)
    ccd_temperature = device_ccd.getNumber("CCD_TEMPERATURE")
ccd_temperature[0].value = -10
indiclient.sendNewNumber(ccd_temperature)
``` 
  For every device, there is a defined list of properties, with specific types and names (most of them can be found under [Standard Properties](https://indilib.org/develop/developer-manual/101-standard-properties.html#:~:text=Put%20another%20way%2C%20INDI%20standard,telescope's%20current%20RA%20and%20DEC.) on the [Indilib website](https://indilib.org/index.html). The CCD's temperature is a type **Number** property and its name is *'CCD_TEMPERATURE'*. Other types include **Text** and **Switch** (ON/OFF). In order to change a property, it has to be accessed first with the *getType(“NAME_OF_PROP”)* method. For example the CCD's temperature is accessed by *getNumber(“CCD_TEMPERATURE”)*.
	
  Then, once the server was able to get the property, we can set its value, text, or position depending on whether the property type is **Number**, **Text** or **Switch**. Each property is represented as an array in Python (it can be an array of just 1 element), so in order to set values for a property, it can simply be called with indexes. The CCD temperature property is a single value, so *ccd_temperature[0].value = XX* will set the CDD temperature to *XX*. Finally, for the new set value to be taken into account, the redefined array has to be sent to the device by the client, using the *sendNewType* method. For the CCD temperature property, it would be *sendNewNumber(ccd_temp)*.

![properties](https://user-images.githubusercontent.com/105792791/218799526-040d9522-9d9a-404f-91af-b61fe3184488.jpg)

## 3. setting the values for the constants

  Before getting started, the constants have to be adapted. First, the indiserver launching command in the terminal depends on the type of each device, so it's important to change the line to whatever type of devices we have. Just as important are the names of the devices that we wish to connect to INDI. Their names can be found in the terminal after executing the indiserver command, or by launching the server with KStars/Ekos.
  
``` 
TELESCOPE_NAME = "Synscan"
CCD_NAME = "QHY CCD QHY174M-7a6fbf4"
```

  Another set of constants that will probably need to be changed is that of the coordinates of the telescope. In this case, the telescope is located at the OCA, so the constants LATITUDE, LONGITUDE and ELEVATION correspond to the observatory. The OBSERVER constant uses astroplan to create an Observer instance corresponding to the location of the telescope.
  
```
LATITUDE = 43.78944444
LONGITUDE = 7.26298334
ELEVATION = 369.0
NAME = "OCA"
TIMEZONE = "Europe/Paris"
OBSERVER = Observer(longitude=LONGITUDE*u.deg, latitude=LATITUDE*u.deg, elevation=ELEVATION*u.m, name=NAME, timezone=TIMEZONE)
```

  Next, the names of the files on which the coordinates are written can be changed. CSV_FILENAME is the name of the already existing CSV file giving the program the coordinates of the stars to observe, and TXT_FILENAME is the name of the TXT file that will be created within the program. 
  
```
CSV_FILENAME = 'all_coordinates_CSV.csv'
TXT_FILENAME = 'all_coordinates_TXT.txt'
```

The DELAY constant corresponds to the number of seconds prior to the start time given in the CSV file at which to start the calibration of the telescope. For example, here, the calibration of the telescope will start 5 minutes (300 seconds) before the time at which we want to start recording the stream. Finally, the RADIUS constant corresponds to the radius entered during the astrometry.net search, which is the radius from the given coordinates for it to look for known recognizable stars. 

```
DELAY = 300 # number of seconds to start-time to start calibrating
RADIUS = 10 # radius given to astrometry.net search
```

# II/ The main function

  The main function is the function that will trigger the pictures and streams of a chosen star at a chosen time. It takes in argument a CSV file containing information on stars to captured and when and how to capture them (see [example](https://github.com/jdescloitres/stellar-occult/blob/main/all_coordinates_CSV_example.csv)). This CSV file changes every night. Each line of the file represents a star. To simplify the code, this content of the CSV file is then represented as dictionnaries in a TXT file (see CSV_TO_TXT).

The main function is divided in three parts for each star:
- calibration of the telescope
- capture of the stream
- parking the telescope before next star

The calibration of the telescope and the capture of the stream are set to start respectively five minutes (see value of DELAY) before and at the time given in the text file, with the help of the scheduler function. 

```
s = sched.scheduler(time.time)
s.enterabs(star['start'] - DELAY, 1, CalibrateTelescope, kwargs = (star))
s.run()
```

The telescope is parked once the stream recording has ended.

## 1. calibration of the telescope
	
The calibration itself is divided into three (or four) parts (see Figure):
- making sure the star is visible
- making sure the telescope is pointing in the correct direction
- (and recalibrating it if not)
- capturing a control picture for future analysis
	
 The first step to calibrating the telescope is making sure the star we are directing it to is in fact visible at this time of night. To do so, we are using the astroplan library, and giving it the scope's coordinates on Earth, the coordinates of the target (star), and the time.
 
```
star_coord = SkyCoord(ra = star['ra']*u.deg, dec = star['dec']*u.deg)
target = FixedTarget(coord = star_coord)
time = Time(datetime.now())
h = OCA.altaz(time, target).alt		# h is the current altitude of the star
```
  If the star is not yet visible, the program will stop the calibration and move on to the next target in the text file.
  If the star is visible, however, the program carries on with the next step: checking the accuracy of the telescope's coordinates. The coordinates of the star are given to the telescope for it to move to them. Once the telescope is locked on a direction (and tracking it), a picture is captured. This picture is then analyzed by astrometry.net, which will return (if the stars are recognizable) the actual coordinates of the portion of the sky the telescope is pointing to. 
  
``` 
reply = os.popen('solve-field --ra ' + str(star['ra']*360.0/24.0) + ' --dec ' + str(star['dec']) + ' --radius 10 ' + img_path + ' --overwrite')
output = reply.read()
if "Field center: (RA,Dec)" in output :
	coordinates_str = output.split("Field center: (RA,Dec) = (",1)[1]
	coordinates_cpl = coordinates_str.split(")")[0]
	alpha0 = float(coordinates_cpl.split(", ")[0]) * 24.0/360.0
	delta0 = float(coordinates_cpl.split(", ")[1]) * 24.0/360.0
	logging.info('Stars recognized, coordinates found are (' + str(alpha0) + ', ' + str(delta0) + ')')
else :
	print("Stars are not recognizable - ignoring calibration")
	alpha0 = star['ra']
	delta0 = star['dec']*24.0/360.0
```

  If the difference - between the coordinates given to the telescope and the actual ones returned by astrometry.net - is small enough, the telescope is considered already calibrated. 
  If not, the telescope is then synced to the coordinates returned by astrometry.net
	
  In any case, the program then moves on to capturing a picture of the sky, which will serve as a control image.

## 2. capture of the stream
	
The steps to capturing the stream are fairly straightforward:
- starting the stream (setting the streaming property switch ON)
- setting the streaming exposure
- setting the duration of the recording 
- starting the recording of the stream
- turning the stream of once the duration of the recording's passed
	
## 3. parking of the telescope
	
  To park the telescope, the telescope property for parking is switched on, and the telescope will move to predefined parking coordinates. Then, we make sure the tracking mode of the telescope is disabled so that the telescope does not move until the next target's time has come. 
  
```
telescope_park[0].s = PyIndi.ISS_ON  # this is the PARK switch
telescope_park[1].s = PyIndi.ISS_OFF # this is the UNPARK switch
indiclient.sendNewSwitch(telescope_park)
while telescope_park.getState() == PyIndi.IPS_BUSY:
    time.sleep(2)
print('Telescope parked')
```

### Visual representation of the main function

![main](https://user-images.githubusercontent.com/105792791/218799919-626b37ef-00ba-4238-b944-7c8e0c749587.jpg)


# III/ Details for secondary functions
 ## 1. EnterNewCoordinates
	
  This function gives the telescope new equatorial coordinates to track, and waits for it to be locked on its new position (by interrogating the state of the property and waiting until it is not BUSY anymore).
	
 ## 2. CapturePictures
	
  This function takes in argument a star and a list of exposures to capture the star with. For every given exposure, the program will wait for the previous picture to have been captured before taking a new one, while the first one is being processed and saved to a fits file, the name of which contains information on the star itself and the time of the capture. All pictures are saved into a folder named with the current date. 
The function returns a list of the names of the paths. The use of this function in the main function is restricted to one exposure each time it is called, and the path returned is used for astrometry.net.
	
 ## 3. MagnitudeToExposure
	
  The aim of this function is to give an equivalent of exposure for magnitude given, in a way that the relation between magnitude and exposure is the same for every star (no matter the magnitude).


# IV/ Terminating the program

  Once the all the stars have been captured, it is time to properly stop the program. First, the devices have to be disconnected from the server (the same way they were connected to it). NB: the CCD camera's cooler should be turned off before disconnecting the camera. Once the devices are disconnecting, the server can be killed through a terminal, and the Raspberry PI can be shutdown.

```
# killing the indiserver
os.popen('touch /tmp/noindi')
os.popen('sudo pkill indiserver')

# shutting down the raspberry
os.popen('sudo shutdown -h now')
```

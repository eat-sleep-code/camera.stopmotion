#/usr/bin/python3
from picamera import PiCamera
from light import Light
import server
import datetime
import fractions
import os
import signal
import subprocess
import sys
import threading
import time


version = '2022.02.13'

camera = PiCamera()
PiCamera.CAPTURE_TIMEOUT = 1500
camera.resolution = camera.MAX_RESOLUTION
camera.sensor_mode = 3
camera.framerate = 30
running = False
statusDictionary = {'message': '', 'action': '', 'colorR': 0, 'colorG': 0, 'colorB': 0, 'colorW': 0}
buttonDictionary = {'switchMode': 0, 'shutterUp': False, 'shutterDown': False, 'isoUp': False, 'isoDown': False, 'evUp': False, 'evDown': False, 'capture': False, 'lightR': 0, 'lightB': 0, 'lightG': 0, 'lightW': 0, 'exit': False}

outputLog = open('/home/pi/camera.stopmotion/logs/output.log', 'w+')
errorLog = open('/home/pi/camera.stopmotion/logs/error.log', 'w+')

shutter = 'auto'
shutterLong = 30000
shutterLongThreshold = 1000
shutterShort = 0
defaultFramerate = 30

iso = 'auto'
isoMin = 100
isoMax = 1600

exposure = 'auto'

ev = 0
evMin = -25
evMax = 25

awb = 'auto'

outputFolder = 'dcim/'

timer = 0

raw = False
try:
	from pidng.core import RPICAM2DNG
	dng = RPICAM2DNG()
	raw = True
except:
	print( ' WARNING: DNG file format not currently supported on this device.  ')


# === Echo Control =============================================================

os.environ['TERM'] = 'xterm-256color'
def echoOff():
	subprocess.Popen(['stty', '-echo'], shell=True, stdout=subprocess.DEVNULL, stderr=errorLog)
def echoOn():
	subprocess.Popen(['stty', 'echo'], shell=True, stdout=subprocess.DEVNULL, stderr=errorLog)
def clear():
	subprocess.Popen('clear' if os.name == 'posix' else 'cls')
clear()



# === Functions ================================================================

def showInstructions(clearFirst = False, wait = 0):
	if clearFirst == True:
		clear()
	else:
		print(' ----------------------------------------------------------------------')

		time.sleep(wait)
	return

# ------------------------------------------------------------------------------

def setShutter(input, wait = 0):
	global shutter
	global shutterLong
	global shutterLongThreshold
	global shutterShort
	global defaultFramerate
	global statusDictionary
	
	if str(input).lower() == 'auto' or str(input) == '0':
		shutter = 0
	else:
		shutter = int(float(input))
		if shutter < shutterShort:
			shutter = shutterShort
		elif shutter > shutterLong:
			shutter = shutterLong 

	try:
		if camera.framerate == defaultFramerate and shutter > shutterLongThreshold:
			camera.framerate=fractions.Fraction(5, 1000)
		elif camera.framerate != defaultFramerate and shutter <= shutterLongThreshold:
			camera.framerate = defaultFramerate
	except Exception as ex:
		# print( ' WARNING: Could not set framerate! ')
		pass
	
	try:
		if shutter == 0:
			camera.shutter_speed = 0
			#print(str(camera.shutter_speed) + '|' + str(camera.framerate) + '|' + str(shutter))	
			print(' Shutter Speed: auto')
			statusDictionary.update({'message': 'Shutter Speed: auto'})
		else:
			camera.shutter_speed = shutter * 1000
			#print(str(camera.shutter_speed) + '|' + str(camera.framerate) + '|' + str(shutter))		
			floatingShutter = float(shutter/1000)
			roundedShutter = '{:.3f}'.format(floatingShutter)
			if shutter > shutterLongThreshold:
				print(' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]')
				statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]'})
			else:
				print(' Shutter Speed: ' + str(roundedShutter) + 's')
				statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter) + 's'})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Shutter Speed! ' + str(shutter) + '\n ' + str(ex))

# ------------------------------------------------------------------------------				

def setISO(input, wait = 0):
	global iso
	global isoMin
	global isoMax
	global statusDictionary

	if str(input).lower() == 'auto' or str(input) == '0':
		iso = 0
	else: 
		iso = int(input)
		if iso < isoMin:	
			iso = isoMin
		elif iso > isoMax:
			iso = isoMax	
	try:	
		camera.iso = iso
		#print(str(camera.iso) + '|' + str(iso))
		if iso == 0:
			print(' ISO: auto')
			statusDictionary.update({'message': ' ISO: auto'})
		else:	
			print(' ISO: ' + str(iso))
			statusDictionary.update({'message': ' ISO: ' + str(iso)})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid ISO Setting! ' + str(iso))

# ------------------------------------------------------------------------------

def setExposure(input, wait = 0):
	global exposure
	global statusDictionary

	exposure = input
	try:	
		camera.exposure_mode = exposure
		print(' Exposure Mode: ' + exposure)
		statusDictionary.update({'message': ' Exposure Mode: ' + exposure})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Exposure Mode! ')
				
# ------------------------------------------------------------------------------

def setEV(input, wait = 0, displayMessage = True):
	global ev 
	global statusDictionary

	ev = input
	ev = int(ev)
	evPrefix = '+/-'
	if ev > 0:
		evPrefix = '+'
	elif ev < 0:
		evPrefix = ''
	try:
		camera.exposure_compensation = ev
		# print(str(camera.exposure_compensation) + '|' + str(ev))
		if displayMessage == True:
			print(' Exposure Compensation: ' + evPrefix + str(ev))
			statusDictionary.update({'message': ' Exposure Compensation: ' + evPrefix + str(ev)})
		time.sleep(wait)
		return
	except Exception as ex: 
		print(' WARNING: Invalid Exposure Compensation Setting! ')	
		
# ------------------------------------------------------------------------------				

def setAWB(input, wait = 0):
	global awb
	global statusDictionary

	awb = input
	try:	
		camera.awb_mode = awb
		print(' White Balance Mode: ' + awb)
		statusDictionary.update({'message': ' White Balance Mode: ' + awb})
		time.sleep(wait)
		return
	except Exception as ex:
		print(' WARNING: Invalid Auto White Balance Mode! ')

# ------------------------------------------------------------------------------

def getFileName(timestamped = True, isVideo = False):
	now = datetime.datetime.now()
	datestamp = now.strftime('%Y%m%d')
	timestamp = now.strftime('%H%M%S')		
			
	if isVideo==True:
		extension = '.h264'
		return datestamp + '-' + timestamp + extension
	else:
		extension = '.jpg'
		if timestamped == True:
			return datestamp + '-' + timestamp + '-' + str(imageCount).zfill(2) + extension
		else:
			return datestamp + '-' + str(imageCount).zfill(8) + extension

# ------------------------------------------------------------------------------

def getFilePath(timestamped = True, isVideo = False):
	try:
		os.makedirs(outputFolder, exist_ok = True)
	except OSError:
		print (' ERROR: Creation of the output folder ' + outputFolder + ' failed! ')
		echoOn()
		quit()
	else:
		return outputFolder + getFileName(timestamped, isVideo)

# ------------------------------------------------------------------------------

def captureImage(filepath, raw=False):
	camera.capture(filepath, quality=100, bayer=raw)
	if raw == True:
		conversionThread = threading.Thread(target=convertBayerDataToDNG, args=(filepath,))
		conversionThread.daemon = True
		conversionThread.start()

# ------------------------------------------------------------------------------		

def convertBayerDataToDNG(filepath):
	dng.convert(filepath)


# ------------------------------------------------------------------------------
def createControls():
	global running
	global statusDictionary	
	global buttonDictionary
	
	running = True
	server.startStream(camera, running, statusDictionary, buttonDictionary)
	
# -------------------------------------------------------------------------------
def darkMode():
	Light.off()
	

# === Image Capture ============================================================

controlsThread = threading.Thread(target=createControls)
controlsThread.daemon = True
controlsThread.start()


try:
	echoOff()
	imageCount = 1

	try:
		os.chdir('/home/pi') 
	except:
		pass
	
	def Capture():
		global shutter
		global shutterLong
		global shutterShort
		global iso
		global isoMin
		global isoMax
		global exposure
		global ev
		global evMin
		global evMax
		global awb
		global timer
		global raw
		global imageCount
		global statusDictionary
		global buttonDictionary
		global running
		

		# print(str(camera.resolution))
		

		print('\n Camera Stop ' + version )
		print('\n ----------------------------------------------------------------------')
		time.sleep(2)

		
		setShutter(shutter, 0)		
		setISO(iso, 0)
		setExposure(exposure, 0)
		setEV(ev, 0)
		setAWB(awb, 0)
		
		showInstructions(False, 0)
		
		while True:
			try:

				if buttonDictionary['exit'] == True:
					running = False
					darkMode()
					echoOn()
					camera.close()
					time.sleep(1.0)
					sys.exit(0)

				# Capture
				elif buttonDictionary['capture'] == True:
					
					# Normal photo
					filepath = getFilePath(True)
					print(' Capturing image: ' + filepath + '\n')
					captureImage(filepath, raw)
					imageCount += 1
					buttonDictionary.update({'capture': False})

				# Shutter Speed	
				elif buttonDictionary['shutterUp'] == True:
					if shutter == 0:
						shutter = shutterShort
					elif shutter > shutterShort and shutter <= shutterLong:					
						shutter = int(shutter / 1.5)
					setShutter(shutter, 0.25)
					buttonDictionary.update({'shutterUp': False})
				elif buttonDictionary['shutterDown'] == True:
					if shutter == 0:						
						shutter = shutterLong
					elif shutter < shutterLong and shutter >= shutterShort:					
						shutter = int(shutter * 1.5)
					elif shutter == shutterShort:
						shutter = 0
					setShutter(shutter, 0.25)
					buttonDictionary.update({'shutterDown': False})

				# ISO
				elif buttonDictionary['isoUp'] == True:
					if iso == 0:
						iso = isoMin
					elif iso >= isoMin and iso < isoMax:					
						iso = int(iso * 2)
					setISO(iso, 0.25)
					buttonDictionary.update({'isoUp': False})
				elif buttonDictionary['isoDown'] == True:
					if iso == 0:
						iso = isoMax
					elif iso <= isoMax and iso > isoMin:					
						iso = int(iso / 2)
					elif iso == isoMin:
						iso = 0
					setISO(iso, 0.25)
					buttonDictionary.update({'isoDown': False})

				# Exposure Compensation
				elif buttonDictionary['evUp'] == True:
					if ev >= evMin and ev < evMax:					
						ev = int(ev + 1)
						setEV(ev, 0.25)
						buttonDictionary.update({'evUp': False})
				elif buttonDictionary['evDown'] == True:
					if ev <= evMax and ev > evMin:					
						ev = int(ev - 1)
						setEV(ev, 0.25)
						buttonDictionary.update({'evDown': False})

			except Exception as ex:
				print(str(ex))
				pass

	Capture()

except KeyboardInterrupt:
	darkMode()
	echoOn()
	sys.exit(1)

# USAGE
# python ball_tracking.py --video ball_tracking_example.mp4
# python ball_tracking.py

# import the necessary packages
from collections import deque
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import numpy as np
import argparse
import serial
# import imutils
import cv2
import sys

print("Sending hello message over serial at 115200,n,8,1")
port = serial.Serial("/dev/serial0", baudrate=115200, timeout=0)
port.write("\r\nHi, this is Raspberry Pi\r\n")
port.write("Valid commands are BG?Q\r\n")
PY3 = sys.version_info[0] == 3

if PY3:
	xrange = range

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64,
	help="max buffer size")
args = vars(ap.parse_args())

#Horizontal
mode = 'G'

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
# greenLower = (28, 128, 6)
# greenUpper = (34, 255, 255)
greenLower = (59, 93, 61)
greenUpper = (69, 255, 218)
pts = deque(maxlen=args["buffer"])

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
camera.shutter_speed = 461	# microseconds
camera.awb_mode = 'sunlight'

rawCapture = PiRGBArray(camera, size=(640,480))
# allow the camera to warmup
time.sleep(0.1)
xOut=str
yOut=str

center1x=0.0
center1y=0.0
center2x=0.0
center2y=0.0
centerGearTarget=tuple

# loop forever (at least, until the q key is pressed)
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	
	gearBlobsFound = 0
	xOut = "000"
	yOut = "000"
	
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array

	# convert the frame to the HSV color space
	# blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	
	# find contours in the mask
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]

	#Look at all contours
	for c in cnts:
		
		#find rect and aspect ratio
		x, y, w, h = cv2.boundingRect(c)
		aspect = float(w)/h
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]),int(M["m01"] / M["m00"]))
		centerx = (int(M["m10"] / M["m00"]))
		centery = (int(M["m01"] / M["m00"]))
		
		if mode == 'G' and aspect >= 0.1 and aspect <= 0.6:
			cv2.circle(image, center, 5, (0, 0, 255), -1)
			cv2.circle(image, (x,y), 5, (0, 0, 255), -1)
			cv2.circle(image, (x,y), 5, (0, 0, 255), -1)
			cv2.circle(image, (x + w, y + h), 5, (0, 0, 255), -1)
			cv2.circle(image, (x + w, y), 5, (0, 0, 255), -1)
			cv2.circle(image, (x, y + h), 5, (0, 0, 255), -1)
			
			if gearBlobsFound == 0:
				center1x = centerx
				center1y = centery
				gearBlobsFound+=1
			elif gearBlobsFound == 1:
				center2x = centerx
				center2y = centery
				gearBlobsFound+=1
			elif gearBlobsFound>=2:
				print("Found more than 2 gear blobs")
				gearBlobsFound+=1

			centerGearTarget=(int((center1x + center2x)/2), int(((center1y + center2y)/2)))
			cv2.circle(image,centerGearTarget,5,(255,255,255),-1)

			xOut1 = format(centerx, '03d')
			yOut1 = format(centery, '03d')

		if mode == 'B' and aspect >= 1 and aspect <= 3:
			concaveX = x+(w/2)
			concaveY = y+(h*4/5)
			inOrOut = cv2.pointPolygonTest(c, (concaveX, concaveY), True)
			if inOrOut < 0:
				cv2.circle(image, (x,y), 5, (0, 0, 255), -1)
				cv2.circle(image, (x + w, y + h), 5, (0, 0, 255), -1)
				cv2.circle(image, (x + w, y), 5, (0, 0, 255), -1)
				cv2.circle(image, (x, y + h), 5, (0, 0, 255), -1)
				# print(x, y, w, h, aspect)
				# print(inOrOut)
				cv2.circle(image, (concaveX, concaveY),5, (255, 0, 0), -1)
				cv2.circle(image, center, 5, (0, 0, 255), -1)
				xOut2 = format(centerx, '03d')
				yOut2 = format(centery, '03d')
				#print (xOut+yOut)
		
	#print(gearBlobsFound)

	#port.write("\r\nHi, " +str(gearBlobsFound)+ "\r\n")

	# show the frame to our screen
	cv2.imshow("Frame", image)
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
 
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
	
	read = port.read()
	
	if read == 'B':
		print("Looking for boiler targe")
		mode = 'B'
		port.write (xOut2+yOut2+"\r\n")
		
	if read == 'G':
		print("Looking for gear target")
		mode = 'G'
		port.write(xOut1+yOut1+"\r\n")
		
	if key == ord("B"):
		mode = 'B'
		print(xOut2 + yOut2 + "\r\n")
		
	if key == ord("G"):
		mode = 'G'
		print(xOut1 + yOut1 + "\r\n")

	#if key == ord("A"):
        #        print(center1y - center2y)
#
 #       if key == ord("D"):
  #              print(center1x - (int(xOut1)))

# clean up camera resources and close any open windows
camera.close()
cv2.destroyAllWindows()

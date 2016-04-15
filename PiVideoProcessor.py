import time
import cv2
import sys, os, getopt
import numpy as np
import imutils
import serial
from PiVideoStream import PiVideoStream

from pymavlink import mavlink

#blue = {'lower' : (105, 80, 70), 'upper' : (125, 255, 255)}
#orange = {'lower' : (0, 70, 70), 'upper' : (12, 255, 255)}
#purple = {'lower' : (130, 70, 50), 'upper' : (145, 255, 255)}
#neon = {'lower' : (20, 30, 50), 'upper' : (38, 180, 255)}

def parse_args(argv):
   params = {'method' : 'color', 'xRes' : 400, 'yRes' : 200,
      'capTime' : 0, 'preview' : False, 'sendToPX4' : False,
      'debug' : False}

   try:
      opts, args = getopt.getopt(argv, 'm:t:h:w:pds')
   except getopt.GetoptError:
      print 'Error with arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == "-h" and int(arg) > 0:
         params['yRes'] = int(arg)
      elif opt == "-w" and int(arg) > 0:
         params['xRes'] = int(arg)
      elif opt == "-p":
         params['preview'] = True
      elif opt == "-t" and int(arg) > 0:
         params['capTime'] = int(arg) 
      elif opt == "-m": 
         if arg != "hough" and arg != "color" and arg != "orb":
            print "Not a valid method. Use hough or color"
            sys.exit(1)
         params['method'] = arg
      elif opt == "-s":
         params['sendToPX4'] = True
      elif opt == "-d":
         params['debug'] = True
   return params

def findBallColor(frame, color, preview):
   lower = color['lower']
   upper = color['upper']
   found = False
   center = None
   radius = 0

   #blur = cv2.GaussianBlur(frame, (5,5), 0)
   #Convert color space
   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

   #Find colors within range
   mask = cv2.inRange(hsv, lower, upper)

   #perform morphological opening
   mask = cv2.erode(mask, None, iterations=1)
   mask = cv2.dilate(mask, None, iterations=1);

   #Find contours within image
   cnts = cv2.findContours(mask.copy(), 
      cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

   (x, y) = (0, 0)

   if len(cnts) > 0:
      #Find largest contour
      c = max(cnts, key=cv2.contourArea)

      #Match contour to circle
      ((x, y), radius) = cv2.minEnclosingCircle(c)
      M = cv2.moments(c)
      if M["m00"] != 0: 
         center = (int(M["m10"] / M["m00"]), 
            int(M["m01"] / M["m00"]))

         #Only accept circle if it is large enough
         if radius > 6:
            found = True

            if preview:
               cv2.circle(frame, (int(x), int(y)),
                  int(radius), (0, 255, 255), 2)
   
   return found, (x,y), radius

def findBallHough(frame):
   #Convert color to grayscale
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

   #Perform Hough Circles algorithm
   circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp = 3, minDist=100, \
                              param1=50, param2=50, minRadius=10, maxRadius=200)
   circles = np.uint16(np.around(circles))

   #Find largest circle
   for i in circles[0,0:1]:
      cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)

def findChessORB(frame, orb, kp, des, template):
   #find keypoints for new frame
   kp2, des2 = orb.detectAndCompute(frame, None)

   #use brute force matching
   bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
   matches = bf.match(des, des2)
   matches = sorted(matches, key = lambda x:x.distance)

   found = frame
   #There is a match if there is at least 10 matches and the distance of the 
   # furthest one is not too far
   if len(matches) > 10 and matches[9].distance < 60:
      found = cv2.drawMatches(template, kp, frame, kp2, matches[:10], outImg=None, flags=2)
   return found

def calibrateColor(frame, yRes):
   # Use Hough Circles to find ball. Histogram the ball to find the most prominent
   # color. Use that color to set the color to find.

   # Gray Scale it and blur it
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   blur = cv2.GaussianBlur(gray, (9, 9), 1)

   maxR = int(.6 * yRes)
   minR = int(.3 * yRes)
    
   # Perform Hough Circles algorithm
   circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp = 2, minDist=200, \
                              param1=30, param2=50, minRadius=minR, maxRadius=maxR)
   if circles is not None:
      circles = np.uint16(np.around(circles))
   else:
      print "Color Calibration failed"
      sys.exit(1)

   # Find largest circle
   loc = circles[0, 0]
   (y, x, z) = frame.shape

   # Create Mask for Histogram. Ignore all data that isnt the found ball
   mask = np.zeros((y, x), dtype=np.uint8)
   cv2.circle(mask, (loc[0], loc[1]), loc[2], (255, 255, 255), -1)

   # Convert to HSV and histogram the Hue values
   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
   hue_histr = cv2.calcHist([hsv], [0], mask, [180], [0, 180])
   sat_histr = cv2.calcHist([hsv], [1], mask, [256], [0, 256])
   val_histr = cv2.calcHist([hsv], [2], mask, [256], [0, 256])

   sat_avg = np.average(sat_histr)
   print sat_avg

   sat_min = sat_avg - 40
   if sat_min < 10:
      sat_min = 10

   sat_max = sat_avg + 40
   if sat_max > 255:
      sat_max = 255

   val_avg = np.average(val_histr)
   print val_avg

   val_min = val_avg - 40
   if val_min < 10:
      val_min = 10

   val_max = val_avg + 40
   if val_max > 255:
      val_max = 255


   max = np.argmax(hue_histr)

   if max < 8 or max > 277:
      return None
   
   color = {'lower' : (max - 8, sat_min, val_min), 'upper' : (max + 8, sat_max, val_max)}
   return color


def main():
   params = parse_args(sys.argv[1:]) 
   
   #Start up Video processing thread
   vs = PiVideoStream(resolution=(params['xRes'], params['yRes'])).start()

   #Wait for camera to warm up
   time.sleep(2.0)

   windowName = 'Frame'

   if params['method'] == 'color':
      color = calibrateColor(vs.read(), params['yRes']) 
      if color == None:
         vs.stop()
         sys.exit(1)

   
   #Used for calculating FPS
   startTime = time.time()
   if params['capTime'] == 0:
      endTime = startTime + 1000000000
   else:
      endTime = startTime + params['capTime']
   frames = 0

   #Startup code for ORB method
   if params['method'] == 'orb':
      orb = cv2.ORB_create()
      template = cv2.imread('training/checkerboard.jpg', 0)
      kp, des = orb.detectAndCompute(template, None)

   if params['sendToPX4']:
      port = serial.Serial('/dev/ttyAMA0', 57600)
      mav = mavlink.MAVLink(port)

   while time.time() < endTime:
      frames += 1
      frame = vs.read()

      #Find object based on method
      if params['method'] == 'color':
         found, (x,y), radius = findBallColor(frame, color, params['preview'])
         if found:
            loc = 2.0 * x / params['xRes'] - 1;

            if params['sendToPX4']:
               message = mavlink.MAVLink_duck_leader_loc_message(loc, 5.0)
               mav.send(message)

            if params['debug'] :
               print str(time.time() - startTime) + ", " + str(loc)           

      elif params['method'] == 'hough':
         findBallHough(frame)
      elif params['method'] == 'orb':
         frame = findChessORB(frame, orb, kp, des, template)
      if params['preview']:
         frame = imutils.resize(frame, width=400)
         cv2.imshow(windowName, frame)

      key = cv2.waitKey(1) & 0xFF
      if (key == ord("q")):
         break;
      
   totalTime = time.time() - startTime
   cv2.destroyAllWindows()

   vs.stop()

   print "Average main FPS: " + str(float(frames) / totalTime) + "fps"

if __name__ == "__main__":
   main()

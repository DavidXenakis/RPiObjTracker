import time
import cv2
import sys, os, getopt
import numpy as np
import imutils
import serial
import FindingFuncs
from PiVideoStream import PiVideoStream
from pymavlink import mavlink
from KalmanFilter import KalmanFilter

def parse_args(argv):
   params = {'xRes' : 600, 'yRes' : 450,
      'capTime' : 0, 'preview' : False, 'sendToPX4' : False,
      'debug' : False, 'file' : None}

   try:
      opts, args = getopt.getopt(argv, 'f:t:w:pds')
   except getopt.GetoptError:
      print 'Error with arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == "-w" and int(arg) > 0:
         params['xRes'] = int(arg)
         params['yRes'] = int(.75 * int(arg))
      elif opt == "-p":
         params['preview'] = True
      elif opt == "-t" and int(arg) > 0:
         params['capTime'] = int(arg) 
      elif opt == "-s":
         params['sendToPX4'] = True
      elif opt == "-d":
         params['debug'] = True
      elif opt == "-f":
         params['file'] = arg
   return params

def check_params(params):
   if params['file'] == None:
      print "Please specify a template file for those patterns"
      print "Place that template file in the 'training' folder"
      sys.exit(1)

   return params

def read_template(params):
   template = cv2.imread(params['file'], cv2.IMREAD_GRAYSCALE)
   if template is None:
      print "Could not open file"
      sys.exit(1)

   return template

def init_surf():
   # This number affects how many keypoints are found. 
   # Higher number -> Fewer keypoints -> Worse detection, higher performance
   # and vice versa
   surf = cv2.xfeatures2d.SURF_create(1500)

   FLANN_INDEX_KDTREE = 0
   index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
   search_params = dict(checks=50)

   flann = cv2.FlannBasedMatcher(index_params, search_params)

   return surf, flann

def boundFloat(val, low, high):
   if val < low:
      return low
   if val > high:
      return high
   return val

def main():
   params = check_params(parse_args(sys.argv[1:]))
   kf = KalmanFilter()

   if params['file']:
      template = read_template(params)

   surf, flann = init_surf()
   kp, des = surf.detectAndCompute(template, None)

   #Start up Video processing thread
   vs = PiVideoStream(resolution=(params['xRes'], params['yRes'])).start()

   #Wait for camera to warm up
   time.sleep(3.0)

   #Used for calculating FPS
   startTime = time.time()
   if params['capTime'] == 0:
      endTime = startTime + 1000000000
   else:
      endTime = startTime + params['capTime']
   frames = 0

   # Open up serial port with Pixhawk
   if params['sendToPX4']:
      port = serial.Serial('/dev/ttyAMA0', 57600)
      mav = mavlink.MAVLink(port)

   # Typically only need to search within a small Y-range
   yRes = params['yRes']
   (cropYmin, cropYmax) = (yRes * .25, yRes * .70)

   #Take weighted average of last # of distances to filter out noise
   notFoundCount = 1000

   while time.time() < endTime:
      frames += 1
      frame = vs.read()
      frame = frame[cropYmin : cropYmax, 0:params['xRes']]

      found, [x,y], frame = FindingFuncs.findPatternSURF(frame, surf, kp, des, template, flann, params['preview'])

      # Count how many frames it has been since the RPi has not found anything
      if not found:
         notFoundCount += 1
      else:
         notFoundCount = 0
         kf.update(x)

      # How many frames until you assume to keep going straight.
      if notFoundCount > 100:
         kf.reset()
         x = params['xRes'] / 2
      else:      
         x = kf.predict()

      loc = boundFloat(2.0 * x / params['xRes'] - 1, -1., 1.)

      if params['sendToPX4']:
         message = mavlink.MAVLink_duck_leader_loc_message(loc, 5.0)
         mav.send(message)

      if params['debug'] :
         print str(time.time() - startTime) + ", " + str(loc)

      if params['preview']:
         # Draw a circle on frame where the Kalman filter predicts.
         cv2.circle(frame, (int(x), 10), 4, (0, 0, 255), 6)

         frame = imutils.resize(frame, width=1000)
         cv2.imshow("Preview", frame)

      #Check for keypress, ending if Q is entered
      key = cv2.waitKey(1) & 0xFF
      if (key == ord("q")):
         break;
      
   totalTime = time.time() - startTime
   cv2.destroyAllWindows()

   vs.stop()

   print "Average main FPS: " + str(float(frames) / totalTime) + "fps"

if __name__ == "__main__":
   main()

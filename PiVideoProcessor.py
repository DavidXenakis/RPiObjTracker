import time
import cv2
import sys, os, getopt
import numpy as np
import imutils
import serial
import FindingFuncs
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
         (x,y), frame = FindingFuncs.findBallColor(frame, color, params['preview'])
         if found:
            loc = 2.0 * x / params['xRes'] - 1;

            if params['sendToPX4']:
               message = mavlink.MAVLink_duck_leader_loc_message(loc, 5.0)
               mav.send(message)

            if params['debug'] :
               print str(time.time() - startTime) + ", " + str(loc)           

      elif params['method'] == 'hough':
         FindingFuncs.findBallHough(frame)
      elif params['method'] == 'orb':
         frame = FindingFuncs.findChessORB(frame, orb, kp, des, template)
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

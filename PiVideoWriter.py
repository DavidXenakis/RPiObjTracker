import time
import threading
import numpy as np
import imutils
import cv2
import sys, os, getopt
import datetime
from PiVideoStream import PiVideoStream

def parse_args(argv):
   params = {'x' : 350, 'y' : 250, 'fps' : 10,
      'capTime' : 10, 'preview' : False}
   try:
      opts, args = getopt.getopt(argv, 'x:y:f:t:')
   except getopt.GetoptError:
      print 'Error in arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == '-x' and int(arg) > 0:
         params['x'] = int(arg)
      elif opt == '-y' and int(arg) > 0:
         params['y'] = int(arg)
      elif opt == '-t' and int(arg) > 0:
         params['capTime'] = int(arg)
      elif opt == '-f' and int(arg) > 0:
         params['fps'] = int(arg)
      elif opt == '-p':
         params['preview'] = True
   return params

def main():
   params = parse_args(sys.argv[1:])

   vs = PiVideoStream(resolution=(params['x'], params['y'])).start()
   time.sleep(2.0)

   freq = 1. / params['fps']
   numFrames = params['capTime'] * params['fps']

   date = datetime.datetime.now().isoformat()[:-7]
   name = "/home/pi/RPiObjTracker/videos/Video_" + date + ".avi"
   fourcc = cv2.VideoWriter_fourcc(*'XVID')
   vw = cv2.VideoWriter(name, fourcc, params['fps'], (params['x'], params['y']), True)

   last = 0

   for i in range(numFrames):
      while time.time() - last < freq:
         time.sleep(.001)
      last = time.time()
      frame = vs.read()
      vw.write(frame)
      if params['preview']:
         cv2.imshow('frame', frame)
         cv2.waitKey(1)

   vs.stop()
   vw.release()
   cv2.destroyAllWindows()

if __name__ == "__main__":
   main()

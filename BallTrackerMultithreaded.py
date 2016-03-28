from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import io
import threading
import time
import cv2
import sys, getopt

blueLower = (110, 50, 50)
blueUpper = (130, 255, 255)

#Default params
height   = 360
width    = 480
capTime  = 10
preview  = False
method   = "color"

#Create a pool of image processors
done = False
lock = threading.Lock()
pool = []

frames = 0

startTime = None
endTime = None
cam = None

class ImageProcessor(threading.Thread):
   def __init__(self):
      super(ImageProcessor, self).__init__()
      self.stream = PiRGBArray(cam, size=(width, height))
      self.event = threading.Event()
      self.terminated = False
      self.start()

   def run(self):
      global done
      while not self.terminated:
         if self.event.wait(1):
            try:
               #IMPLEMENT PROCESSING
               frame = self.stream.array

               if method == "color":
                  foundBall = findBallColor(frame)
               elif method == "hough":
                  foundBall = findBallHough(frame)

               if preview:
                  cv2.imshow("frame", frame)

            finally:
               self.stream.truncate(0)
               self.event.clear()
               with lock:
                  pool.append(self)

def findBallHough(frame):
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, \
                              param1=50, param2=30, minRadius=0, maxRadius=0)
#   circles = np.uint16(np.around(circles))
   if circles != None:
      return True
   return False


def findBallColor(frame):
   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

   mask = cv2.inRange(hsv, blueLower, blueUpper)
   mask = cv2.erode(mask, None, iterations=1)
   mask = cv2.dilate(mask, None, iterations=1);

   cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
   center = None

   if len(cnts) > 0:
      c = max(cnts, key=cv2.contourArea)
      ((x, y), radius) = cv2.minEnclosingCircle(c)
      M = cv2.moments(c)
      center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

      if radius > 10:
         cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
         return True
   return False

def streams():
   global frames
   while not done and time.time() < endTime:
      with lock:
         if pool:
            processor = pool.pop()
         else:
            processor = None
      if processor:
         frames += 1
         yield processor.stream
         processor.event.set()
      else:
         time.sleep(0.1)

def parse_args(argv):
   global height
   global width
   global preview
   global capTime
   global method

   try:
      opts, args = getopt.getopt(argv, 'm:t:h:w:p')
   except getopt.GetoptError:
      print 'Error with arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == "-h" and int(arg) > 0:
         height = int(arg)
      elif opt == "-w" and int(arg) > 0:
         width = int(arg)
      elif opt == "-p":
         preview = True
      elif opt == "-t":
         capTime = int(arg) 
      elif opt == "-m": 
         if arg != "hough" and arg != "color":
            print "Not a valid method. Use hough or color"
            sys.exit(1)
         method = arg

   
def main():
   global frames
   global pool
   global cam
   global startTime
   global endTime
   
   with PiCamera() as cam:
      parse_args(sys.argv[1:])
      pool = [ImageProcessor() for i in range(4)]
      cam.resolution = (width, height)
      cam.framerate = 60
      cam.rotation = -90

      #cam.start_preview()
      time.sleep(2)
      startTime = time.time()
      endTime = startTime + capTime
      cam.capture_sequence(streams(), format="bgr", use_video_port=True)

   print 'Average Framerate for ' + str(frames) + \
      ' frames was: ' + str(float(frames) / capTime) + 'fps'

   while pool:
      with lock:
         processor = pool.pop()
      processor.terminated = True
      processor.join()
   
if __name__ == "__main__":
   main()

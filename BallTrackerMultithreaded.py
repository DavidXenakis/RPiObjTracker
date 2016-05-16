from picamera.array import PiRGBArray
from PiVideoStream import PiVideoStream
from picamera import PiCamera
import FindingFuncs
import numpy as np
import io
import threading
import time
import cv2
import sys, getopt
import serial
from Queue import Queue
from pymavlink import mavlink

color = None

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
mav = None

frameQueue = Queue()
locQueue = Queue()

class ImageProcessor(threading.Thread):
   def __init__(self, method, lQ, fQ):
      super(ImageProcessor, self).__init__()
      self.stream = PiRGBArray(cam, size=(width, height))
      self.event = threading.Event()
      self.terminated = False
      self.method = method
      self.locQueue = lQ
      self.frameQueue = fQ
      self.start()


   def run(self):
      global done
      while not self.terminated:
         if self.event.wait(1):
            try:
               frame = self.stream.array
               frame = frame[height * .25 : height * .65, 0:width]
               found, (x, y), frame = self.method(frame, color, preview)
               if found:
                  loc = 2.0 * x / width - 1;
                  self.locQueue.put(loc)
                  if preview:
                     self.frameQueue.put(frame)

            finally:
               self.stream.truncate(0)
               self.event.clear()
               with lock:
                  pool.append(self)

def processQueues():
   try:
      loc = locQueue.get_nowait()
      sendLocToPX4(loc)
      print loc
      #sys.stdout.flush()
      locQueue.task_done()
   except:
      loc = None

   if preview:
      try:
         frame = frameQueue.get_nowait()
         cv2.imshow("Frame", frame)
         key = cv2.waitKey(1) & 0xFF
         frameQueue.task_done()
      except:
         frame = None

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
         time.sleep(0.01)
      processQueues()

def parse_args(argv):
   global height
   global width
   global preview
   global capTime
   global method

   try:
      opts, args = getopt.getopt(argv, 'm:t:w:p')
   except getopt.GetoptError:
      print 'Error with arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == "-w" and int(arg) > 0:
         width = int(arg)
         height = int(.75 * width)
      elif opt == "-p":
         preview = True
      elif opt == "-t":
         capTime = int(arg) 
      elif opt == "-m": 
         if arg != "hough" and arg != "color":
            print "Not a valid method. Use hough or color"
            sys.exit(1)
         method = arg

def sendLocToPX4(loc):
   message = mavlink.MAVlink_duck_leader_loc_message(loc, 4.0)
   print "Sending message"
   mav.send(message)

def createMAVLink(): 
   port = serial.Serial('/dev/ttyAMA0', 57600)
   return mavlink.MAVLink(port)

def main():
   global frames
   global pool
   global cam
   global startTime
   global endTime
   global color
   global mav

   method = FindingFuncs.findBallColor 
   mav = createMAVLink()

   vs = PiVideoStream(resolution=(width, height)).start()
   time.sleep(2.0)
   color = FindingFuncs.calibrateColor(vs.read(), height) 
   vs.stop()
   time.sleep(.1)
   
   with PiCamera() as cam:
      parse_args(sys.argv[1:])
      pool = [ImageProcessor(method, locQueue, frameQueue) for i in range(4)]
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

import time
import threading
import numpy as np
import imutils
import cv2
import sys, os, getopt
import datetime
from PiVideoStream import PiVideoStream

vs = PiVideoStream(resolution=(350, 250)).start()
time.sleep(2.0)

fps = 20

date = datetime.datetime.now().isoformat()
name = "/home/pi/RPiObjTracker/Video_" + date + ".avi"
fourcc = cv2.VideoWriter_fourcc(*'XVID')
vw = cv2.VideoWriter(name, fourcc, fps, (350, 250), True)

freq = 1. / 20
last = 0

for i in range(100):
   while time.time() - last < freq:
      time.sleep(.001)
   last = time.time()
   frame = vs.read()
   vw.write(frame)
   cv2.imshow('frame', frame)
   cv2.waitKey(1)
   


vs.stop()
vw.release()
cv2.destroyAllWindows()


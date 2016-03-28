import cv2
from threading import Thread
from imutils.video import FPS

class PiBallFinder:
   def __init__(self, vs, hueLow=110, hueHigh=120):
      self.vs = vs
      self.lower = (hueLow, 64, 128)
      self.upper = (hueHigh, 255, 255)
      self.found = False
      self.center = None
      self.newFrame = None
      self.stopped = False
      self.fps = FPS().start()

   def start(self):
      Thread(target = self.findBall, args=()).start()
      return self
   
   def findBall(self):
      while not self.stopped:
         frame = self.vs.read()
         self.found = False
         self.center = None

         hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

         mask = cv2.inRange(hsv, self.lower, self.upper)
         mask = cv2.erode(mask, None, iterations=1)
         mask = cv2.dilate(mask, None, iterations=1);

         cnts = cv2.findContours(mask.copy(), 
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

         if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            if M["m00"] != 0: 
               self.center = (int(M["m10"] / M["m00"]), 
                  int(M["m01"] / M["m00"]))

               if radius > 10:
                  self.found = True
                  cv2.circle(frame, (int(x), int(y)),
                     int(radius), (0, 255, 255), 2)
         self.newFrame = frame
         self.fps.update()
      

   def read(self):
      return self.found, self.center, self.newFrame

   def stop(self):
      self.fps.stop()
      self.stopped = True

   def getFPS(self):
      return self.fps.fps()
      



import cv2
import numpy as np
import time

class PiVideoReader:
   def __init__(self, filename):
      self.filename = filename
      self.cap = cv2.VideoCapture(self.filename)
      self.fps = self.cap.get(cv2.CAP_PROP_FPS)
      self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
      self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
      self.stopped = False
      self.lastTime = 0

   def read(self):
      ret, frame = self.cap.read()
      if frame is None:
         self.stop() 
      return frame

   def getWH(self):
      return (self.width, self.height)

   def stop(self):
      self.stopped = True
      self.cap.release()
      return

   def getFPS(self):
      return self.fps 

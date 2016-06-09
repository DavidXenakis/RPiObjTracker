# This class opens up a connection to the RPi Camera.
# This connection runs in a separate thread to reduce
# I/O impact on the image processing thread.

from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
from imutils.video import FPS
import cv2

class PiVideoStream:
   def __init__(self, resolution=(400,200), framerate=60):

      #Start up camera
      self.camera = PiCamera()
      self.camera.resolution = resolution
      self.camera.framerate = framerate
      self.camera.rotation = -90
      self.rawCap = PiRGBArray(self.camera, size=resolution)
      self.stream = self.camera.capture_continuous(self.rawCap,
         format="bgr", use_video_port=True)

      self.frame = None
      self.stopped = False
      self.fps = FPS().start()

   def start(self):
      Thread(target=self.update, args=()).start()
      return self

   def update(self):
      # Continually grab frames from camera
      for f in self.stream:
         self.frame = f.array
         self.rawCap.truncate(0)
         self.fps.update()

         if self.stopped:
            self.stream.close()
            self.rawCap.close()
            self.camera.close()
            return

   def read(self):
      return self.frame

   def stop(self):
      self.fps.stop()
      self.stopped = True

   def getFPS(self):
      return self.fps.fps()

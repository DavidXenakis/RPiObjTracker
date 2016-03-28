from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import sys, getopt

height   = 480
width    = 360
capTime  = 10
preview  = False

def parse_args(argv):
   global height
   global width
   global preview
   global capTime
   try:
      opts, args = getopt.getopt(argv, 't:h:w:p')
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
   
def main():
   global preview

   parse_args(sys.argv[1:])
   cam = PiCamera()
   cam.rotation = -90
   cam.resolution = (width, height)
   cam.framerate = 60
   rawCapture = PiRGBArray(cam, size=(width, height))

   startTime = time.time()
   endTime = time.time() + capTime
   frames = 0

   for image in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      if image is None:
         print 'capture failed'
         break
      frames += 1
      frame = image.array

      if preview: 
         cv2.imshow("frame", frame)
         key = cv2.waitKey(1) & 0xFF


      if time.time() > endTime:
         break
      rawCapture.truncate(0)

   print "Average Framerate for " + str(frames) + \
      " frames was: " + str(float(frames) / capTime) + "fps"
   cv2.destroyAllWindows()

   
if __name__ == "__main__":
   main()

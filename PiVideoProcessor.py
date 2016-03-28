import time
import cv2
import sys, getopt
import numpy as np
import imutils
from PiVideoStream import PiVideoStream

blue = {'lower' : (105, 80, 70), 'upper' : (125, 255, 255)}
orange = {'lower' : (0, 70, 70), 'upper' : (12, 255, 255)}
purple = {'lower' : (130, 70, 50), 'upper' : (145, 255, 255)}
neon = {'lower' : (18, 50, 20), 'upper' : (32, 255, 255)}

colors = {
   'blue'    : blue,
   'orange'  : orange, 
   'purple'  : purple,
   'neon'    : neon
}

def parse_args(argv):
   params = {'method' : 'color', 'xRes' : 400, 'yRes' : 200,
      'capTime' : 10, 'preview' : False, 'color' : 'blue'}

   try:
      opts, args = getopt.getopt(argv, 'c:m:t:h:w:p')
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
      elif opt == "-c":
         if arg != "blue" and arg != "purple" \
            and arg != "orange" and arg != "neon":
            print "Not a valid color. Use blue, purple, orange, or neon"
            sys.exit(1)
         params['color'] = arg
      elif opt == "-m": 
         if arg != "hough" and arg != "color" and arg != "orb":
            print "Not a valid method. Use hough or color"
            sys.exit(1)
         params['method'] = arg
   return params

def findBallColor(frame, color):
   lower = color['lower']
   upper = color['upper']
   found = False
   center = None
   radius = 0

   #blur = cv2.GaussianBlur(frame, (5,5), 0)
   #Convert color space
   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

   #Find colors within range
   mask = cv2.inRange(hsv, lower, upper)

   #perform morphological opening
   mask = cv2.erode(mask, None, iterations=1)
   mask = cv2.dilate(mask, None, iterations=1);

   #Find contours within image
   cnts = cv2.findContours(mask.copy(), 
      cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

   if len(cnts) > 0:
      #Find largest contour
      c = max(cnts, key=cv2.contourArea)

      #Match contour to circle
      ((x, y), radius) = cv2.minEnclosingCircle(c)
      M = cv2.moments(c)
      if M["m00"] != 0: 
         center = (int(M["m10"] / M["m00"]), 
            int(M["m01"] / M["m00"]))

         #Only accept circle if it is large enough
         if radius > 6:
            found = True

            cv2.circle(frame, (int(x), int(y)),
               int(radius), (0, 255, 255), 2)
   
   return found, center, radius

def findBallHough(frame):
   #Convert color to grayscale
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

   #Perform Hough Circles algorithm
   circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp = 3, minDist=100, \
                              param1=50, param2=50, minRadius=10, maxRadius=200)
   circles = np.uint16(np.around(circles))

   #Find largest circle
   for i in circles[0,0:1]:
      cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)

def findChessORB(frame, orb, kp, des, template):
   #find keypoints for new frame
   kp2, des2 = orb.detectAndCompute(frame, None)

   #use brute force matching
   bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
   matches = bf.match(des, des2)
   matches = sorted(matches, key = lambda x:x.distance)

   found = frame
   #There is a match if there is at least 10 matches and the distance of the 
   # furthest one is not too far
   if len(matches) > 10 and matches[9].distance < 60:
      found = cv2.drawMatches(template, kp, frame, kp2, matches[:10], outImg=None, flags=2)
   return found

def main():
   params = parse_args(sys.argv[1:]) 
   
   #Start up Video processing thread
   vs = PiVideoStream(resolution=(params['xRes'], params['yRes'])).start()

   #Wait for camera to warm up
   time.sleep(2.0)

   windowName = 'Frame'
   
   #Used for calculating FPS
   startTime = time.time()
   endTime = startTime + params['capTime']
   frames = 0

   #Startup code for ORB method
   if params['method'] == 'orb':
      orb = cv2.ORB_create()
      template = cv2.imread('training/checkerboard.jpg', 0)
      kp, des = orb.detectAndCompute(template, None)

   while time.time() < endTime:
      frames += 1
      frame = vs.read()

      #Find object based on method
      if params['method'] == 'color':
         color = colors.get(params['color'], blue)
         found, center, radius = findBallColor(frame, color)
      elif params['method'] == 'hough':
         findBallHough(frame)
      elif params['method'] == 'orb':
         frame = findChessORB(frame, orb, kp, des, template)
      if params['preview']:
         frame = imutils.resize(frame, width=400)
         cv2.imshow(windowName, frame)
         key = cv2.waitKey(1) & 0xFF
      
   cv2.destroyAllWindows()

   vs.stop()

   print "Average main FPS: " + str(float(frames) / params['capTime']) + "fps"

if __name__ == "__main__":
   main()

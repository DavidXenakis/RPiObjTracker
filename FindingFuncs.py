import cv2
import imutils
import math
import numpy as np
from Queue import Queue
from KalmanFilter import KalmanFilter

kf = KalmanFilter()

def findBallColor(frame, color, preview):
   lower = color['lower']
   upper = color['upper']
   found = False
   center = None
   radius = 0

   blur = cv2.GaussianBlur(frame, (5,5), 1)
   #Convert color space
   hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

   #Find colors within range
   mask = cv2.inRange(hsv, lower, upper)

   #perform morphological opening
   mask = cv2.erode(mask, None, iterations=1)
   mask = cv2.dilate(mask, None, iterations=1);

   #Find contours within image
   cnts = cv2.findContours(mask.copy(), 
      cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

   [x, y]= [None, None]

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

            if preview:
               cv2.circle(frame, (int(x), int(y)),
                  int(radius), (0, 255, 255), 2)
   
   return found, [x,y], frame

def findPatternORB(frame, orb, kp, des, template, preview):
   #find keypoints for new frame
   kp2, des2 = orb.detectAndCompute(frame, None)
   found = False
   x, y = 0, 0

   #use brute force matching
   bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
   matches = bf.match(des, des2)
   matches = sorted(matches, key = lambda x:x.distance)

   #There is a match if there is at least 10 matches and the distance of the 
   # furthest one is not too far
   if len(matches) > 6 and matches[6].distance < 50:
      found = True
      frame = cv2.drawMatches(template, kp, frame, kp2, matches[:6], outImg=None, flags=2)
   return found, (x, y), frame


def findPatternSURF(frame, surf, kp, des, template, flann, preview):
   f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   #f = cv2.GaussianBlur(f, (3,3), 0)
   kp2, des2 = surf.detectAndCompute(f, None)

   found = False
   xLoc, yLoc, dev = 0, 0, 0
   
   if des is not None and des2 is not None and \
      len(des) >= 2 and len(des2) >= 2:

      # Number of matches is the number of keypoints in template image
      matches = flann.knnMatch(des, des2, k=2)
      matchesMask = [[0,0] for i in xrange(len(matches))]

      queryDMatches = []
      
      for i, (m, n) in enumerate(matches):
         if m.distance < .9 * n.distance:
            matchesMask[i] = [1, 0]
            queryDMatches.append(m)

      #This glorious algorithm gets rid of matches that have the same xvalue in query image
      # This usually corresponds to places that are not matches
      queryDMatches = [x for x in queryDMatches if \
         sum(kp2[x.trainIdx].pt[0] == kp2[y.trainIdx].pt[0] for y in queryDMatches) == 1]


      #Sort the matches based on the best distance
      if len(queryDMatches) >= 4:
         found = True
         
         num = int(len(queryDMatches) * 1)
         #Sort the coordinates to only find best matches
         queryDMatches = sorted(queryDMatches, key = lambda x: x.distance)[:num]

         #extract the x and y coordinates
         xCoords = map((lambda match: kp2[match.trainIdx].pt[0]), queryDMatches)
         yCoords = map((lambda match: kp2[match.trainIdx].pt[1]), queryDMatches)

         xCoords = filterOutliers(xCoords, 1.2)
         yCoords = filterOutliers(yCoords, 1.2)
      
         if len(xCoords) != 0 and len(yCoords) != 0:
            xLoc = sum(xCoords) / len(xCoords)
            yLoc = sum(yCoords) / len(yCoords)

                           #draw_params = dict(matchColor = (255, 255, 0),
               #                   singlePointColor = (255, 0, 0),
               #                   matchesMask = matchesMask,
               #                   flags = 0)
               #frame = cv2.drawMatchesKnn(template, kp, frame, kp2, matches, None, **draw_params)

   if xLoc != 0:
      kf.update(xLoc)
   xLoc = kf.predict()

   if preview:
      cv2.circle(frame, (int(xLoc), 10), 4, (0, 255, 255), 6)
      #for x,y in zip(xCoords, yCoords):
      #   cv2.circle(frame, (int(y), int(x)), 2, (255, 0, 255), 3)


   return found, [xLoc, yLoc, dev], frame

def filterOutliers(array, numStdDev = 1.5):
   npArray = np.array(array)
   stdDev = np.std(npArray)
   mean = np.mean(npArray)
   return [x for x in array if abs(x - mean) < numStdDev * stdDev]

class DistanceSmoother(object):
   def __init__(self, size):
      self.size = size
      # choose large value for this because we want default behavior to assume to slow down
      # If update returns large numbers, it means you are close to vehicle.
      # This will make the vehicle slow down.
      self.readings = [100] * size
      self.weights = map(lambda x: math.sqrt(x), range(self.size+1)[1:])
      self.weights = map(lambda y: float(y) / sum(self.weights), self.weights)
      self.current = 100

   # Call this with each new reading to get smoothed reading
   def update(self, reading):
      self.readings.append(reading)
      self.readings = self.readings[1:]
      s = 0
      for (w,r) in zip(self.weights, self.readings):
         s += w * r
      self.current = s
      return s

   def get(self):
      return self.current

   # Call this if you finding algorithm returns false many consecutive times
   def reset(self):
      self.readings = [100] * self.size
      self.current = 100

def calibrateColor(frame, yRes):
   # Use Hough Circles to find ball. Histogram the ball to find the most prominent
   # color. Use that color to set the color to find.

   # Gray Scale it and blur it
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   blur = cv2.GaussianBlur(gray, (9, 9), 1)

   maxR = int(.6 * yRes)
   minR = int(.3 * yRes)
    
   # Perform Hough Circles algorithm
   circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp = 2, minDist=200, \
                              param1=30, param2=50, minRadius=minR, maxRadius=maxR)
   if circles is not None:
      circles = np.uint16(np.around(circles))
   else:
      print "Color Calibration failed"
      sys.exit(1)

   # Find largest circle
   loc = circles[0, 0]
   (y, x, z) = frame.shape

   # Create Mask for Histogram. Ignore all data that isnt the found ball
   mask = np.zeros((y, x), dtype=np.uint8)
   cv2.circle(mask, (loc[0], loc[1]), loc[2], (255, 255, 255), -1)

   # Convert to HSV and histogram the Hue values
   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
   hue_histr = cv2.calcHist([hsv], [0], mask, [180], [0, 180])

   max = np.argmax(hue_histr)

   if max < 8 or max > 277:
      return None
   
   color = {'lower' : (max - 8, 40, 40), 'upper' : (max + 8, 255, 255)}
   cv2.circle(frame, (loc[0], loc[1]), loc[2], (0, 255, 255), 2)
   return color



import cv2
import imutils
import numpy as np

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
   
   return [x,y], frame

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



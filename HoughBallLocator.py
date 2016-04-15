import time
from matplotlib import pyplot as plt
import cv2
import sys, os, getopt
import numpy as np
import imutils
import serial
from PiVideoStream import PiVideoStream

def findBallHough(frame):
   #Convert color to grayscale
   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
   cv2.imshow("gray", gray)

   blur = cv2.GaussianBlur(gray, (9, 9), 1)
   cv2.imshow("blur", blur)

   #Perform Hough Circles algorithm
   circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp = 4, minDist=200, \
                              param1=30, param2=50, minRadius=60, maxRadius=120)
   circles = np.uint16(np.around(circles))

   #Find largest circle
   loc = circles[0, 0]
   (y, x, z) = frame.shape

   mask = np.zeros((y, x), dtype=np.uint8)
   cv2.circle(mask, (loc[0], loc[1]), loc[2], (255, 255, 255), -1)
   cv2.imshow("mask", mask)

   cv2.circle(frame, (loc[0], loc[1]), loc[2], (0, 255, 0), 2)

   hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

   hue_histr = cv2.calcHist([hsv], [0], mask, [256], [0, 256])
   plt.plot(hue_histr, color='r')
   sat_histr = cv2.calcHist([hsv], [1], mask, [256], [0, 256])
   plt.plot(sat_histr, color='g')
   val_histr = cv2.calcHist([hsv], [2], mask, [256], [0, 256])
   plt.plot(val_histr, color='b')

   print "Mean: ("+ str(hue_avg) + ", " + str(sat_avg) + ", " + str(val_avg) + ")"

   plt.show()

   return (frame, loc)


def main():
   vs = PiVideoStream(resolution=(400, 240)).start()
   time.sleep(2.0)

   #frame = cv2.imread("ballimage2.jpg", 1)
   frame = vs.read()
   (frame, loc) = findBallHough(frame)
   cv2.imshow("Hough", frame)
   key = cv2.waitKey(0) & 0xFF
   cv2.destroyAllWindows()
   vs.stop()

   print "Found ball at (" + str(loc[0]) + ", " + str(loc[1]) + "), size = " + str(loc[2])


if __name__ == "__main__":
   main()

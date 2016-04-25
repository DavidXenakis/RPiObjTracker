import cv2
import math
import glob
import numpy as np
import sys, os, getopt
import FindingFuncs
from natsort import natsort_keygen, ns
import scipy.io
from time import time
from PiVideoReader import PiVideoReader

params = {'preview' : False, 'dir' : None}

def parse_args(argv):
   try:
      opts, args = getopt.getopt(argv, 'd:p')
   except getopt.GetoptError:
      print 'Error with arguments'
      sys.exit(1)
   for opt, arg in opts:
      if opt == "-p":
         params['preview'] = True
      elif opt == "-d":
         params['dir'] = arg

def processFrame(frame, func, color=None):
   t1 = time()
   loc, frame = func(frame, color, params['preview'])
   t2 = time()

   return t2 - t1, loc, frame

def getFileList(ext):
   files = glob.glob(params['dir'] + "/*" + ext)
   natsort_key = natsort_keygen(key = lambda y: y.lower())
   files.sort(key=natsort_key)

   return files

def error(p1, p2):
   #return math.sqrt(math.pow(p2[0] - p1[0], 2) 
   #   + math.pow(p2[1] - p1[1], 2))
   return abs(p2[0] - p1[0])

def main():
   parse_args(sys.argv[1:])

   #if params['file'] == None:
   #   print "Please specify a file"
   #   sys.exit(1)
   if params['dir'] == None:
      print "Please specify a photo directory"
   
   files = getFileList(".tif")
   if files is None:
      print "Didn't grab files"
   #Load matlab matrix
   #Get rid of the extra information, just keep the coords
   coords = scipy.io.loadmat(
         params['dir'] + "/coords.mat")['coords']
   if coords is None:
      print "Didn't grab coords"
   
   frame = cv2.imread(files[0])
   (y, x, z) = np.shape(frame)
   color = FindingFuncs.calibrateColor(frame, y)
   print color
   color = {'lower' : (110, 40, 40), 'upper' : (130, 255, 255)}
   #cv2.imshow("frame", frame)
   #key = cv2.waitKey(5000) & 0xFF

   runTime = 0
   frames =  0
   totalError = 0

   for i, f in enumerate(files):
      frames += 1
      frame = cv2.imread(f)
      frame = frame[y * .28 : y * .62, 0:x]

      func = FindingFuncs.findBallColor
      t, [bx, by], frame = processFrame(frame, func, color)
      if bx is None:
         bx = coords[i][0] + x

      e = error([bx, by], coords[i])
      totalError += e
      runTime += t


      if params['preview']:
         print "---Frame: " + str(i)
         print "Coord: " + str(coords[i])
         print "Found: " + str([bx, by])
         print "Error: " + str(e)
         cv2.imshow("frame", frame)
         key = cv2.waitKey(1000) & 0xFF
         if key == ord("q"):
            break;
          
   
   print "--Report--"
   print "Frames Read:\t\t" + str(frames)
   print "Processing Time:\t" + str(runTime)
   print "Average Processing:\t" + str(runTime / frames)
   print "Average Error:\t\t" + str(totalError / frames)
   cv2.destroyAllWindows()


if __name__ == "__main__":
   main()

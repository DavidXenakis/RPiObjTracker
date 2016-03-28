import os
import sys

yRes = [50, 100, 150, 200, 250, 300, 350, 400]
xRes = [75, 150, 225, 300, 375, 450, 525, 600]

test = 0

print '********Test Suite without preview********'
for x, y in zip(xRes, yRes):
   test += 1
   print '****Testing #' + str(test) + ' with res: (' + str(x) + ", " + str(y) + ")****"
   print 'Single Threaded'
   os.system("python balltracker.py -m color -h " + str(y) + " -w " + str(x))
   print 'Parallel'
   os.system("python PiVideoProcessor.py -m color -h " + str(y) + " -w " + str(x))
   print 'Hough'
   os.system("python PiVideoProcessor.py -m hough -h " + str(y) + " -w " + str(x))



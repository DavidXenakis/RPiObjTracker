import os
import sys

yRes = [150, 200, 250, 300, 350, 400]
xRes = [225, 300, 375, 450, 525, 600]

test = 0

for x, y in zip(xRes, yRes):
   test += 1
   print '****Testing #' + str(test) + ' with res: (' + str(x) + ", " + str(y) + ")****"
   print 'Orb'
   os.system("python PiVideoProcessor.py -m orb -h " + str(y) + " -w " + str(x))

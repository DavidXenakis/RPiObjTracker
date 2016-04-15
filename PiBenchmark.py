import os

resolutions = ((50, 75), (100, 150), (150, 225), (200, 300), (250, 375), (300, 450), (350, 525), (400, 600))

for res in resolutions:
   y, x = res[0], res[1]
   print "** Testing Resolution (" + str(x) + ", " + str(y) + ") **"
   os.system("python PiVideoProcessor.py -h " + str(y) + 
             " -w " + str(x) + " -m color -t 10")
   

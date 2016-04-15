This program is used to track objects and report their positions over MAVLink.
If you run color method, the first action this program takes is runs a color 
calibration. You need to hold the ball you want to track in front of the camera
about 8 inches away for a couple seconds after the camera starts up.

Usage:
   python PiVideoProcessor [options...]

   Options are given in c-style formatting

   [options] = 
      -h <int>    Y resolution for capture
                  <int> = (1...infinity)
                  Default = 200
      -w <int>    X resulution for capture
                  <int> = (1...infinity)
                  Default = 400
      -t <int>    Time to capture in seconds
                  <int> = (1...infinity)
                  Default = 10 
      -m <method> Method of object detection
                  <method> = hough color orb
                  Default = color
      -s          Send messages over MAVLink
                  Default = False
      -p          Preview capture 
                  Default = False

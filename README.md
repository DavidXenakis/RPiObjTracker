This program is used to track objects and report their positions over MAVLink.

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
      -c <color>  Color of object to look for
                  <color> = (blue orange purple neon)
                  Default = blue
      -m <method> Method of object detection
                  <method> = hough color orb
                  Default = color
      -s          Send messages over MAVLink
                  Default = False
      -p          Preview capture 
                  Default = False

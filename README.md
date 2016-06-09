This program is used to track objects and report their positions over MAVLink.

Usage:
   python PiVideoProcessor [options...]

   Options are given in c-style formatting

   [options] = 
      -w <int>    X resulution for capture
                  <int> = (1...infinity)
                  Default = 600
      -t <int>    Time to capture in seconds
                  <int> = (1...infinity)
                  Default = infinite 
      -m <method> Method of object detection
                  <method> = color, orb, surf
                  Default = surf
      -f <file>   Which image file to track
                  Default = None
      -d          Print debug information
                  Default = None
      -s          Send messages over MAVLink
                  Default = False
      -p          Preview capture 
                  Default = False

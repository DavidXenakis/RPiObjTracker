#!/bin/bash
# Sometimes a run of PiVideoProcessor will crash and hangup. 
# I just run this command to kill the process. 

ps | grep python | awk '{print $1}' | xargs kill -9

from pymavlink import mavlink
import serial

port = serial.Serial('/dev/ttyAMA0', 57600, timeout=0)
mav = mavlink.MAVLink(port)

message = mavlink.MAVLink_duck_leader_loc_message(-1.0, 4.0)
mav.send(message)

port.close()



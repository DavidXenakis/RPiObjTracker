from KalmanFilter import KalmanFilter
import time
kf = KalmanFilter()
kf.update(5)
print kf.predict()
time.sleep(.2)
kf.update(5.5)
print kf.predict()

time.sleep(.2)
kf.update(6)
print kf.predict()

time.sleep(.2)
kf.update(6.5)
print kf.predict()

time.sleep(.2)
kf.update(7)
print kf.predict()

time.sleep(.2)
kf.update(15)
print kf.predict()

time.sleep(.2)
kf.update(8.5)
print kf.predict()

time.sleep(.2)
kf.update(7)
print kf.predict()

time.sleep(.2)
kf.update(9.5)
print kf.predict()

time.sleep(.2)
print kf.predict()

time.sleep(.2)
kf.update(10.5)
print kf.predict()

time.sleep(.2)
print kf.predict()
time.sleep(.2)
print kf.predict()
time.sleep(.2)
print kf.predict()


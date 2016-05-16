from Matrix import matrix
from time import time

class KalmanFilter:
    def __init__(self):
        # Location and Speed
        self.x = matrix([[0.], [0.]])
        # Initial uncertainty
        self.P = matrix([[10., 0.], [0., 10.]])
        # External Motion (Steering)
        self.u = matrix([[0.], [0.]])
        # State Transition Matrix
        self.F = matrix([[1., 1.], [0, 1.]])
        # Measurement Function. What are you measuring?
        self.H = matrix([[1., 0.]])
        # Measurement Uncertainty
        self.R = matrix([[.1]])
        # Increase Gain
        self.G = matrix([[2.]])
        # Identity Matrix
        self.I = matrix([[1., 0], [0, 1.]])
        self.t = time()

    def update(self, measurement):
        # Update State Transition Matrix
        curTime = time()
        dt = curTime - self.t
        self.F = matrix([[1., dt], [0, 1.]])

        z = matrix([[measurement]])
        y = z - self.H * self.x
        S = self.H * self.P * self.H.transpose() + self.R
        K = self.P * self.H.transpose() * S.inverse()
      
        self.x = self.x + (K * y)# * self.G
        self.P = (self.I - K * self.H) * self.P

    def predict(self):
        # Update State Transition Matrix
        curTime = time()
        dt = curTime - self.t 
        self.t = curTime
        self.F = matrix([[1., dt], [0, 1.]])

        self.x = self.F * self.x + self.u
        self.P = self.F * self.P * self.F.transpose()
        return self.x.getValue()[0][0]
        
        

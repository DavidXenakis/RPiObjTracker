import cv2
import imutils
import numpy as np
from FindingFuncs import *
from matplotlib import pyplot as plt

img = cv2.imread('training/yinyang.jpg', 0)
query = cv2.imread('yin2.jpg', 0)

surf = cv2.xfeatures2d.SURF_create(800)

kpImg, desImg = surf.detectAndCompute(img, None)

FLANN_INDEX_KDTREE = 0
index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
search_params = dict(checks=50)

flann = cv2.FlannBasedMatcher(index_params, search_params)

found, [x,y], frame = findPatternSURF(query, surf, kpImg, desImg, img, flann, True)

cv2.imshow("Figure", frame)
cv2.waitKey(0)





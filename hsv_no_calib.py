import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import time

def apply_threshold_hsv(roi, hsv_color, threshold=10, threshold_s=50, threshold_v=80):
    """Apply color thresholding in HSV color space to isolate specific color ranges in the ROI."""
    # Adjust the saturation (S) and value (V) thresholds based on lighting conditions
    lower_limit = np.array([max(0, hsv_color[0] - threshold), max(0, hsv_color[1] - threshold_s), max(0, hsv_color[2] - threshold_v)])
    upper_limit = np.array([min(179, hsv_color[0] + threshold), min(255, hsv_color[1] + threshold_s), min(255, hsv_color[2] + threshold_v)])
    mask = cv2.inRange(roi, lower_limit, upper_limit)
    return mask
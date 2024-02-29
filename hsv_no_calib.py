import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import time

def apply_threshold_hsv(roi, hsv_color, threshold_h=10, threshold_s=35, threshold_v=80):
    """Apply color thresholding in HSV color space to isolate specific color ranges in the ROI."""
    
    lower_bound = np.array([max(0, hsv_color[0] - threshold_h), max(0, hsv_color[1] - threshold_s), max(0, hsv_color[2] - threshold_v)])
    upper_bound = np.array([min(180, hsv_color[0] + threshold_h), min(255, hsv_color[1] + threshold_s), min(255, hsv_color[2] + threshold_v)])
    mask = cv2.inRange(roi, lower_bound, upper_bound)
    return mask

def find_clusters(mask):
    """Find clusters in the mask using DBSCAN."""
    
    y_coord, x_coord = np.where(mask != 0)
    if len(y_coord) == 0:
        return {}  # Return an empty dict if no points found
    
    coord_array = np.stack((y_coord, x_coord), axis=-1)
    sorted_array = coord_array[coord_array[:, 1].argsort()]
    dbscan = DBSCAN(eps=5, min_samples=10)
    clusters = dbscan.fit_predict(sorted_array)

    cluster_dict = {}
    for point, cluster_idx in zip(sorted_array, clusters):
        if cluster_idx != -1:
            cluster_dict.setdefault(cluster_idx, []).append(point.tolist())
            
    return cluster_dict

def filter_noise_clusters(cluster_dict, size_threshold):
    """
    Filters clusters based on a minimum size threshold.

    Parameters:
    - cluster_dict (dict): A dictionary where each key represents a cluster index,
      and the value is a list of points belonging to that cluster.
    - size_threshold (int): The minimum number of points a cluster must have to be included.

    Returns:
    - dict: A new dictionary containing only the clusters that meet the size threshold.
    """
    
    filtered_clusters = {}
    for key, points in cluster_dict.items():
        if len(points) > size_threshold:
            filtered_clusters[key] = points
            
    return filtered_clusters

def generate_error_bounds_for_clusters(cluster_dict_black, cluster_dict_white, initial_threshold=5):
    """
    Generates error bounds for black and white clusters based on their counts and an initial threshold.

    Parameters:
    - cluster_dict_black (dict): The black clusters dictionary.
    - cluster_dict_white (dict): The white clusters dictionary.
    - initial_threshold (int): The initial threshold for error calculation.

    Returns:
    - tuple: Contains two tuples for black and white error bounds, each with a list for lower and upper bounds.
    """
    error_lower_bound_black = [initial_threshold for _ in range(len(cluster_dict_black))]
    error_upper_bound_black = [initial_threshold + 15 for _ in range(len(cluster_dict_black))]
    
    error_lower_bound_white = [initial_threshold for _ in range(len(cluster_dict_white))]
    error_upper_bound_white = [initial_threshold + 12 for _ in range(len(cluster_dict_white))]

    black_error_bounds = (error_lower_bound_black, error_upper_bound_black)
    white_error_bounds = (error_lower_bound_white, error_upper_bound_white)
    
    return black_error_bounds, white_error_bounds


def calibrate_error_bounds(error_keys, error_bounds):
    """
    Adjusts error bounds based on the presence of keys in the error_keys list. If error_keys is not empty,
    increments the bounds for those keys. Otherwise, indicates that calibration is done.

    Parameters:
    - error_keys (list): A list of indices corresponding to clusters that met error criteria.
    - error_bounds (tuple): A tuple containing two lists (error_lower_bound, error_upper_bound) representing the current error bounds for filtering.

    Returns:
    - tuple: The updated error_bounds tuple after adjustment.
    """
    error_lower_bound, error_upper_bound = error_bounds
    if error_keys:
        for _, value in enumerate(error_keys):
            error_lower_bound[value] += 1
            error_upper_bound[value] += 1
        updated_bounds = (error_lower_bound, error_upper_bound)
    else:
        print("calibration_done:", error_lower_bound, error_upper_bound)
        # each value in error_lower_bound + something to notget other keys  
        updated_bounds = error_bounds  # No change if calibration done

    return updated_bounds

def filter_keys(cluster_dict, roi, inf_roi, error_bounds):
    """
    Calculates error percentages for clusters and filters keys based on error bounds.

    Parameters:
    - cluster_dict (dict): Clusters to analyze, where each key is a cluster index, and the value is a list of points.
    - roi (numpy.ndarray): The reference region of interest from the original frame.
    - inf_roi (numpy.ndarray): The inference region of interest from the compared frame.
    - error_bounds (tuple): A tuple containing two lists, the first for lower bounds and the 
      second for upper bounds of error percentages for filtering. Each list's length should match the number of clusters.

    Returns:
    - tuple: (error_keys, error_percentages)
        - error_keys (list): The keys of clusters that fall within the specified error bounds.
        - error_percentages (list): The error percentages of all clusters.
    """
    error_keys = []
    error_percentages = []
    error_lower_bound, error_upper_bound = error_bounds

    for index, (key, cluster) in enumerate(cluster_dict.items()):
        error_count = sum(1 for row_ref, col_ref in cluster if not np.array_equal(roi[row_ref, col_ref], inf_roi[row_ref, col_ref]))
        total_comparisons = len(cluster)

        error_percentage = (error_count / total_comparisons) * 100 if total_comparisons > 0 else 0
        error_percentages.append(error_percentage)

        if total_comparisons > 0 and error_lower_bound[index] < error_percentage < error_upper_bound[index]:
            error_keys.append(key)
    return error_keys

def reference_frame(frame, mask_bound, hsv_color_1, hsv_color_2, threshold=40):
    x1, y1, x2, y2 = mask_bound
    roi = frame[y1:y2, x1:x2]
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # black
    mask_1 = apply_threshold_hsv(roi_hsv, hsv_color_1)
    roi[mask_1 != 0] = [255, 0, 0]
    cluster_dict_1 = find_clusters(mask_1)

    # white
    mask_2 = apply_threshold_hsv(roi_hsv, hsv_color_2)
    roi[mask_2 != 0] = [255, 0, 255]
    cluster_dict_2 = find_clusters(mask_2)

    cluster_dict_1 = filter_noise_clusters(cluster_dict_1, 100)
    cluster_dict_2 = filter_noise_clusters(cluster_dict_2, 100)

    ###### Check if this improves the latency otherwise delete it #########
    # for cluster_idx in cluster_dict_1:
    #     cluster_dict_1[cluster_idx] = np.array(cluster_dict_1[cluster_idx])

    # for cluster_idx in cluster_dict_2:
    #     cluster_dict_2[cluster_idx] = np.array(cluster_dict_2[cluster_idx])
    
    #######################################################################

    return roi, cluster_dict_1, cluster_dict_2
    

def inference_frame(inf_frame, mask_bound, hsv_color_1, hsv_color_2, cluster_dict_1, cluster_dict_2, roi, threshold=40, error_bound_1=(), error_bound_2=()):
    x1, y1, x2, y2 = mask_bound
    inf_roi = inf_frame[y1:y2, x1:x2]
    inf_roi_hsv = cv2.cvtColor(inf_roi, cv2.COLOR_BGR2HSV)

    # black
    mask_1 = apply_threshold_hsv(inf_roi_hsv, hsv_color_1)
    inf_roi[mask_1 != 0] = [255, 0, 0]

    # white
    mask_2 = apply_threshold_hsv(inf_roi_hsv, hsv_color_2)
    inf_roi[mask_2 != 0] = [255, 0, 255]

    black_error_keys = filter_keys(cluster_dict_1, roi, inf_roi, error_bound_1)
    white_error_keys = filter_keys(cluster_dict_2, roi, inf_roi, error_bound_2)

    return inf_roi, black_error_keys, white_error_keys
    

white_keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
black_keys = ['C#', 'D#', 'F#', 'G#', 'A#']

def encode_to_scale(values, scale):
    encoded_notes = []
    scale_length = len(scale)
    for value in values:
        # Map each value to a note in the scale
        note = scale[value % scale_length]
        encoded_notes.append(note)
    return encoded_notes

cap =  cv2.VideoCapture(0, cv2.CAP_DSHOW)
ref_img = False
# white = (196, 140, 233)
# black = (161, 222, 216)
HSV_color_1 = (174, 131, 201)
HSV_color_2 = (29, 58, 201)

while cap.isOpened():
    
    success, frame_img = cap.read()

    if not success:
        print("Ignoring empty camera frame.")
        break

    if not ref_img:    
        cv2.imshow('Pressed Key Frame', frame_img)
        
        if cv2.waitKey(1) & 0xFF == ord('s'):
            mask_bound = (0, 265, 640, 452)
            roi, cluster_dict_1, cluster_dict_2 = reference_frame(frame_img, mask_bound, HSV_color_1 , HSV_color_2)
            ref_img = True
            black_error_bounds, white_error_bounds = generate_error_bounds_for_clusters(cluster_dict_1, cluster_dict_2, initial_threshold=8)

    elif(ref_img):
        frame_roi, black_error_keys, white_error_keys = inference_frame(frame_img, mask_bound, HSV_color_1, HSV_color_2,
                cluster_dict_1, cluster_dict_2, roi, threshold=40, 
                error_bound_1=black_error_bounds, error_bound_2=white_error_bounds)
        
        encoded_notes_black = encode_to_scale(black_error_keys, black_keys)
        encoded_notes_white = encode_to_scale(white_error_keys, white_keys)
        all_notes = encoded_notes_white + encoded_notes_black
        
        if(all_notes):
            # print(all_notes)
            pass

        for keys in black_error_keys:
            for i in cluster_dict_1[keys]:
                rows, columns = i
                
                frame_roi[rows][columns][0] = 0
                frame_roi[rows][columns][1] = 255
                frame_roi[rows][columns][2] = 0
                
        for keys in white_error_keys:
            for i in cluster_dict_2[keys]:
                rows, columns = i
                
                frame_roi[rows][columns][0] = 0
                frame_roi[rows][columns][1] = 125
                frame_roi[rows][columns][2] = 125
        
        cv2.imshow('Pressed Key Frame', frame_roi)

    cv2.waitKey(1)
    if cv2.getWindowProperty('Pressed Key Frame', cv2.WND_PROP_VISIBLE) < 1:
        break
    
cap.release()
cv2.destroyAllWindows()
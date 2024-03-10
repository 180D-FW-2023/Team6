import cv2
import time
import numpy as np
from sklearn.cluster import DBSCAN
from pupil_apriltags import Detector


def apply_threshold_hsv(roi, hsv_color, threshold_h=10, threshold_s=35, threshold_v=80):
    """
    Applies a color threshold to a region of interest (ROI) in HSV color space.

    Parameters:
    - roi (array): The region of interest, an image array where the color thresholding will be applied.
    - hsv_color (tuple): The central HSV color around which the thresholding will be performed. It's a tuple
      of (Hue, Saturation, Value).
    - threshold_h (int, optional): The threshold for the Hue component. Defaults to 10.
    - threshold_s (int, optional): The threshold for the Saturation component. Defaults to 35.
    - threshold_v (int, optional): The threshold for the Value component. Defaults to 80.

    Returns:
    - array: A mask where pixels within the specified HSV threshold range are white (255) and others are black (0).
    """

    lower_bound = np.array(
        [max(0, hsv_color[0] - threshold_h), max(0, hsv_color[1] - threshold_s), max(0, hsv_color[2] - threshold_v)])
    upper_bound = np.array([min(180, hsv_color[0] + threshold_h), min(255, hsv_color[1] + threshold_s),
                            min(255, hsv_color[2] + threshold_v)])
    mask = cv2.inRange(roi, lower_bound, upper_bound)
    return mask


def find_clusters(mask, size_threshold=(50, 300)):
    """
    Identifies clusters of non-zero pixels in a mask using the DBSCAN clustering algorithm.

    Parameters:
    - mask (array): A 2D numpy array where non-zero values represent pixels of interest.

    Returns:
    - dict: A dictionary where each key is a cluster index and the value is a list of [y, x] coordinates
      belonging to that cluster. Clusters are formed based on the spatial proximity of non-zero pixels
      in the mask. If no clusters are found, returns an empty dictionary.
    """

    y_coord, x_coord = np.where(mask != 0)

    if len(y_coord) == 0:
        return {}

    coord_array = np.stack((y_coord, x_coord), axis=-1)
    sorted_array = coord_array[coord_array[:, 1].argsort()]

    dbscan = DBSCAN(eps=5, min_samples=10)
    clusters = dbscan.fit_predict(sorted_array)

    cluster_dict = {}
    min_size, max_size = size_threshold
    index = 0
    for cluster_idx in np.unique(clusters):
        if cluster_idx != -1:
            cluster_points = sorted_array[clusters == cluster_idx]
            if min_size <= len(cluster_points) <= max_size:
                cluster_dict[index] = cluster_points
                index += 1

    # for point, cluster_idx in zip(sorted_array, clusters):
    #     if cluster_idx != -1 :  # Ignore noise points which are labeled as -1.
    #         cluster_dict.setdefault(cluster_idx, []).append(point.tolist())

    return cluster_dict


def filter_noise_clusters(cluster_dict, size_threshold=(50, 300)):
    """
    Filters clusters based on size thresholds.

    Parameters:
    - cluster_dict (dict): A dictionary where each key represents a cluster index,
      and the value is a list of points belonging to that cluster.
    - size_threshold (tuple): A tuple of two integers where the first value is the minimum
      number of points a cluster must have to be included, and the second value is the maximum
      number of points a cluster can have to be included.

    Returns:
    - dict: A new dictionary containing only the clusters whose sizes are within the specified range.
    """

    filtered_clusters = {}
    lower_limit, upper_limit = size_threshold
    for key, points in cluster_dict.items():
        if lower_limit < len(points) < upper_limit:
            filtered_clusters[key] = points

    return filtered_clusters


def find_pressed_keys(ref_lt_distances, ref_rt_distances, inf_lt_distances, inf_rt_distances, displacement_threshold):
    """
    Identifies keys that are considered pressed based on their displacement exceeding specified thresholds.

    Parameters:
    - ref_distance (list): A list of reference distances, typically representing the default position of each key.
    - inf_distance (list): A list of influenced distances, representing the current position of each key.
    - displacement_threshold (list): A list of threshold values for each key; a key is considered pressed if its
      displacement (ref_distance - inf_distance) is less than its corresponding threshold.

    Returns:
    - list: A list of indices representing keys that are considered pressed.
    """
    key_pressed = []

    if len(ref_lt_distances) == len(inf_lt_distances) and len(ref_rt_distances) == len(inf_rt_distances):

        displacement_lt = ref_lt_distances - inf_lt_distances
        displacement_rt = ref_rt_distances - inf_rt_distances
        displacement_lt = np.array(displacement_lt)
        displacement_rt = np.array(displacement_rt)
        # print("This is left:", displacement_lt)
        # print("This is right:", displacement_rt)
        displacements = np.abs(displacement_lt) + np.abs(displacement_rt)
        # print(displacements)

        for i in range(len(displacements)):
            if displacements[i] > displacement_threshold[i]:
                key_pressed.append(i)
                print(displacements)

    return key_pressed


def reference_frame(frame, mask_bound, hsv_color_1, hsv_color_2, right_lt_corner_coord, right_rt_corner_coord,
                    threshold=40):
    """
    Extracts regions of interest (ROIs) based on HSV color thresholds and calculates distances
    from detected cluster centroids to specified corner coordinates within the ROIs.

    Parameters:
    - frame (array): The original image frame from which regions of interest are extracted.
    - mask_bound (tuple): A tuple (x1, y1, x2, y2) defining the bounding box for the region of interest in the frame.
    - hsv_color_1 (tuple): The HSV color tuple used for the first color thresholding.
    - hsv_color_2 (tuple): The HSV color tuple used for the second color thresholding.
    - right_lt_corner_coord (tuple): The (x, y) coordinates of the right lower target corner.
    - right_rt_corner_coord (tuple): The (x, y) coordinates of the right upper target corner.
    - threshold (int, optional): The threshold value for HSV color filtering. Defaults to 40.

    Returns:
    - roi (array): The extracted region of interest from the original frame.
    - distances_lt_1 (list): Distances from the right lower target corner to the centroids of clusters detected after
    applying the first HSV filter.
    - distances_rt_1 (list): Distances from the right upper target corner to the centroids of clusters detected after
    applying the first HSV filter.
    - distances_lt_2 (list): Distances from the right lower target corner to the centroids of clusters detected after
    applying the second HSV filter.
    - distances_rt_2 (list): Distances from the right upper target corner to the centroids of clusters detected after
    applying the second HSV filter.

    The function applies HSV thresholding to the specified region of the frame to isolate areas matching the provided
    HSV colors. It then performs clustering on the thresholded areas and calculates the distances from the centroids of
    these clusters to specified corner coordinates.
    """
    x1, y1, x2, y2 = mask_bound
    roi = frame[y1:y2, x1:x2]
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # black
    mask_1 = apply_threshold_hsv(roi_hsv, hsv_color_1)
    cluster_dict_1 = find_clusters(mask_1)

    # white
    mask_2 = apply_threshold_hsv(roi_hsv, hsv_color_2)
    cluster_dict_2 = find_clusters(mask_2)

    x_centroids_1, y_centroids_1, _ = process_clusters(cluster_dict_1)
    x_centroids_2, y_centroids_2, _ = process_clusters(cluster_dict_2)

    distances_lt_1 = find_distance_corner(right_lt_corner_coord, x_centroids_1, y_centroids_1)
    distances_rt_1 = find_distance_corner(right_rt_corner_coord, x_centroids_1, y_centroids_1)
    distances_lt_2 = find_distance_corner(right_lt_corner_coord, x_centroids_2, y_centroids_2)
    distances_rt_2 = find_distance_corner(right_rt_corner_coord, x_centroids_2, y_centroids_2)

    return roi, distances_lt_1, distances_rt_1, distances_lt_2, distances_rt_2


def inference_frame(inf_frame, mask_bound, hsv_color_1, hsv_color_2, ref_distances_lt_1, ref_distances_rt_1,
                    ref_distances_lt_2, ref_distances_rt_2, right_lt_corner_coord, right_rt_corner_coord, roi,
                    threshold=40, error_bound_1=(), error_bound_2=()):
    """
    Analyzes a given frame to identify pressed keys based on changes in distances from reference distances,
    using specified HSV color thresholds and spatial clustering.

    Parameters:
    - inf_frame (array): The frame to be analyzed for key presses.
    - mask_bound (tuple): A tuple (x1, y1, x2, y2) defining the bounding box for the region of interest in the frame.
    - hsv_color_1 (tuple): The HSV color tuple used for the first color thresholding (typically for one set of keys).
    - hsv_color_2 (tuple): The HSV color tuple used for the second color thresholding (typically for another set of
    keys).
    - ref_distances_lt_1, ref_distances_rt_1, ref_distances_lt_2, ref_distances_rt_2 (list): Lists of reference
    distances
    from the right lower and upper target corners to the centroids of clusters detected in the reference frame, for two
    sets of keys.
    - right_lt_corner_coord, right_rt_corner_coord (tuple): The (x, y) coordinates of the right lower and upper target
    corners.
    - roi (array): The region of interest extracted from the reference frame (not directly used in calculations within
    this function).
    - threshold (int, optional): The threshold value for HSV color filtering. Defaults to 40.
    - error_bound_1, error_bound_2 (tuple, optional): Error bounds for considering a key as pressed for the first and
    second set of keys respectively.

    Returns:
    - inf_roi (array): The extracted region of interest from the inference frame.
    - black_pressed_keys (list): Indices of the black keys that are considered pressed in the current frame.
    - white_pressed_keys (list): Indices of the white keys that are considered pressed in the current frame.
    - cluster_dict_1, cluster_dict_2 (dict): Dictionaries of clusters identified in the current frame for each set of
    keys.

    The function applies HSV thresholding to isolate areas of interest based on color, performs spatial clustering to
    identify key regions, and calculates distances to these clusters from predefined corner coordinates. It then
    compares these distances against reference distances to determine which keys are pressed.
    """
    x1, y1, x2, y2 = mask_bound
    inf_roi = inf_frame[y1:y2, x1:x2]
    inf_roi_hsv = cv2.cvtColor(inf_roi, cv2.COLOR_BGR2HSV)

    # black
    mask_1 = apply_threshold_hsv(inf_roi_hsv, hsv_color_1)
    cluster_dict_1 = find_clusters(mask_1)
    cv2.imshow("mask 1", mask_1)

    # white
    mask_2 = apply_threshold_hsv(inf_roi_hsv, hsv_color_2)
    cluster_dict_2 = find_clusters(mask_2)
    cv2.imshow("mask 2", mask_2)

    x_centroids_1, y_centroids_1, _ = process_clusters(cluster_dict_1)
    x_centroids_2, y_centroids_2, _ = process_clusters(cluster_dict_2)

    inf_distances_lt_1 = find_distance_corner(right_lt_corner_coord, x_centroids_1, y_centroids_1)
    inf_distances_rt_1 = find_distance_corner(right_rt_corner_coord, x_centroids_1, y_centroids_1)
    inf_distances_lt_2 = find_distance_corner(right_lt_corner_coord, x_centroids_2, y_centroids_2)
    inf_distances_rt_2 = find_distance_corner(right_rt_corner_coord, x_centroids_2, y_centroids_2)

    black_pressed_keys = find_pressed_keys(ref_distances_lt_1, ref_distances_rt_1, inf_distances_lt_1,
                                           inf_distances_rt_1, error_bound_1)
    white_pressed_keys = find_pressed_keys(ref_distances_lt_2, ref_distances_rt_2, inf_distances_lt_2,
                                           inf_distances_rt_2, error_bound_2)

    return inf_roi, black_pressed_keys, white_pressed_keys, cluster_dict_1, cluster_dict_2


def frame_correction(frame):
    """
    Applies grayscale conversion and detects AprilTags in the given frame, optionally estimating their poses.

    Parameters:
    - frame (array): The original image frame in which AprilTags are to be detected.

    Returns:
    - corners (list): A list of the corners for each detected AprilTag in the frame. Each element in the list is a
      4x2 array representing the four corners of a tag.
    - euler_angles (list): A list of Euler angles representing the orientation of each detected AprilTag. This list
      is currently empty as the conversion from rotation matrices to Euler angles is not implemented.
    - at_detected (bool): A boolean flag indicating whether at least one AprilTag was detected in the frame.

    The function converts the input frame to grayscale, then uses an AprilTag detector to find and outline AprilTags
    in the frame. It currently sets up for pose estimation but does not complete this step as Euler angle
    calculations are commented out. Lines are drawn around detected tags, indicating successful detection.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    at_detected = False

    camera_params = [640, 480, 640, 480]  # fx, fy, cx, cy
    tag_size = 0.05

    tags = at_detector.detect(gray, estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)
    corners, euler_angles = [], []

    for tag in tags:
        corners.append(tag.corners)
        for idx in range(len(tag.corners)):
            at_detected = True
            cv2.line(frame, tuple(tag.corners[idx - 1].astype(int)), tuple(tag.corners[idx].astype(int)), (0, 255, 0),
                     2)

        # euler_angles = rotationMatrixToEulerAngles(tag.pose_R)
    return corners, euler_angles, at_detected


def get_sampling_coord(coords):
    """
    Calculates and returns sets of sampling coordinates based on a rectangular region defined by input coordinates.
    The function identifies the bounding rectangle for the given points and generates two sets of sampling points
    ('pink' and 'yellow') along the vertical borders outside the defined rectangle.

    Parameters:
        coords (list of lists): A list of four sublists, each representing the (x, y) coordinates of one corner
        of the rectangle. The structure is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]], where each pair [xi, yi]
        corresponds to a corner of the rectangle.

    Returns:
        list of lists: A list containing two lists of coordinates:
            - The first list, 'pink', contains coordinates extending 10 units to the right of the maximum x-value
            of the provided rectangle, at every 10 units of the y-axis within the rectangle's bounds.
            - The second list, 'yellow', contains coordinates extending 10 units to the left of the minimum x-value
            of the provided rectangle, at every 10 units of the y-axis within the rectangle's bounds.
    """

    pink = []
    yellow = []

    x_max = max(coords[0][0], coords[1][0], coords[2][0], coords[3][0])
    x_min = min(coords[0][0], coords[1][0], coords[2][0], coords[3][0])
    y_max = max(coords[0][1], coords[1][1], coords[2][1], coords[3][1])
    y_min = min(coords[0][1], coords[1][1], coords[2][1], coords[3][1])

    for index in range(int(y_min), int(y_max), 10):
        pink.append([x_max + 10, index])
        yellow.append([x_min - 20, index])

    return [pink, yellow]


def get_tag_color(img, sample_coords):
    """
    Extracts and calculates the average color values for specified 'pink' and 'yellow' sample points within an image.

    Parameters:
        img (numpy.ndarray): The image from which color samples will be taken. The image should be in a format
        that is indexable with coordinates, typically a NumPy array where color channels are accessed as
        img[y, x].

        sample_coords (tuple of lists): A tuple containing two lists of coordinates. The first list, 'pink',
        contains the (x, y) coordinates for pink color sampling. The second list, 'yellow', contains the
        (x, y) coordinates for yellow color sampling. Each coordinate pair should be formatted as (x, y).

    Returns:
        tuple of lists: A tuple containing two lists, each with three integers representing the average RGB
        color values sampled from the specified 'pink' and 'yellow' areas. The first list corresponds to the
        'yellow' color average (notably, this seems inverted based on the return statement; if this is a mistake,
        adjust accordingly), and the second list corresponds to the 'pink' color average. If no colors are
        sampled in a particular set, `None` is returned for that set's average color.

    Note:
        The function assumes that the image is indexed as img[y, x], following typical NumPy array conventions.
        Ensure that the sample coordinates provided match the dimensions and orientation of the image.
    """

    pink, yellow = sample_coords
    pink_colors = []
    yellow_colors = []

    for index in pink:
        pink_colors.append(img[int(index[1]), int(index[0])])
        # print(img[int(index[1]), int(index[0])])

    for index in yellow:
        yellow_colors.append(img[int(index[1]), int(index[0])])
        # print(img[int(index[1]), int(index[0])])

    if pink_colors:
        average_pink = np.mean(pink_colors, axis=0)
        average_pink = [int(average_pink[0]), int(average_pink[1]), int(average_pink[2])]
        # print("Average pink color:", average_pink)
    else:
        print("No pink colors sampled.")

    if yellow_colors:
        average_yellow = np.mean(yellow_colors, axis=0)
        average_yellow = [int(average_yellow[0]), int(average_yellow[1]), int(average_yellow[2])]
        # print("Average yellow color:", average_yellow)
    else:
        print("No yellow colors sampled.")

    return (average_yellow if 'average_pink' in locals() else None,
            average_pink if 'average_yellow' in locals() else None)


def BGR_to_HSV(bgr_color_1, bgr_color_2):
    """
    Convert a BGR color to HSV.

    Parameters:
        bgr_color_1 (tuple): The BGR color of black as a tuple of three integers.
        bgr_color_2 (tuple): The BGR color of white as a tuple of three integers.

    Returns:
        tuple: The HSV color as a tuple of three integers.
    """
    bgr_array = np.uint8([[bgr_color_1, bgr_color_2]])
    hsv_array = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)
    hsv_color_1, hsv_color_2 = hsv_array[0]

    return tuple(hsv_color_1), tuple(hsv_color_2)


def find_distance_corner(at_right_corner, x_centroids, y_centroids):
    """
    Calculates the Euclidean distances from a specified corner to multiple centroid points.

    Parameters:
    - at_right_corner (tuple): The (x, y) coordinates of the specified corner point.
    - x_centroids (array): An array of x-coordinates for the centroid points.
    - y_centroids (array): An array of y-coordinates for the centroid points.

    Returns:
    - distances (array): An array of distances from the specified corner to each centroid point.

    The function computes the Euclidean distance between the given corner and each centroid by calculating the
    square root of the sum of the squared differences in the x and y dimensions.
    """
    x, y = at_right_corner
    dx = x_centroids - x
    dy = y_centroids - y
    distances = (np.sqrt(dx ** 2 + dy ** 2))

    return distances


def process_clusters(cluster_dict):
    """
    Processes clusters to find centroids and corners for each cluster.

    Parameters:
    - cluster_dict (dict): A dictionary where keys are cluster indices and values are lists of points belonging to
    each cluster.

    Returns:
    - centroids_x (numpy array): An array containing the x-coordinates of the centroids of each cluster.
    - centroids_y (numpy array): An array containing the y-coordinates of the centroids of each cluster.
    - corners (numpy array): A 3D array where each element contains the corners (in the format [(min_x, min_y),
    (max_x, min_y), (max_x, max_y), (min_x, max_y)]) of the rectangular bounding box for each cluster.

    The function calculates the centroid of each cluster by averaging the x and y coordinates of all points within
    the cluster. It also determines the minimum and maximum x and y values to identify the corners of a rectangular
    bounding box enclosing each cluster.
    """
    centroids_x = []
    centroids_y = []
    corners = []

    for cluster_idx, points in cluster_dict.items():
        points_array = np.array(points)

        centroid = np.mean(points_array, axis=0, dtype=np.float64)
        centroids_x.append(centroid[1])
        centroids_y.append(centroid[0])

        min_x = np.min(points_array[:, 1])
        max_x = np.max(points_array[:, 1])
        min_y = np.min(points_array[:, 0])
        max_y = np.max(points_array[:, 0])

        corners_cluster = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
        corners.append(corners_cluster)  # Append the corners for this cluster

    return np.array(centroids_x), np.array(centroids_y), np.array(corners)


def get_lower_corners(coords):
    """
    Identifies the lower two corners from a set of coordinates and orders them from left to right.

    Parameters:
    - coords (list of tuples): A list of (x, y) tuples representing coordinates from which the lower corners are to be
    identified.

    Returns:
    - left_corner (tuple): The left-most corner among the two lower corners.
    - right_corner (tuple): The right-most corner among the two lower corners.

    The function first sorts the coordinates by their y-values in descending order to find the two lowest points
    (i.e., those with the highest y-values). It then sorts these two points by their x-values to determine which is
    left and which is right.
    """
    sorted_by_lower_y = sorted(coords, key=lambda x: x[1], reverse=True)
    lower_corners = sorted_by_lower_y[:2]

    sorted_by_x = sorted(lower_corners, key=lambda x: x[0])
    left_corner, right_corner = sorted_by_x

    return left_corner, right_corner


def identify_april_tags(corners):
    """
    Identifies the left and right April tags based on the x-coordinates of their corners.

    Parameters:
    - corners (list of np.array): A list containing two numpy arrays where each array represents
      the coordinates of the four corners of an April tag. Each array should be of shape (4, 2),
      where the two columns represent x and y coordinates respectively.

    Returns:
    - tuple: A tuple containing two numpy arrays, where the first array represents the corners
      of the left April tag and the second array represents the corners of the right April tag.
    """
    if len(corners) != 2:
        raise ValueError("Exactly two sets of corners must be provided")

    avg_x_coordinates = [np.mean(tag[:, 0]) for tag in corners]

    left_tag_index = np.argmin(avg_x_coordinates)
    right_tag_index = np.argmax(avg_x_coordinates)

    left_tag = corners[left_tag_index]
    right_tag = corners[right_tag_index]

    return left_tag, right_tag


white_keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
black_keys = ['C#', 'D#', 'F#', 'G#', 'A#']


def encode_to_scale(values, scale):
    """
    Encodes numerical values into musical notes based on a given scale.

    Parameters:
    - values (list of int): A list of integer values representing the positions in the scale.
    - scale (list of str): A list of strings representing musical notes in a specific scale.

    Returns:
    - encoded_notes (list of str): A list of musical notes corresponding to the input values, mapped according to the
    provided scale.

    The function maps each value in the input list to a note in the scale by taking the modulus of the value with the
    length of the scale. This ensures that all values are valid indices of the scale, thereby encoding arbitrary
    numerical values into notes within the given scale.
    """
    encoded_notes = []
    scale_length = len(scale)
    for value in values:
        note = scale[value % scale_length]
        encoded_notes.append(note)
    return encoded_notes


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
ref_img = False
count = 0
CAPTURE_COUNT = 30

# Initialize the AprilTag detector
at_detector = Detector(families='tag36h11',
                       nthreads=1,
                       quad_decimate=1.0,
                       quad_sigma=0.0,
                       refine_edges=1,
                       decode_sharpening=0.25,
                       debug=0)

while cap.isOpened():

    success, frame_img = cap.read()
    frame_img = cv2.rotate(frame_img, cv2.ROTATE_180)

    if not success:
        print("Ignoring empty camera frame.")
        break

    if count < CAPTURE_COUNT:
        count += 1
        continue

    if not ref_img:
        # cv2.imshow('Pressed Key Frame', frame_img)

        # if cv2.waitKey(1) & 0xFF == ord('s'):
        #     # Color Detector

        ref_at_coord, ref_angle, ref_at_detected = frame_correction(frame_img)
        if not ref_at_detected:
            continue
        left_tag, right_tag = identify_april_tags(ref_at_coord)
        color_sample_coords = get_sampling_coord(left_tag)

        BGR_color_1, BGR_color_2 = get_tag_color(frame_img, color_sample_coords)
        HSV_color_1, HSV_color_2 = BGR_to_HSV(BGR_color_1, BGR_color_2)
        ref_lt_left_corner, ref_lt_right_corner = get_lower_corners(left_tag)
        ref_rt_left_corner, ref_rt_right_corner = get_lower_corners(right_tag)

        # Tag Detection
        mask_bound = (0, 0, 640, 480)
        roi, distances_lt_1, distances_rt_1, distances_lt_2, distances_rt_2 = reference_frame(frame_img, mask_bound,
                                                                                                HSV_color_1,
                                                                                                HSV_color_2,
                                                                                                ref_lt_right_corner,
                                                                                                ref_rt_right_corner)
        ref_img = True
        
        # TODO: CHECK THRESHOLD/SET THE CORRECT ONES
        black_error_bounds = [-1.0, -1.0, -0.8, -0.84, -0.7, -0.6, -0.5, -0.4, -1.0, -1.0, -0.65, -0.7, -0.6, -0.5,
                                -0.5, -0.4]
        black_error_bounds = [1.5 for _ in range(len(black_error_bounds))]
        white_error_bounds = [-1.0, -1.0, -0.8, -0.84, -0.7, -0.6, -0.5, -0.4, -1.0, -1.0, -0.65, -0.7, -0.6, -0.5,
                                -0.5, -0.4]
        white_error_bounds = [1.5 for _ in range(len(white_error_bounds))]

    elif (ref_img):
        # April Tag Correction
        inf_at_coord, inf_angle, inf_at_detected = frame_correction(frame_img)

        if (inf_at_detected):
            left_tag, right_tag = identify_april_tags(inf_at_coord)
            inf_lt_left_corner, inf_lt_right_corner = get_lower_corners(left_tag)
            inf_rt_left_corner, inf_rt_right_corner = get_lower_corners(right_tag)

            # Tag Detection
            frame_roi, black_error_keys, white_error_keys, cluster_dict_1, cluster_dict_2 = inference_frame(frame_img,
                                                                                                            mask_bound,
                                                                                                            HSV_color_1,
                                                                                                            HSV_color_2,
                                                                                                            distances_lt_1,
                                                                                                            distances_rt_1,
                                                                                                            distances_lt_2,
                                                                                                            distances_rt_2,
                                                                                                            inf_lt_right_corner,
                                                                                                            inf_rt_right_corner,
                                                                                                            roi,
                                                                                                            threshold=40,
                                                                                                            error_bound_1=black_error_bounds,
                                                                                                            error_bound_2=white_error_bounds)

            encoded_notes_black = encode_to_scale(black_error_keys, black_keys)
            encoded_notes_white = encode_to_scale(white_error_keys, white_keys)
            all_notes = encoded_notes_white + encoded_notes_black

            if(all_notes):
                print(all_notes)


cap.release()
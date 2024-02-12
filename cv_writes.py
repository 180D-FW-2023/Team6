import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import time
import zmq
# Prepare the ZeroMQ context and PUSH socket
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.bind("tcp://*:5555")  # Bind to TCP port 5555 on all interfaces


# create hex_color_picker

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))[::-1]


def reference_frame(frame, mask_bound, hex_color_1, hex_color_2, threshold=40):
    x1, y1, x2, y2 = mask_bound
    roi = frame[y1:y2, x1:x2]

    # black
    bgr_color_1 = hex_to_bgr(hex_color_1)  # "#C8CE7B"
    lower_bound_1 = np.array(
        [max(0, bgr_color_1[0] - threshold), max(0, bgr_color_1[1] - threshold), max(0, bgr_color_1[2] - threshold)])
    upper_bound_1 = np.array([min(255, bgr_color_1[0] + threshold), min(255, bgr_color_1[1] + threshold),
                              min(255, bgr_color_1[2] + threshold)])
    mask_1 = cv2.inRange(roi, lower_bound_1, upper_bound_1)

    y_coord_1, x_coord_1 = np.where(mask_1 != 0)
    roi[mask_1 != 0] = [255, 0, 0]
    coord_array_1 = np.stack((y_coord_1, x_coord_1), axis=-1)
    sorted_array_1 = coord_array_1[coord_array_1[:, 1].argsort()]

    # white
    bgr_color_2 = hex_to_bgr(hex_color_2)  # "#C8CE7B"
    lower_bound_2 = np.array(
        [max(0, bgr_color_2[0] - threshold), max(0, bgr_color_2[1] - threshold), max(0, bgr_color_2[2] - threshold)])
    upper_bound_2 = np.array([min(255, bgr_color_2[0] + threshold), min(255, bgr_color_2[1] + threshold),
                              min(255, bgr_color_2[2] + threshold)])
    mask_2 = cv2.inRange(roi, lower_bound_2, upper_bound_2)

    y_coord_2, x_coord_2 = np.where(mask_2 != 0)
    roi[mask_2 != 0] = [0, 0, 255]
    coord_array_2 = np.stack((y_coord_2, x_coord_2), axis=-1)
    sorted_array_2 = coord_array_2[coord_array_2[:, 1].argsort()]

    # DBSCAN Black
    if sorted_array_1.size > 0:
        dbscan_1 = DBSCAN(eps=5, min_samples=10)  # Adjust eps and min_samples as needed
        clusters_1 = dbscan_1.fit_predict(sorted_array_1)

        # Organize points into a dictionary based on their cluster
        cluster_dict_1 = {}
        for point, cluster_idx in zip(sorted_array_1, clusters_1):
            if cluster_idx != -1:  # Filter out noise points if needed
                cluster_dict_1.setdefault(cluster_idx, []).append(point.tolist())
    else:
        print("No blue points found in the image.")
        cluster_dict_1 = {}

    for cluster_idx in cluster_dict_1:
        cluster_dict_1[cluster_idx] = np.array(cluster_dict_1[cluster_idx])

    # DBSCAN White
    if sorted_array_2.size > 0:
        dbscan_2 = DBSCAN(eps=5, min_samples=10)  # Adjust eps and min_samples as needed
        clusters_2 = dbscan_2.fit_predict(sorted_array_2)

        # Organize points into a dictionary based on their cluster
        cluster_dict_2 = {}
        for point, cluster_idx in zip(sorted_array_2, clusters_2):
            if cluster_idx != -1:  # Filter out noise points if needed
                cluster_dict_2.setdefault(cluster_idx, []).append(point.tolist())
    else:
        print("No blue points found in the image.")
        cluster_dict_2 = {}

    cluster_dict_2_proc = {}
    index = 0
    for key in cluster_dict_2:
        if (len(cluster_dict_2[key]) > 75):
            cluster_dict_2_proc[index] = cluster_dict_2[key]
            index += 1

    for cluster_idx in cluster_dict_2:
        cluster_dict_2[cluster_idx] = np.array(cluster_dict_2[cluster_idx])

    print(len(cluster_dict_2_proc))

    return roi, cluster_dict_1, cluster_dict_2_proc


def inference_frame(inf_frame, mask_bound, hex_color_1, hex_color_2, cluster_dict_1, cluster_dict_2, roi, threshold=40, error_lower_bound=[], error_upper_bound=[]):
    x1, y1, x2, y2 = mask_bound
    inf_roi = inf_frame[y1:y2, x1:x2]

    # black
    bgr_color_1 = hex_to_bgr(hex_color_1)  # "#C8CE7B"
    lower_bound_1 = np.array(
        [max(0, bgr_color_1[0] - threshold), max(0, bgr_color_1[1] - threshold), max(0, bgr_color_1[2] - threshold)])
    upper_bound_1 = np.array([min(255, bgr_color_1[0] + threshold), min(255, bgr_color_1[1] + threshold),
                              min(255, bgr_color_1[2] + threshold)])
    mask_1 = cv2.inRange(inf_roi, lower_bound_1, upper_bound_1)

    y_coord_1, x_coord_1 = np.where(mask_1 != 0)
    coord_array_1 = np.stack((y_coord_1, x_coord_1), axis=-1)
    inf_roi[mask_1 != 0] = [255, 0, 0]

    # white
    bgr_color_2 = hex_to_bgr(hex_color_2)  # "#C8CE7B"
    lower_bound_2 = np.array(
        [max(0, bgr_color_2[0] - threshold), max(0, bgr_color_2[1] - threshold), max(0, bgr_color_2[2] - threshold)])
    upper_bound_2 = np.array([min(255, bgr_color_2[0] + threshold), min(255, bgr_color_2[1] + threshold),
                              min(255, bgr_color_2[2] + threshold)])
    mask_2 = cv2.inRange(inf_roi, lower_bound_2, upper_bound_2)

    y_coord_2, x_coord_2 = np.where(mask_2 != 0)
    coord_array_2 = np.stack((y_coord_2, x_coord_2), axis=-1)
    inf_roi[mask_2 != 0] = [255, 0, 255]

    all_errors_black = []
    error_keys_black = []
    for cluster in cluster_dict_1.values():
        error_count_1 = sum(1 for rows_ref, columns_ref in cluster
                            if all(roi[rows_ref][columns_ref]) != all(inf_roi[rows_ref][columns_ref]))
        all_errors_black.append(error_count_1)

    for index, values in enumerate(all_errors_black):
        if (values > 20):
            error_keys_black.append(index)

    # Black
    # all_errors_black = []
    # error_keys_black= []
    # error_percentages_black = []  # List to store error percentages

    # for cluster in cluster_dict_1.values():
    #     error_count_1 = 0
    #     total_comparisons = 0  # Initialize total comparisons for the current cluster
    #     for rows_ref, columns_ref in cluster:
    #         total_comparisons += 1  # Increment total comparisons
    #         if all(roi[rows_ref][columns_ref]) != all(inf_roi[rows_ref][columns_ref]):
    #             error_count_1 += 1
    #     all_errors_black.append(error_count_1)
    #     if total_comparisons > 0:  # Avoid division by zero
    #         error_percentage = (error_count_1 / total_comparisons) * 100
    #     else:
    #         error_percentage = 0  # If no comparisons, set error percentage to 0
    #     error_percentages_black.append(error_percentage)  # Store the error percentage

    # error_lower_bound_1 = [7, 7, 8, 7, 8, 8, 8, 8, 8]
    # error_upper_bound_1 = [15, 15, 15, 15, 15, 15, 15, 15, 15]
    # for index, values in enumerate(error_percentages_black):
    #     if values > error_lower_bound_1[index] and values < error_upper_bound_1[index]:
    #         error_keys_black.append(index)

    # White
    all_errors_white = []
    error_keys_white = []
    error_percentages_white = []  # List to store error percentages

    for cluster in cluster_dict_2.values():
        error_count_2 = 0
        total_comparisons = 0  # Initialize total comparisons for the current cluster
        for rows_ref, columns_ref in cluster:
            total_comparisons += 1  # Increment total comparisons
            if all(roi[rows_ref][columns_ref]) != all(inf_roi[rows_ref][columns_ref]):
                error_count_2 += 1
        all_errors_white.append(error_count_2)
        if total_comparisons > 0:  # Avoid division by zero
            error_percentage = (error_count_2 / total_comparisons) * 100
        else:
            error_percentage = 0  # If no comparisons, set error percentage to 0
        error_percentages_white.append(error_percentage)  # Store the error percentage

    # error_lower_bound = [6, 7, 8.5, 9, 7, 8, 11, 12, 7]
    # error_upper_bound = [15, 20, 20, 15, 20, 15, 20, 20, 15]
    # error_lower_bound = [6, 7, 5, 5, 5, 8, 7, 7, 7]
    # error_upper_bound = [15, 20, 20, 15, 20, 15, 20, 15, 15]
    for index, values in enumerate(error_percentages_white):
        if values > error_lower_bound[index] and values < error_upper_bound[index]:
            error_keys_white.append(index)

    # Now, error_percentages_white contains the error percentage for each cluster

    # key = 0
    # # print(all_errors_white)
    # if(key in error_keys_white):
    #     print(error_percentages_white[key])

    # if(key in error_keys_black):
    #     print(error_percentages_black[key])

    return inf_roi, error_keys_black, error_keys_white


def inference_frame_calibration(inf_frame, mask_bound, hex_color_1, hex_color_2, cluster_dict_1, cluster_dict_2, roi,
                                threshold=40, error_lower_bound=[], error_upper_bound=[], initial_state=True):
    x1, y1, x2, y2 = mask_bound
    inf_roi = inf_frame[y1:y2, x1:x2]

    # black
    bgr_color_1 = hex_to_bgr(hex_color_1)  # "#C8CE7B"
    lower_bound_1 = np.array(
        [max(0, bgr_color_1[0] - threshold), max(0, bgr_color_1[1] - threshold), max(0, bgr_color_1[2] - threshold)])
    upper_bound_1 = np.array([min(255, bgr_color_1[0] + threshold), min(255, bgr_color_1[1] + threshold),
                              min(255, bgr_color_1[2] + threshold)])
    mask_1 = cv2.inRange(inf_roi, lower_bound_1, upper_bound_1)

    y_coord_1, x_coord_1 = np.where(mask_1 != 0)
    coord_array_1 = np.stack((y_coord_1, x_coord_1), axis=-1)
    inf_roi[mask_1 != 0] = [255, 0, 0]

    # white
    bgr_color_2 = hex_to_bgr(hex_color_2)  # "#C8CE7B"
    lower_bound_2 = np.array(
        [max(0, bgr_color_2[0] - threshold), max(0, bgr_color_2[1] - threshold), max(0, bgr_color_2[2] - threshold)])
    upper_bound_2 = np.array([min(255, bgr_color_2[0] + threshold), min(255, bgr_color_2[1] + threshold),
                              min(255, bgr_color_2[2] + threshold)])
    mask_2 = cv2.inRange(inf_roi, lower_bound_2, upper_bound_2)

    y_coord_2, x_coord_2 = np.where(mask_2 != 0)
    coord_array_2 = np.stack((y_coord_2, x_coord_2), axis=-1)
    inf_roi[mask_2 != 0] = [255, 0, 255]

    all_errors_black = []
    error_keys_black = []
    for cluster in cluster_dict_1.values():
        error_count_1 = sum(1 for rows_ref, columns_ref in cluster
                            if all(roi[rows_ref][columns_ref]) != all(inf_roi[rows_ref][columns_ref]))
        all_errors_black.append(error_count_1)

    for index, values in enumerate(all_errors_black):
        if (values > 20):
            error_keys_black.append(index)

    # White
    all_errors_white = []
    error_keys_white = []
    error_percentages_white = []  # List to store error percentages

    if (initial_state):
        print(initial_state)
        initial_threshold = 6
        error_lower_bound = [initial_threshold for _ in range(len(cluster_dict_2))]
        error_upper_bound = [initial_threshold + 12 for _ in range(len(cluster_dict_2))]

    for cluster in cluster_dict_2.values():
        error_count_2 = 0
        total_comparisons = 0  # Initialize total comparisons for the current cluster
        for rows_ref, columns_ref in cluster:
            total_comparisons += 1  # Increment total comparisons
            if all(roi[rows_ref][columns_ref]) != all(inf_roi[rows_ref][columns_ref]):
                error_count_2 += 1
        all_errors_white.append(error_count_2)
        if total_comparisons > 0:  # Avoid division by zero
            error_percentage = (error_count_2 / total_comparisons) * 100
        else:
            error_percentage = 0  # If no comparisons, set error percentage to 0
        error_percentages_white.append(error_percentage)  # Store the error percentage

    # error_lower_bound = [6, 7, 7, 6, 5, 8, 7, 7, 7]
    # error_upper_bound = [15, 20, 20, 15, 20, 15, 20, 15, 15]
    for index, values in enumerate(error_percentages_white):
        if values > error_lower_bound[index] and values < error_upper_bound[index]:
            error_keys_white.append(index)
    if (error_keys_white):
        for _, value in enumerate(error_keys_white):
            print("its here")
            error_lower_bound[value] += 1
            error_upper_bound[value] += 1
            # print(error_lower_bound, error_upper_bound)
    else:
        print("calibration_done:", error_lower_bound, error_upper_bound)

    return inf_roi, error_keys_black, error_keys_white, error_lower_bound, error_upper_bound

white_keys = ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3']
black_keys = ['C♯3', 'D♯3', 'F♯3', 'G♯3', 'A♯3']

def encode_to_scale(values, scale):
    encoded_notes = []
    scale_length = len(scale)
    for value in values:
        # Map each value to a note in the scale
        note = scale[value % scale_length]
        encoded_notes.append(note)
    return encoded_notes


cap = cv2.VideoCapture("/dev/video0")
ref_img = False
count = 0
calibration_frames = 150
print("starting loop", cap)
while cap.isOpened():
    if count < calibration_frames:
        count += 1
    # print("inside the loop")
    success, frame_img = cap.read()
    # frame = cv2.rotate(frame, cv2.ROTATE_180)

    if not success:
        print("Ignoring empty camera frame.")
        break

    if not ref_img:
        if count == 100:
            mask_bound = (0, 265, 640, 452)
            roi, cluster_dict_1, cluster_dict_2 = reference_frame(frame_img, mask_bound, "#C2C36F", "#DC6D99")
            # roi, cluster_dict_1 = reference_frame(frame_img, mask_bound, "#C8CE7B", "#699faf")
            ref_img = True
            frame_img = roi
            count += 1
            first_state = True

    elif (ref_img):
        if count < calibration_frames:
            print("calibrating...")
            if(first_state):
                frame_roi, error_keys_black, error_keys_white, error_lower_bound_1, error_upper_bound_1 = inference_frame_calibration(frame_img, mask_bound, "#C2C36F", "#DC6D99", cluster_dict_1, cluster_dict_2,
                                        roi, threshold=40)
                first_state = False

            else:
                frame_roi, error_keys_black, error_keys_white, error_lower_bound_1, error_upper_bound_1 = inference_frame_calibration(
                    frame_img, mask_bound, "#C2C36F", "#DC6D99", cluster_dict_1, cluster_dict_2,
                    roi, threshold=40, error_lower_bound=error_lower_bound_1, error_upper_bound=error_upper_bound_1,
                    initial_state=False)
                # for keys in error_keys_black:
                #     for i in cluster_dict_1[keys]:
                #         rows, columns = i
                #
                #         frame_roi[rows][columns][0] = 0
                #         frame_roi[rows][columns][1] = 0
                #         frame_roi[rows][columns][2] = 255
                #
                # for keys in error_keys_white:
                #     for i in cluster_dict_2[keys]:
                #         rows, columns = i
                #
                #         frame_roi[rows][columns][0] = 0
                #         frame_roi[rows][columns][1] = 255
                #         frame_roi[rows][columns][2] = 255
        else:
            frame_roi, error_keys_black, error_keys_white = inference_frame(frame_img, mask_bound, "#C2C36F", "#DC6D99",
                                                                        cluster_dict_1, cluster_dict_2, roi,
                                                                        threshold=40, error_lower_bound=error_lower_bound_1, error_upper_bound=error_upper_bound_1)
            encoded_notes_white = encode_to_scale(error_keys_white, white_keys)
            encoded_notes_black = encode_to_scale(error_keys_black, black_keys)
            all_notes = encoded_notes_white + encoded_notes_black
            if (all_notes):
                print("sending to socket: ", ' '.join(all_notes))
                socket.send_string(' '.join(all_notes))   
            # for keys in error_keys_black:
            #     for i in cluster_dict_1[keys]:
            #         rows, columns = i
            #
            #         frame_roi[rows][columns][0] = 0
            #         frame_roi[rows][columns][1] = 0
            #         frame_roi[rows][columns][2] = 255
            #
            # for keys in error_keys_white:
            #     for i in cluster_dict_2[keys]:
            #         rows, columns = i
            #
            #         frame_roi[rows][columns][0] = 0
            #         frame_roi[rows][columns][1] = 255
            #         frame_roi[rows][columns][2] = 255
            #
        cv2.waitKey(1)
        # cv2.imshow('Pressed Key Frame', frame_roi)


cap.release()
cv2.destroyAllWindows()
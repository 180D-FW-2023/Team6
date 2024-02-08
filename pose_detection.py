import cv2
import time
import math as m
import mediapipe as mp
import time

# Initilize medipipe selfie segmentation class.
mp_pose = mp.solutions.pose
mp_holistic = mp.solutions.holistic

def findDistance(x1, y1, x2, y2):
    dist = m.sqrt((x2-x1)**2+(y2-y1)**2)
    return dist

# Calculate angle.
def findAngle(x1, y1, x2, y2):
    theta = m.acos((y2 -y1)*(-y1) / (m.sqrt((x2 - x1)**2 + (y2 - y1)**2) * y1))
    degree = int(180/m.pi)*theta
    return degree

# calculate angle of arm
def findAngleArm(P1_x, P1_y, P2_x, P2_y, P3_x, P3_y):
    P12 = m.sqrt((P1_x - P2_x)**2 + (P1_y - P2_y)**2)
    P13 = m.sqrt((P1_x - P3_x)**2 + (P1_y - P3_y)**2)
    P23 = m.sqrt((P2_x - P3_x)**2 + (P2_y - P3_y)**2)
    theta = m.acos((P12**2 + P23**2 - P13**2) / (2 * P12 * P23))
    degree = int(180/m.pi)*theta
    return degree

def check_left_right(hand_x_cord, hip_x_cord):
    diff = hand_x_cord - hip_x_cord
    if diff < 0:
        # print("left_facing")
        return "left"
    else:
        # print("right_facing")
        return "right"
    
def sendWarning(x):
    pass

count = 0

# Font type.
font = cv2.FONT_HERSHEY_SIMPLEX
 
# Colors.
blue = (255, 127, 0)
red = (50, 50, 255)
green = (127, 255, 0)
dark_blue = (127, 20, 0)
light_green = (127, 233, 100)
yellow = (0, 255, 255)
pink = (255, 0, 255)
 
# Initialize mediapipe pose class.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

import paho.mqtt.client as mqtt
import numpy as np

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("ece180d/test")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')
    # The default message callback.
    # (won’t be used if only publishing, but can still exist)

def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
    message.topic + '" with QoS ' + str(message.qos))
    
# # 1. create a client instance.
# client = mqtt.Client()

# # add additional client options (security, certifications, etc.)
# # many default options should be good to start off.
# # add callbacks to client.
# client.on_connect = on_connect
# client.on_disconnect = on_disconnect
# client.on_message = on_message

# # 2. connect to a broker using one of the connect*() functions.
# client.connect_async('test.mosquitto.org')

# 3. call one of the loop*() functions to maintain network traffic flow with the broker.
# client.loop_start()

# # 4. use subscribe() to subscribe to a topic and receive messages.
# # 5. use publish() to publish messages to the broker.
# # payload must be a string, bytearray, int, float or None.
# for i in range(10):
#     client.publish('ece180d/test', float(np.random.random(1)), qos=1)
    
# # 6. use disconnect() to disconnect from the broker.
# client.loop_stop()
# client.disconnect()
    
#RUN THIS CELL

# 1. create a client instance.
client = mqtt.Client()

# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client.
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# 2. connect to a broker using one of the connect*() functions.
client.connect_async('test.mosquitto.org')

client.loop_start()
#cap = cv2.VideoCapture('C:\\Users\\17147\\Desktop\\College\\180DA\\input.mp4')
# cap = cv2.VideoCapture('C:\\Users\\17147\\Desktop\\College\\180DA\\sample1.mp4')
cap =  cv2.VideoCapture(0, cv2.CAP_DSHOW)

# start = time.time()
while cap.isOpened():
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    # Capture frames.
    success, frame = cap.read()

    if not success:
        print("Ignoring empty camera frame.")
        break
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert the BGR image to RGB.
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # To improve performance
    image.flags.writeable = False

    # Process the image.
    keypoints = pose.process(image)

    # Convert the image back to BGR.
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Use lm and lmPose as representative of the following methods.
    lm = keypoints.pose_landmarks
    lmPose = mp_pose.PoseLandmark

    """Getting the facing direction"""
    if count == 0:
        l_hip_x = int(lm.landmark[lmPose.LEFT_HIP].x * w)
        l_wrist_x = int(lm.landmark[lmPose.LEFT_WRIST].x * w)
        facing = check_left_right(l_wrist_x, l_hip_x)
        count += 1
    
    """Acquire the landmark coordinates depending on facing direction"""
    if facing == "left":
        # print("left")
        # Left shoulder.
        l_shldr_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
        l_shldr_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)
        # Right shoulder
        r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
        r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)
        # Left ear.
        l_ear_x = int(lm.landmark[lmPose.LEFT_EAR].x * w)
        l_ear_y = int(lm.landmark[lmPose.LEFT_EAR].y * h)
        # Left hip.
        l_hip_y = int(lm.landmark[lmPose.LEFT_HIP].y * h)
        l_hip_x = int(lm.landmark[lmPose.LEFT_HIP].x * w)
        # Left elbow
        l_elbw_y = int(lm.landmark[lmPose.LEFT_ELBOW].y * h)
        l_elbw_x = int(lm.landmark[lmPose.LEFT_ELBOW].x * w)
        # Left wrist
        l_wrst_y = int(lm.landmark[lmPose.LEFT_WRIST].y * h)
        l_wrst_x = int(lm.landmark[lmPose.LEFT_WRIST].x * w)


        # To improve performance
        image.flags.writeable = True

        cv2.circle(image, (l_shldr_x, l_shldr_y), 7, yellow, -1)
        cv2.circle(image, (l_ear_x, l_ear_y), 7, yellow, -1)
        cv2.circle(image, (l_shldr_x, l_shldr_y - 100), 7, yellow, -1)
        cv2.circle(image, (r_shldr_x, r_shldr_y), 7, pink, -1)
        cv2.circle(image, (l_hip_x, l_hip_y), 7, yellow, -1)
        cv2.circle(image, (l_hip_x, l_hip_y - 100), 7, yellow, -1)
        cv2.circle(image, (l_elbw_x, l_elbw_y), 7, yellow, -1)
        cv2.circle(image, (l_wrst_x, l_wrst_y), 7, yellow, -1)

        # Calculate angles.
        neck_inclination = findAngle(l_shldr_x, l_shldr_y, l_ear_x, l_ear_y)
        torso_inclination = findAngle(l_hip_x, l_hip_y, l_shldr_x, l_shldr_y)
        arm_inclination = findAngleArm(l_shldr_x, l_shldr_y, l_elbw_x, l_elbw_y, l_wrst_x, l_wrst_y)

        """Put text, Posture and angle inclination."""
        # Text string for display.
        angle_text_string = 'Neck : ' + str(int(neck_inclination)) + '  Torso : ' + str(int(torso_inclination))

        # Determine whether good posture or bad posture.
        if neck_inclination < 40 and torso_inclination < 10:
    
            cv2.putText(image, angle_text_string, (10, 30), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(neck_inclination)), (l_shldr_x + 10, l_shldr_y), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(torso_inclination)), (l_hip_x + 10, l_hip_y), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(arm_inclination)), (l_elbw_x + 10, l_elbw_y), font, 0.9, light_green, 2)
    
            # Join landmarks.
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_ear_x, l_ear_y), green, 4)
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_shldr_x, l_shldr_y - 100), green, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_shldr_x, l_shldr_y), green, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_hip_x, l_hip_y - 100), green, 4)
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_elbw_x, l_elbw_y), green, 4)
            cv2.line(image, (l_elbw_x, l_elbw_y), (l_wrst_x, l_wrst_y), green, 4)
    
        else:
    
            cv2.putText(image, angle_text_string, (10, 30), font, 0.9, red, 2)
            cv2.putText(image, str(int(neck_inclination)), (l_shldr_x + 10, l_shldr_y), font, 0.9, red, 2)
            cv2.putText(image, str(int(torso_inclination)), (l_hip_x + 10, l_hip_y), font, 0.9, red, 2)
            cv2.putText(image, str(int(arm_inclination)), (l_elbw_x + 10, l_elbw_y), font, 0.9, red, 2)
    
            # Join landmarks.
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_ear_x, l_ear_y), red, 4)
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_shldr_x, l_shldr_y - 100), red, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_shldr_x, l_shldr_y), red, 4)
            cv2.line(image, (l_hip_x, l_hip_y), (l_hip_x, l_hip_y - 100), red, 4)
            cv2.line(image, (l_shldr_x, l_shldr_y), (l_elbw_x, l_elbw_y), red, 4)
            cv2.line(image, (l_elbw_x, l_elbw_y), (l_wrst_x, l_wrst_y), red, 4)
        

    elif facing == "right":
        # print("right")
        l_shldr_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
        l_shldr_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)
        # Right shoulder
        r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
        r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)
        # Right ear
        r_ear_x = int(lm.landmark[lmPose.RIGHT_EAR].x * w)
        r_ear_y = int(lm.landmark[lmPose.RIGHT_EAR].y * h)
        # Right hip
        r_hip_y = int(lm.landmark[lmPose.RIGHT_HIP].y * h)
        r_hip_x = int(lm.landmark[lmPose.RIGHT_HIP].x * w)
        # Right elbow
        r_elbw_y = int(lm.landmark[lmPose.RIGHT_ELBOW].y * h)
        r_elbw_x = int(lm.landmark[lmPose.RIGHT_ELBOW].x * w)
        # Right wrist
        r_wrst_y = int(lm.landmark[lmPose.RIGHT_WRIST].y * h)
        r_wrst_x = int(lm.landmark[lmPose.RIGHT_WRIST].x * w)

        cv2.circle(image, (r_shldr_x, r_shldr_y), 7, yellow, -1)
        cv2.circle(image, (r_shldr_x, r_shldr_y - 100), 7, yellow, -1)
        cv2.circle(image, (r_ear_x, r_ear_y), 7, yellow, -1)
        cv2.circle(image, (l_shldr_x, l_shldr_y), 7, pink, -1)
        cv2.circle(image, (r_hip_x, r_hip_y), 7, yellow, -1)
        cv2.circle(image, (r_hip_x, r_hip_y - 100), 7, yellow, -1)
        cv2.circle(image, (r_elbw_x, r_elbw_y), 7, yellow, -1)
        cv2.circle(image, (r_wrst_x, r_wrst_y), 7, yellow, -1)

        # Calculate angles.
        neck_inclination = findAngle(r_shldr_x, r_shldr_y, r_ear_x, r_ear_y)
        torso_inclination = findAngle(r_hip_x, r_hip_y, r_shldr_x, r_shldr_y)
        arm_inclination = findAngleArm(r_shldr_x, r_shldr_y, r_elbw_x, r_elbw_y, r_wrst_x, r_wrst_y)
    
        """Put text, Posture and angle inclination."""
        # Text string for display.
        angle_text_string = 'Neck : ' + str(int(neck_inclination)) + '  Torso : ' + str(int(torso_inclination))

        # Determine whether good posture or bad posture.
        if neck_inclination < 40 and torso_inclination < 10:
    
            cv2.putText(image, angle_text_string, (10, 30), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(neck_inclination)), (r_shldr_x + 10, r_shldr_y), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(torso_inclination)), (r_hip_x + 10, r_hip_y), font, 0.9, light_green, 2)
            cv2.putText(image, str(int(arm_inclination)), (r_elbw_x + 10, r_elbw_y), font, 0.9, light_green, 2)
    
            # Join landmarks.
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_ear_x, r_ear_y), green, 4)
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_shldr_x, r_shldr_y - 100), green, 4)
            cv2.line(image, (r_hip_x, r_hip_y), (r_shldr_x, r_shldr_y), green, 4)
            cv2.line(image, (r_hip_x, r_hip_y), (r_hip_x, r_hip_y - 100), green, 4)
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_elbw_x, r_elbw_y), green, 4)
            cv2.line(image, (r_elbw_x, r_elbw_y), (r_wrst_x, r_wrst_y), green, 4)
    
        else:
    
            cv2.putText(image, angle_text_string, (10, 30), font, 0.9, red, 2)
            cv2.putText(image, str(int(neck_inclination)), (r_shldr_x + 10, r_shldr_y), font, 0.9, red, 2)
            cv2.putText(image, str(int(torso_inclination)), (r_hip_x + 10, r_hip_y), font, 0.9, red, 2)
            cv2.putText(image, str(int(arm_inclination)), (r_elbw_x + 10, r_elbw_y), font, 0.9, red, 2)
    
            # Join landmarks.
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_ear_x, r_ear_y), red, 4)
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_shldr_x, r_shldr_y - 100), red, 4)
            cv2.line(image, (r_hip_x, r_hip_y), (r_shldr_x, r_shldr_y), red, 4)
            cv2.line(image, (r_hip_x, r_hip_y), (r_hip_x, r_hip_y - 100), red, 4)
            cv2.line(image, (r_shldr_x, r_shldr_y), (r_elbw_x, r_elbw_y), red, 4)
            cv2.line(image, (r_elbw_x, r_elbw_y), (r_wrst_x, r_wrst_y), red, 4)
    
    client.publish('your_topic', int(neck_inclination), qos=1)
    if (torso_inclination < 10):
        client.publish('your_topic', "Your torso is too forward, please lean back to a straight position", qos=1)
    if (neck_inclination < 10):
        client.publish('your_topic', "Your neck is too forward, please lean back to a straight position", qos=1) 
    cv2.imshow('Raw Webcam Feed', image)
    cv2.waitKey(1)

    if cv2.getWindowProperty('Raw Webcam Feed', cv2.WND_PROP_VISIBLE) < 1:
        break
    
# end = time.time()
# print(end - start)
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
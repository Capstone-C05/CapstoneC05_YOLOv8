from ultralytics import YOLO
import time
import cv2
import settings
import pandas as pd

from PIL import Image
import cv2
import numpy as np

from utils import calculate_iou

first_frame = True

# Initialize
breach_frequency = {}
prev_active_breachers = set()

def load_model(model_path):
    """
    Loads a YOLO object detection model from the specified model_path.

    Parameters:
        model_path (str): The path to the YOLO model file.

    Returns:
        A YOLO object detection model.
    """
    model = YOLO(model_path)

    return model

def display_tracker_options():
    display_tracker = 'No' #st.radio("Display Tracker", ('Yes', 'No'))
    is_display_tracker = True if display_tracker == 'Yes' else False
    if is_display_tracker:
        tracker_type = None#st.radio("Tracker", ("bytetrack.yaml", "botsort.yaml"))
        return is_display_tracker, tracker_type
    return is_display_tracker, None#

def _display_detected_frames(conf, model, st_frame, image, dz_box, is_display_tracking=None, tracker=None, first_frame_flag = False):
    """
    Display the detected objects on a video frame using the YOLOv8 model.

    Args:
    - conf (float): Confidence threshold for object detection.
    - model (YoloV8): A YOLOv8 object detection model.
    - st_frame (Streamlit object): A Streamlit object to display the detected video.
    - image (numpy array): A numpy array representing the video frame.
    - is_display_tracking (bool): A flag indicating whether to display object tracking (default=None).

    Returns:
    None
    """
    
    W, H = (1280, int(1280*(9/16)))
    # Resize the image to a standard size
    image = cv2.resize(image, (W, H))
    
def play_webcam(conf, model):
    """
    Plays a webcam stream. Detects Objects in real-time using the YOLOv8 object detection model.

    Parameters:
        conf: Confidence of YOLOv8 model.
        model: An instance of the `YOLOv8` class containing the YOLOv8 model.

    Returns:
        None

    Raises:
        None
    """
    source_webcam = settings.WEBCAM_PATH #source webcam
    is_display_tracker, tracker = display_tracker_options()
    
    print("Select Danger Zone:")
    print("Draw your polygon on the canvas below:")
    
    bg_video = source_webcam #background for drawing the polygon
    drawing_mode = "polygon"
    stroke_width =  3
    stroke_color = "#000000"
    bg_color = "#eee"
    DZ_BOX = 0,0,0,0,0,0,0,0 #For storing polygon coordinates (4)
    
    # Initialize video capture
    video_capture = None
    frame_width = 0
    frame_height = 0
    
    video_capture = cv2.VideoCapture(bg_video)
    # Check if the video file was successfully opened
     #global first_frame
    if video_capture.isOpened():
        # Read the first frame
        ret, frame = video_capture.read()
        video_capture.release()
        first_frame_webcam = frame

    frame_width, frame_height = (1280, int(1280*(9/16)))
    canvas_width = frame_width
    canvas_height = frame_height

    # Convert BGR frame to RGB format
    frame_rgb = cv2.cvtColor(first_frame_webcam, cv2.COLOR_BGR2RGB)
    canvas_background_image = Image.fromarray(frame_rgb)
    
    flag = False 
    points = []
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            if len(points) > 1:
                cv2.line(frame, points[-2], points[-1], (0, 255, 0), 1)
        cv2.imshow("Video Stream", frame)
        flags = True
        
    cv2.namedWindow("Video Stream")
    cv2.setMouseCallback("Video Stream", mouse_callback)
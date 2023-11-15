# Python In-built packages
from pathlib import Path
import PIL
import PyQt6

# External packages
#import streamlit as st

# Local Modules
import settings
import helper

# Setting page layout

# Sidebar
#st.sidebar.header("ML Model Config")

# Model Options
model_type = 'Detection' #st.sidebar.radio("Select Task", ['Detection', 'Segmentation'])

confidence = 0.2#float(st.sidebar.slider("Select Model Confidence (%)", 0, 100, 30)) / 100

iou_threshold = 0.01#float(st.sidebar.slider("Select IoU Threshold (%)", 25, 100, 5)) / 100

# Selecting Detection Or Segmentation
if model_type == 'Detection':
    model_path = Path(settings.DETECTION_MODEL)
#elif model_type == 'Segmentation':
#    model_path = Path(settings.SEGMENTATION_MODEL)

# Load Pre-trained ML Model
try:
    model = helper.load_model(model_path)
except Exception as ex:
    print("Could not load model")
    #st.error(f"Unable to load model. Check the specified path: {model_path}")
    #st.error(ex)

#st.sidebar.header("Image/Video Config")
# 
source_stream = settings.WEBCAM #st.sidebar.radio("Select Source", settings.SOURCES_LIST)

#source_img = None
# If image is selected
# Execute helper function upon selection of a radio button
if source_stream == settings.VIDEO:
    print("Selected Stored Video")
    helper.play_stored_video(confidence, model)

elif source_stream == settings.WEBCAM:
    print("Selected Webcam")
    helper.play_webcam(confidence, model)

else:
    print("Please select a valid source type!")
    #st.error("Please select a valid source type!")

import cv2
import torch
import numpy as np
from ultralytics import YOLO
from torchreid.utils import FeatureExtractor

# YOLOv8 for person detection
yolo_model = YOLO("yolov8n.pt")

# TorchReID for person re-identification
extractor = FeatureExtractor(
    model_name='osnet_x1_0', 
    model_path='osnet_x1_0_imagenet.pth',  # download from TorchReID repo
    device='cuda' if torch.cuda.is_available() else 'cpu'
)

def detect_person_in_frame(frame, target_image_path, threshold=0.5):
    """
    frame: single video frame
    target_image_path: path to uploaded person image
    returns: (match_found: bool, annotated_frame)
    """
    frame_small = cv2.resize(frame, (640, 360))
    
    # Detect people
    results = yolo_model(frame_small)
    detections = results[0].boxes.xyxy
    classes = results[0].boxes.cls

    # Extract feature of target person
    target_feature = extractor(target_image_path)

    best_match_score = 0
    best_box = None

    for i, cls in enumerate(classes):
        if int(cls) != 0:  # person class
            continue

        x1, y1, x2, y2 = map(int, detections[i])
        person_crop = frame_small[y1:y2, x1:x2]
        
        # Skip if box is too small
        if person_crop.shape[0] < 20 or person_crop.shape[1] < 20:
            continue

        person_feature = extractor(person_crop)

        # Cosine similarity
        sim = np.dot(target_feature, person_feature.T) / (np.linalg.norm(target_feature) * np.linalg.norm(person_feature))

        if sim > best_match_score:
            best_match_score = sim
            best_box = (x1, y1, x2, y2)

    if best_box and best_match_score >= threshold:
        # Rescale box to original frame size
        scale_x = frame.shape[1] / 640
        scale_y = frame.shape[0] / 360
        x1, y1, x2, y2 = best_box
        cv2.rectangle(frame,
                      (int(x1*scale_x), int(y1*scale_y)),
                      (int(x2*scale_x), int(y2*scale_y)),
                      (0, 255, 0), 3)
        return True, frame

    return False, frame

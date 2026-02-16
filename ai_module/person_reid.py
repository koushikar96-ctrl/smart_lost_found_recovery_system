from torchreid.reid.utils import FeatureExtractor
import cv2
import numpy as np
from ultralytics import YOLO
import torch

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# YOLOv8 person detector
yolo_model = YOLO("yolov8n.pt")
yolo_model.to(DEVICE)
PERSON_CLASS_ID = 0

# TorchReID extractor
extractor = FeatureExtractor(model_name='osnet_x1_0', device=DEVICE)

def cosine_similarity(feat1, feat2):
    feat1 = feat1.flatten()
    feat2 = feat2.flatten()
    return np.dot(feat1, feat2) / (np.linalg.norm(feat1) * np.linalg.norm(feat2))

def detect_and_match_person(frame, query_feature, prev_features, threshold=0.5):
    """
    Detect only the person in query_feature in the video frame.
    Returns:
        is_match_found: bool
        annotated_frame: frame with bounding box
        updated_features: list of matched features (to avoid duplicates)
        max_similarity: max similarity score in this frame
    """
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = yolo_model(frame_rgb, classes=[PERSON_CLASS_ID], conf=0.25)

    annotated_frame = frame.copy()
    updated_features = prev_features.copy()
    is_match = False
    max_similarity = 0.0

    if results[0].boxes is None or len(results[0].boxes.xyxy) == 0:
        return is_match, annotated_frame, updated_features, max_similarity

    for box in results[0].boxes.xyxy.cpu().numpy():
        x1, y1, x2, y2 = map(int, box)
        person_crop = frame[y1:y2, x1:x2]

        # Skip tiny crops
        if person_crop.shape[0] < 20 or person_crop.shape[1] < 20:
            continue

        # Resize for extractor
        person_crop_resized = cv2.resize(person_crop, (128, 256))

        # Extract feature for detected person
        person_feat = extractor([person_crop_resized])[0]
        sim = cosine_similarity(query_feature, person_feat)
        max_similarity = max(max_similarity, sim)

        # Only match if similarity is above threshold AND not duplicate
        if sim >= threshold:
            duplicate = any(cosine_similarity(f, person_feat) >= threshold for f in prev_features)
            if not duplicate:
                is_match = True
                updated_features.append(person_feat)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Match {sim:.2f}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                break  # only one person per frame

    return is_match, annotated_frame, updated_features, max_similarity

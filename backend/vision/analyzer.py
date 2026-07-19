import warnings
from typing import Dict, Any

import cv2
import numpy as np

from backend import config


class VisionAnalyzer:
    def __init__(self):
        self.available = False
        try:
            from mediapipe import Image, ImageFormat
            from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarker
            from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarker

            import os as _os
            _model_dir = _os.path.join(_os.path.dirname(__file__), "models")
            _face_model = _os.path.join(_model_dir, "face_landmarker.task")
            _hand_model = _os.path.join(_model_dir, "hand_landmarker.task")

            if not (_os.path.exists(_face_model) and _os.path.exists(_hand_model)):
                warnings.warn("MediaPipe model files not found in backend/vision/models/. Vision disabled.")
                self.face_mesh = None
                self.hands = None
                return

            self.face_mesh = FaceLandmarker.create_from_model_path(_face_model)
            self.hands = HandLandmarker.create_from_model_path(_hand_model)
            self.available = True
        except Exception as e:
            warnings.warn(f"Vision analyzer init failed: {e}. Vision disabled.")

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        result = {
            "face_detected": False,
            "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0},
            "eye_contact": False,
            "mouth_open": False,
            "hand_gestures": False,
            "landmarks": None,
        }
        if not self.available:
            return result

        from mediapipe import Image, ImageFormat
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        h, w = frame.shape[:2]

        face_result = self.face_mesh.detect(mp_image)
        hands_result = self.hands.detect(mp_image)

        if face_result.face_landmarks:
            landmarks = face_result.face_landmarks[0]
            result["face_detected"] = True
            result["landmarks"] = self._extract_landmarks(landmarks, w, h)

            nose_tip = landmarks[1]
            left_eye = landmarks[33]
            right_eye = landmarks[263]
            chin = landmarks[152]
            forehead = landmarks[10]

            yaw = np.degrees(np.arctan2(
                nose_tip.x - (left_eye.x + right_eye.x) / 2,
                forehead.x - chin.x
            ))
            pitch = np.degrees(np.arctan2(
                nose_tip.y - (forehead.y + chin.y) / 2,
                abs(forehead.x - chin.x)
            ))
            result["head_pose"]["yaw"] = round(yaw, 1)
            result["head_pose"]["pitch"] = round(pitch, 1)

            result["eye_contact"] = abs(yaw) < 20 and abs(pitch) < 15

            upper_lip = landmarks[13]
            lower_lip = landmarks[14]
            mouth_dist = abs(upper_lip.y - lower_lip.y) * h
            result["mouth_open"] = mouth_dist > 8

        if hands_result.hand_landmarks:
            result["hand_gestures"] = True

        return result

    def _extract_landmarks(self, landmarks, w: int, h: int) -> list:
        return [
            {"x": lm.x * w, "y": lm.y * h, "z": lm.z}
            for lm in landmarks
        ]

    def draw_overlay(self, frame: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        if analysis["face_detected"] and analysis["landmarks"]:
            for lm in analysis["landmarks"]:
                cv2.circle(frame, (int(lm["x"]), int(lm["y"])), 1, (0, 255, 0), -1)

            color = (0, 255, 0) if analysis["eye_contact"] else (0, 0, 255)
            cv2.putText(
                frame,
                f"Eye Contact: {analysis['eye_contact']}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )
            cv2.putText(
                frame,
                f"Head: yaw={analysis['head_pose']['yaw']:.0f} pitch={analysis['head_pose']['pitch']:.0f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
        return frame

    def close(self):
        self.face_mesh.close()
        self.hands.close()

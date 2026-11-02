"""
Machine Learning Service Module for CaneCare AI.

This module isolates all sugarcane disease inference logic:
- MODE 1 (Default / Mock): When no trained model file exists in `models/`,
  it generates realistic, mathematically valid probabilities with a dominant class
  and logs a warning: "Using MOCK model".
- MODE 2 (Real Model): If `models/sugarcane_model.h5` or a `.tflite` file is present,
  it attempts to load it using TensorFlow, resizes to 224x224, normalizes (0-1),
  and returns real model outputs. If TensorFlow is missing, it falls back to Mock.
"""

import os
import glob
import logging
import random
from typing import List, Dict, Any
from PIL import Image
from app.config import settings

logger = logging.getLogger("canecare.ml")

# Disease classes supported by the CaneCare AI model
CLASSES: List[str] = ["healthy", "red_rot", "rust", "yellow_leaf", "mosaic"]

# Human-readable English display names for classes
DISPLAY_NAMES: Dict[str, str] = {
    "healthy": "Healthy Leaf",
    "red_rot": "Red Rot Disease",
    "rust": "Sugarcane Rust",
    "yellow_leaf": "Yellow Leaf Disease",
    "mosaic": "Sugarcane Mosaic Virus",
}


class MLService:
    def __init__(self, model_dir: str = settings.MODEL_DIR):
        self.model_dir = model_dir
        self.model_path = None
        self.model = None
        self.is_real_model = False
        self.model_version = "mock-v1.0.0"

        self._initialize_model()

    def _initialize_model(self):
        """Check for existing trained model weights and initialize accordingly."""
        # Check for .h5, .keras, or .tflite files in model_dir
        h5_candidates = glob.glob(os.path.join(self.model_dir, "*.h5"))
        keras_candidates = glob.glob(os.path.join(self.model_dir, "*.keras"))
        tflite_candidates = glob.glob(os.path.join(self.model_dir, "*.tflite"))

        all_candidates = h5_candidates + keras_candidates + tflite_candidates

        if all_candidates:
            self.model_path = all_candidates[0]
            logger.info(f"Found model file: {self.model_path}. Attempting to load with TensorFlow...")
            try:
                # Import TensorFlow dynamically ONLY when a model file is detected
                import tensorflow as tf

                if self.model_path.endswith(".tflite"):
                    # Load TFLite model
                    self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
                    self.interpreter.allocate_tensors()
                    self.input_details = self.interpreter.get_input_details()
                    self.output_details = self.interpreter.get_output_details()
                    self.is_real_model = True
                    self.model_version = f"tflite-{os.path.basename(self.model_path)}"
                    logger.info("Successfully loaded TFLite model!")
                else:
                    # Load Keras/H5 model
                    self.model = tf.keras.models.load_model(self.model_path)
                    self.is_real_model = True
                    self.model_version = f"keras-{os.path.basename(self.model_path)}"
                    logger.info("Successfully loaded Keras/H5 model!")
            except ImportError:
                logger.warning(
                    "WARNING: Model file exists, but TensorFlow is not installed in the environment! "
                    "To use real model inference, install TensorFlow with: pip install tensorflow\n"
                    "Falling back to MOCK model."
                )
                self.is_real_model = False
                self.model_version = "mock-v1.0.0"
            except Exception as e:
                logger.error(f"Error loading model from {self.model_path}: {e}. Falling back to MOCK model.")
                self.is_real_model = False
                self.model_version = "mock-v1.0.0"
        else:
            logger.warning(
                "Using MOCK model: No trained model weights found in 'models/' directory. "
                "Returning realistic simulated predictions for development and testing."
            )
            self.is_real_model = False
            self.model_version = "mock-v1.0.0"

    def predict(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Run inference on a PIL leaf image.
        Returns top-3 predictions formatted as:
        [
            {"label": "rust", "display_name": "Sugarcane Rust", "score": 0.912},
            {"label": "red_rot", "display_name": "Red Rot Disease", "score": 0.054},
            {"label": "healthy", "display_name": "Healthy Leaf", "score": 0.021}
        ]
        """
        if self.is_real_model:
            return self._predict_real(image)
        else:
            return self._predict_mock(image)

    def _predict_real(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Preprocess image and execute inference using loaded TensorFlow model."""
        try:
            import numpy as np
        except ImportError:
            logger.warning("NumPy is required for real model inference. Falling back to MOCK.")
            return self._predict_mock(image)

        # Convert to RGB, resize to standard 224x224
        img = image.convert("RGB").resize((224, 224))
        img_array = np.array(img, dtype=np.float32) / 255.0  # Normalize to [0, 1]
        img_batch = np.expand_dims(img_array, axis=0)

        if hasattr(self, "interpreter"):
            # TFLite inference
            self.interpreter.set_tensor(self.input_details[0]["index"], img_batch)
            self.interpreter.invoke()
            raw_scores = self.interpreter.get_tensor(self.output_details[0]["index"])[0]
        else:
            # Keras model inference
            raw_scores = self.model.predict(img_batch)[0]

        # Map to class scores
        scored_classes = []
        for i, class_name in enumerate(CLASSES):
            score = float(raw_scores[i]) if i < len(raw_scores) else 0.0
            scored_classes.append({
                "label": class_name,
                "display_name": DISPLAY_NAMES.get(class_name, class_name),
                "score": round(score, 4)
            })

        # Sort descending by score and pick top 3
        scored_classes.sort(key=lambda x: x["score"], reverse=True)
        return scored_classes[:3]

    def _predict_mock(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Generate a realistic simulated prediction.
        Chooses a primary class with high/moderate confidence (e.g. 0.78 to 0.96)
        and distributes the remaining probability among other classes.
        """
        # Pick one dominant class randomly
        primary_class = random.choice(CLASSES)
        primary_score = round(random.uniform(0.78, 0.95), 4)

        remaining_classes = [c for c in CLASSES if c != primary_class]
        random.shuffle(remaining_classes)

        # Distribute leftover probability
        remainder = round(1.0 - primary_score, 4)
        second_score = round(remainder * random.uniform(0.60, 0.85), 4)
        third_score = round(remainder - second_score, 4)

        results = [
            {
                "label": primary_class,
                "display_name": DISPLAY_NAMES.get(primary_class, primary_class),
                "score": primary_score,
            },
            {
                "label": remaining_classes[0],
                "display_name": DISPLAY_NAMES.get(remaining_classes[0], remaining_classes[0]),
                "score": second_score,
            },
            {
                "label": remaining_classes[1],
                "display_name": DISPLAY_NAMES.get(remaining_classes[1], remaining_classes[1]),
                "score": third_score,
            },
        ]
        return results


# Global singleton instance of MLService
ml_service = MLService()


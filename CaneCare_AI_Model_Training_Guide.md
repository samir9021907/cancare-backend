# 🌾 CaneCare AI - Sugarcane Disease ML Model Training Specification

This technical specification document is prepared for the **Machine Learning Engineer / Developer** who will train the Sugarcane Foliar Disease Detection model for **CaneCare AI**.

---

## 1. Executive Summary & Objective

The objective is to train a high-accuracy, lightweight deep learning computer vision model that accurately classifies sugarcane leaf diseases from camera photos taken under real-world agricultural conditions.

The trained model will be integrated directly into the **CaneCare AI FastAPI backend** and **Flutter Mobile App**.

---

## 2. Target Classes & Exact Label Requirements

The model **must strictly classify into these 5 classes**. The exact lowercase `snake_case` names below must be used in the dataset folders and output mapping, as the production backend maps them directly to multilingual advisories and agricultural treatment plans:

| Index | Exact Label (Folder Name) | Disease Name (English / Marathi) | Pathogen / Cause |
|:---:|---|---|---|
| **0** | `healthy` | Healthy Sugarcane (निरोगी ऊस) | No Disease / Normal Leaf |
| **1** | `red_rot` | Red Rot (लाल कुज रोग) | *Colletotrichum falcatum* |
| **2** | `rust` | Sugarcane Rust (तांबेरा रोग) | *Puccinia melanocephala* |
| **3** | `yellow_leaf` | Yellow Leaf Disease (पिवळा पान रोग) | *Sugarcane Yellow Leaf Virus (SCYLV)* |
| **4** | `mosaic` | Mosaic Virus (काणी / मोझॅक) | *Sugarcane Mosaic Virus (SCMV)* |

> ⚠️ **Important**: Do not use custom names like `Class_1`, `RedRot`, or `disease_0`. The labels must match `healthy`, `red_rot`, `rust`, `yellow_leaf`, `mosaic`.

---

## 3. Dataset & Preprocessing Specifications

1. **Recommended Dataset Size**: 
   - Minimum **250 to 500 images per class** (Total: 1,500 – 2,500+ images).
   - Standard datasets on Kaggle (e.g. *Sugarcane Leaf Disease Dataset*, *PlantVillage Sugarcane*) can be utilized.
2. **Input Image Resolution**: `224 x 224 x 3` (RGB).
3. **Train / Validation Split**: 80% Training, 20% Validation.
4. **Data Augmentation**:
   - Random Horizontal & Vertical Flip
   - Random Rotation ($\pm 25^{\circ}$)
   - Random Zoom (15%) & Shift (15%)
   - Random Brightness and Contrast adjustments ($\pm 15\%$) to mimic outdoor sunlight/shadows.

---

## 4. Recommended Architecture & Hyperparameters

| Component | Specification | Reason |
|---|---|---|
| **Base Model** | **MobileNetV2** (pre-trained on ImageNet) | Extremely lightweight (< 20MB), low RAM, fast inference (< 100ms on mobile CPU). |
| **Alternative** | EfficientNetB0 or ResNet50 | Also supported if higher accuracy is needed. |
| **Input Shape** | `(224, 224, 3)` | Standard pre-trained input tensor. |
| **Classification Head** | `GlobalAveragePooling2D` ➔ `Dropout(0.3)` ➔ `Dense(5, activation='softmax')` | Mitigates overfitting. |
| **Loss Function** | `CategoricalCrossentropy` | Multi-class probability distribution. |
| **Optimizer** | `Adam(learning_rate=1e-4)` | Stable convergence with transfer learning. |
| **Target Metric** | **Validation Accuracy $\ge$ 92%** | High diagnostic reliability for farmers. |

---

## 5. Ready-to-Run Training Script (Google Colab / Python)

The developer can copy and paste this complete code directly into **Google Colab** (Runtime: Python 3 with free T4 GPU):

```python
import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

# 1. Dataset Configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
DATASET_DIR = "sugarcane_dataset/" # Must contain healthy/, red_rot/, rust/, yellow_leaf/, mosaic/

train_datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    rotation_range=25,
    width_shift_range=0.15,
    height_shift_range=0.15,
    shear_range=0.15,
    zoom_range=0.15,
    horizontal_flip=True,
    vertical_flip=True,
    validation_split=0.20
)

train_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

val_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

# 2. Build MobileNetV2 Transfer Learning Model
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False # Freeze base weights for initial training

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
predictions = Dense(5, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(
    optimizer=Adam(learning_rate=1e-4),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# 3. Callbacks & Training
callbacks = [
    ModelCheckpoint('canecare_model.h5', monitor='val_accuracy', save_best_only=True, verbose=1),
    EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
]

print("🚀 Starting Initial Training (Frozen Base)...")
history = model.fit(
    train_generator,
    epochs=15,
    validation_data=val_generator,
    callbacks=callbacks
)

# 4. Fine-Tuning Top Layers
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(optimizer=Adam(learning_rate=1e-5), loss='categorical_crossentropy', metrics=['accuracy'])
print("🚀 Fine-Tuning Top Layers...")
model.fit(train_generator, epochs=10, validation_data=val_generator, callbacks=callbacks)

# 5. Convert to TensorFlow Lite (.tflite) for Mobile
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open('canecare_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("🎉 Model successfully exported: canecare_model.h5 and canecare_model.tflite")
```

---

## 6. Deliverables Required from Developer (ZIP File Contents)

Please request the developer to provide a single **ZIP file** with the following contents:

1. `canecare_model.h5` (or `canecare_model.keras`) — Primary weights file for the backend.
2. `canecare_model.tflite` — Quantized mobile inference model.
3. `classes.json` — Class index mapping:
   ```json
   {
     "0": "healthy",
     "1": "mosaic",
     "2": "red_rot",
     "3": "rust",
     "4": "yellow_leaf"
   }
   ```
4. `metrics_summary.txt` — Final test accuracy, precision, and recall scores.

---

## 7. How We Integrate the Deliverable into CaneCare AI

Once you receive the ZIP file from the developer:
1. Provide the ZIP or model file to me.
2. I will place it into: `canecare-backend/models/canecare_model.h5`.
3. The CaneCare AI server will immediately and automatically detect the model, turn off Mock Mode, and activate **Real AI Predictions**!

---
*CaneCare AI © 2026 • Sugarcane Leaf Disease Detection System*

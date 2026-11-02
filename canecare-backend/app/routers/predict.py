"""
Prediction Router (/api/v1/predict).

Receives leaf image uploads from authenticated farmers, validates format and size,
runs ML inference (or mock model), calculates confidence bands and severity,
persists scan history, and returns treatment advice.
"""

import io
import os
import uuid
import json
import logging
from typing import Optional
from PIL import Image

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security
from app.config import settings
from app.services.ml_service import ml_service
from app.services.shop_service import get_recommended_medicines, find_nearest_shops, resolve_farmer_location

logger = logging.getLogger("canecare.predict")

router = APIRouter(prefix="/api/v1/predict", tags=["Prediction"])

# Allowed MIME types and file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit

# Load disease dictionary
DISEASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "disease_data.json")


def get_disease_guidance(label: str, lang: str) -> schemas.DiseaseGuidance:
    """Retrieve treatment guidance for a specific disease in the given language."""
    try:
        with open(DISEASE_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        diseases = data.get("diseases", {})
        translations = diseases.get(label, {})
        info = translations.get(lang, translations.get("en", {}))
        return schemas.DiseaseGuidance(
            symptoms=info.get("symptoms", []),
            causes=info.get("causes", []),
            treatment=info.get("treatment", []),
            prevention=info.get("prevention", []),
            disclaimer=info.get("disclaimer", data.get("notice", ""))
        )
    except Exception as e:
        logger.error(f"Error fetching disease guidance: {e}")
        return schemas.DiseaseGuidance(
            symptoms=[],
            causes=[],
            treatment=["Consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer."],
            prevention=["Use certified disease-free seed canes."],
            disclaimer="All advisory content should be confirmed with an agricultural officer."
        )


def calculate_severity(label: str, confidence: float) -> str:
    """
    Calculate severity level.
    - Healthy leaves return severity "none".
    - Diseased leaves return "low", "medium", or "high".
    # TODO: Real severity estimation will be computed later using leaf lesion area segmentation.
    """
    if label == "healthy":
        return "none"

    if label in ["red_rot", "yellow_leaf"]:
        return "high" if confidence > 0.85 else "medium"
    else:  # rust, mosaic
        return "medium" if confidence > 0.80 else "low"


@router.post(
    "",
    response_model=schemas.PredictResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload sugarcane leaf photo for disease diagnosis",
    description="Upload a sugarcane leaf image (JPG/JPEG/PNG up to 10MB) to receive instant disease diagnosis and treatment advice."
)
async def predict_leaf(
    request: Request,
    file: UploadFile = File(..., description="Sugarcane leaf photo (JPG/PNG max 10MB)"),
    language: Optional[str] = Form(None, description="Preferred response language (en, mr, hi)"),
    latitude: Optional[float] = Form(None, description="Farmer GPS latitude (optional, auto-detected from location if omitted)"),
    longitude: Optional[float] = Form(None, description="Farmer GPS longitude"),
    pincode: Optional[str] = Form(None, description="Postal pincode"),
    district: Optional[str] = Form(None, description="Farmer district (e.g. Kolhapur, Sangli, Ahilyanagar)"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{file_ext}'. Only JPG, JPEG, and PNG images are supported."
        )

    # 2. Read file content and validate size (10 MB max)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10 MB limit. Please compress or resize the image."
        )

    # 3. Validate image integrity using Pillow
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()  # Verifies image header and integrity
        # Re-open image because verify() closes the file stream
        image = Image.open(io.BytesIO(content))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid or readable image. Please upload a clear photo."
        )

    # 4. Save image to uploads folder with unique UUID filename
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    saved_rel_path = os.path.join(settings.UPLOAD_DIR, unique_filename).replace("\\", "/")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(saved_rel_path, "wb") as f_out:
        f_out.write(content)

    # 5. Run ML inference (or mock model)
    top3_raw = ml_service.predict(image)
    best_match = top3_raw[0]
    label = best_match["label"]
    confidence = best_match["score"]

    # 6. Determine confidence band & status
    if confidence < 0.70:
        status_text = "low_confidence"
        confidence_band = "low"
        user_message = (
            "Confidence is too low (< 70%). The photo may be blurry, poorly lit, or not a sugarcane leaf. "
            "Please retake a clear photo under natural sunlight focusing directly on the leaf symptoms."
        )
    elif confidence <= 0.85:
        status_text = "success"
        confidence_band = "moderate"
        user_message = "Moderate confidence diagnosis. We advise confirming symptoms with a local agricultural extension officer."
    else:
        status_text = "success"
        confidence_band = "high"
        user_message = "High confidence diagnosis based on visible visual symptoms."

    # 7. Calculate severity
    severity = calculate_severity(label, confidence)

    # 8. Create database records (Scan and Prediction)
    new_scan = models.Scan(
        user_id=current_user.id,
        image_path=saved_rel_path
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    new_pred = models.Prediction(
        scan_id=new_scan.id,
        class_label=label,
        confidence=confidence,
        severity=severity,
        top3=top3_raw,
        model_version=ml_service.model_version
    )
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    # 9. Format response
    target_lang = language if language in ["en", "mr", "hi"] else (current_user.language or "en")

    if status_text == "low_confidence":
        # Under low confidence, do not provide a definitive diagnosis or treatment
        return schemas.PredictResponse(
            scan_id=new_scan.id,
            status=status_text,
            message=user_message,
            prediction=None,
            guidance=None,
            model_version=ml_service.model_version,
            disclaimer=True
        )

    # Format top3 items
    top3_items = [
        schemas.Top3Item(
            label=item["label"],
            display_name=item["display_name"],
            score=item["score"]
        ) for item in top3_raw
    ]

    prediction_detail = schemas.PredictionDetail(
        label=label,
        display_name=best_match["display_name"],
        confidence=confidence,
        confidence_band=confidence_band,
        severity=severity,
        top3=top3_items
    )

    guidance = get_disease_guidance(label, target_lang)

    # 10. Dynamically resolve farmer's live location (GPS or IP auto-detection)
    client_ip = request.client.host if request.client else None
    farmer_loc = resolve_farmer_location(
        user_lat=latitude,
        user_lon=longitude,
        client_ip=client_ip
    )

    # 11. Recommend medicines and nearest agro-medical stores
    medicines_raw = get_recommended_medicines(label, target_lang)
    medicines = [schemas.MedicineItem(**m) for m in medicines_raw]

    shops_raw = find_nearest_shops(
        user_lat=farmer_loc["latitude"],
        user_lon=farmer_loc["longitude"],
        pincode=pincode or farmer_loc.get("pincode"),
        district=district or farmer_loc.get("district"),
        limit=3
    )
    nearest_shops = [schemas.AgroShopItem(**s) for s in shops_raw]

    return schemas.PredictResponse(
        scan_id=new_scan.id,
        status=status_text,
        message=user_message,
        prediction=prediction_detail,
        guidance=guidance,
        medicines=medicines,
        farmer_location=schemas.FarmerLocationInfo(**farmer_loc),
        nearest_medical_shops=nearest_shops,
        model_version=ml_service.model_version,
        disclaimer=True
    )


"""
Scan History Router (/api/v1/history and /api/v1/scans).

Endpoints:
- GET /history?filter=all|healthy|diseased&page=1&limit=10 : Paginated list of scans for the current user
- GET /history/{scan_id} : Detailed scan prediction and advisory
- DELETE /scans/{scan_id} : Delete scan record and remove physical image file from storage
"""

import os
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security
from app.services.ml_service import DISPLAY_NAMES
from app.services.shop_service import get_recommended_medicines, find_nearest_shops

logger = logging.getLogger("canecare.history")

router = APIRouter(tags=["History & Scans"])

# Path to the multilingual disease data
DISEASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "disease_data.json")


def make_media_url(file_path: str) -> str:
    """Convert an internal file path (e.g. ./uploads/leaf.jpg) to a public URL path (/media/leaf.jpg)."""
    filename = os.path.basename(file_path)
    return f"/media/{filename}"


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
            treatment=["Consult local Krishi Vigyan Kendra."],
            prevention=["Use certified seed."],
            disclaimer="Consult local agriculture officers."
        )


@router.get(
    "/api/v1/history",
    response_model=schemas.HistoryResponse,
    summary="List past leaf scans",
    description="Retrieve paginated scan history for the logged-in user, sorted newest first."
)
def list_history(
    filter: str = Query("all", pattern="^(all|healthy|diseased)$"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    query = (
        db.query(models.Scan)
        .outerjoin(models.Prediction, models.Scan.id == models.Prediction.scan_id)
        .filter(models.Scan.user_id == current_user.id)
    )

    if filter == "healthy":
        query = query.filter(models.Prediction.class_label == "healthy")
    elif filter == "diseased":
        query = query.filter(models.Prediction.class_label != "healthy", models.Prediction.class_label.isnot(None))

    total = query.count()
    offset = (page - 1) * limit
    scans = query.order_by(models.Scan.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for s in scans:
        pred = s.prediction
        label = pred.class_label if pred else "unknown"
        display = DISPLAY_NAMES.get(label, label)
        confidence = pred.confidence if pred else 0.0
        severity = pred.severity if pred else "none"

        # Calculate confidence band
        if confidence < 0.70:
            band = "low"
        elif confidence <= 0.85:
            band = "moderate"
        else:
            band = "high"

        items.append(
            schemas.HistoryItem(
                scan_id=s.id,
                image_url=make_media_url(s.image_path),
                disease=label,
                display_name=display,
                confidence=confidence,
                confidence_band=band,
                severity=severity,
                created_at=s.created_at
            )
        )

    return schemas.HistoryResponse(
        total=total,
        page=page,
        limit=limit,
        items=items
    )


@router.get(
    "/api/v1/history/{scan_id}",
    response_model=schemas.ScanDetailResponse,
    summary="Get details for a specific scan",
    description="Returns detailed prediction metrics and management guidance for a single scan belonging to the user."
)
def get_scan_detail(
    scan_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found or does not belong to your account."
        )

    prediction_detail = None
    guidance = None
    model_ver = "unknown"

    if scan.prediction:
        pred = scan.prediction
        model_ver = pred.model_version
        conf = pred.confidence
        band = "low" if conf < 0.70 else ("moderate" if conf <= 0.85 else "high")

        # Re-construct Top3 list
        top3_items = []
        if isinstance(pred.top3, list):
            for item in pred.top3:
                top3_items.append(schemas.Top3Item(
                    label=item.get("label", ""),
                    display_name=item.get("display_name", item.get("label", "")),
                    score=float(item.get("score", 0.0))
                ))

        prediction_detail = schemas.PredictionDetail(
            label=pred.class_label,
            display_name=DISPLAY_NAMES.get(pred.class_label, pred.class_label),
            confidence=pred.confidence,
            confidence_band=band,
            severity=pred.severity,
            top3=top3_items
        )

        guidance = get_disease_guidance(pred.class_label, current_user.language or "en")

    # Retrieve medicines and nearby shops
    target_label = scan.prediction.class_label if scan.prediction else "healthy"
    user_lang = current_user.language or "en"
    medicines = [schemas.MedicineItem(**m) for m in get_recommended_medicines(target_label, user_lang)]
    nearest_shops = [schemas.AgroShopItem(**s) for s in find_nearest_shops(limit=3)]

    return schemas.ScanDetailResponse(
        scan_id=scan.id,
        image_url=make_media_url(scan.image_path),
        created_at=scan.created_at,
        prediction=prediction_detail,
        guidance=guidance,
        medicines=medicines,
        nearest_medical_shops=nearest_shops,
        model_version=model_ver
    )


@router.delete(
    "/api/v1/scans/{scan_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a scan record and its image",
    description="Deletes the scan from database and permanently removes the image file from storage."
)
def delete_scan(
    scan_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found or does not belong to your account."
        )

    # Safely remove image file from disk if it exists
    file_path = scan.image_path
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted physical image file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove physical file {file_path}: {e}")

    # Delete scan (cascade deletes prediction and feedback)
    db.delete(scan)
    db.commit()

    return {"detail": f"Scan #{scan_id} and associated image have been deleted successfully."}


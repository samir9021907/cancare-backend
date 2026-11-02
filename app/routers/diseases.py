"""
Disease Library Router (/api/v1/diseases).

Public endpoints to explore sugarcane disease descriptions, symptoms,
causes, and agronomist-vetted cultural practices in English, Marathi, and Hindi.
"""

import json
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app import schemas

router = APIRouter(prefix="/api/v1/diseases", tags=["Disease Library"])

# Path to the multilingual disease information dictionary
DISEASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "services", "disease_data.json")


def load_disease_data() -> dict:
    """Load disease content JSON from disk."""
    with open(DISEASE_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "",
    response_model=List[schemas.DiseaseListItem],
    summary="List all sugarcane diseases",
    description="Retrieves a list of all identifiable sugarcane diseases in the specified language (en, mr, hi)."
)
def list_diseases(lang: Optional[str] = Query("en", pattern="^(en|mr|hi)$")):
    data = load_disease_data()
    diseases = data.get("diseases", {})
    selected_lang = lang if lang in ["en", "mr", "hi"] else "en"

    result = []
    for code, translations in diseases.items():
        info = translations.get(selected_lang, translations.get("en", {}))
        result.append(
            schemas.DiseaseListItem(
                code=code,
                name=info.get("name", code),
                short_description=info.get("short_description", "")
            )
        )
    return result


@router.get(
    "/{code}",
    response_model=schemas.DiseaseDetailResponse,
    summary="Get full details of a specific disease",
    description="Returns detailed symptoms, causes, cultural treatment, and prevention practices in the selected language."
)
def get_disease(code: str, lang: Optional[str] = Query("en", pattern="^(en|mr|hi)$")):
    data = load_disease_data()
    diseases = data.get("diseases", {})
    
    disease_code = code.lower().strip()
    if disease_code not in diseases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease with code '{code}' not found. Supported codes: {list(diseases.keys())}"
        )

    selected_lang = lang if lang in ["en", "mr", "hi"] else "en"
    translations = diseases[disease_code]
    info = translations.get(selected_lang, translations.get("en", {}))

    return schemas.DiseaseDetailResponse(
        code=disease_code,
        name=info.get("name", disease_code),
        symptoms=info.get("symptoms", []),
        causes=info.get("causes", []),
        treatment=info.get("treatment", []),
        prevention=info.get("prevention", []),
        disclaimer=info.get("disclaimer", data.get("notice", ""))
    )


"""
Pydantic Schemas Module.

Defines data validation shapes for incoming API requests and outgoing responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re


# ---------------------------------------------------------------------------
# User Authentication & Profile Schemas
# ---------------------------------------------------------------------------
class UserSignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Ramesh Patil"])
    email: EmailStr = Field(..., examples=["ramesh.patil@example.com"])
    password: str = Field(..., min_length=8, max_length=64, examples=["Kisan@123"])
    phone: Optional[str] = Field(None, max_length=20, examples=["+91 9876543210"])
    language: Optional[str] = Field("en", pattern="^(en|mr|hi)$", examples=["mr"])

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Ensure password has at least 8 characters, at least one letter, and at least one number."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number.")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["ramesh.patil@example.com"])
    password: str = Field(..., examples=["Kisan@123"])


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    language: str
    role: str
    
    # Farmer Profile Details
    region: Optional[str] = None
    village: Optional[str] = None
    avatar_path: Optional[str] = None
    farm_size: Optional[str] = None
    sugarcane_variety: Optional[str] = None
    irrigation_type: Optional[str] = None
    planting_season: Optional[str] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Lifetime in seconds
    user: UserResponse


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    language: Optional[str] = Field(None, pattern="^(en|mr|hi)$")
    
    # Farmer Profile Details
    region: Optional[str] = None
    village: Optional[str] = None
    avatar_path: Optional[str] = None
    farm_size: Optional[str] = None
    sugarcane_variety: Optional[str] = None
    irrigation_type: Optional[str] = None
    planting_season: Optional[str] = None


# ---------------------------------------------------------------------------
# Prediction & ML Schemas
# ---------------------------------------------------------------------------
class Top3Item(BaseModel):
    label: str
    display_name: str
    score: float


class DiseaseGuidance(BaseModel):
    symptoms: List[str]
    causes: List[str]
    treatment: List[str]
    prevention: List[str]
    disclaimer: str


class PredictionDetail(BaseModel):
    label: str
    display_name: str
    confidence: float
    confidence_band: str  # "low", "moderate", "high"
    severity: str         # "none", "low", "medium", "high"
    top3: List[Top3Item]


class MedicineItem(BaseModel):
    name: str
    type: str
    dosage: str
    usage_note: str
    safety: str


class AgroShopItem(BaseModel):
    id: str
    name: str
    type: str
    address: str
    district: str
    state: str
    pincode: str
    contact_phone: str
    opening_hours: str
    distance_km: Optional[float] = None
    google_maps_directions_url: Optional[str] = None
    stocks: List[str]


class FarmerLocationInfo(BaseModel):
    source: str  # "GPS" or "IP_auto_detected"
    latitude: float
    longitude: float
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    google_maps_nearby_url: str


class PredictResponse(BaseModel):
    scan_id: str
    status: str           # "success" or "low_confidence"
    message: Optional[str] = None
    prediction: Optional[PredictionDetail] = None
    guidance: Optional[DiseaseGuidance] = None
    medicines: Optional[List[MedicineItem]] = None
    farmer_location: Optional[FarmerLocationInfo] = None
    nearest_medical_shops: Optional[List[AgroShopItem]] = None
    model_version: str
    disclaimer: bool = True


# ---------------------------------------------------------------------------
# Disease Information Schemas
# ---------------------------------------------------------------------------
class DiseaseListItem(BaseModel):
    code: str
    name: str
    short_description: str


class DiseaseDetailResponse(BaseModel):
    code: str
    name: str
    symptoms: List[str]
    causes: List[str]
    treatment: List[str]
    prevention: List[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# History Schemas
# ---------------------------------------------------------------------------
class HistoryItem(BaseModel):
    scan_id: str
    image_url: str
    disease: str
    display_name: str
    confidence: float
    confidence_band: str
    severity: str
    created_at: datetime


class HistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[HistoryItem]


class ScanDetailResponse(BaseModel):
    scan_id: str
    image_url: str
    created_at: datetime
    prediction: Optional[PredictionDetail] = None
    guidance: Optional[DiseaseGuidance] = None
    medicines: Optional[List[MedicineItem]] = None
    farmer_location: Optional[FarmerLocationInfo] = None
    nearest_medical_shops: Optional[List[AgroShopItem]] = None
    model_version: str


# ---------------------------------------------------------------------------
# Feedback Schemas (Scan Diagnosis + General App)
# ---------------------------------------------------------------------------
class FeedbackCreateRequest(BaseModel):
    scan_id: str
    is_correct: bool
    true_class: Optional[str] = Field(None, examples=["rust"])
    comment: Optional[str] = Field(None, examples=["The leaves have reddish brown spots."])


class FeedbackResponse(BaseModel):
    id: str
    scan_id: str
    is_correct: bool
    true_class: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppFeedbackRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    feedback_type: str = Field(..., max_length=100)
    message: str = Field(..., min_length=5, max_length=2000)


class AppFeedbackResponse(BaseModel):
    id: str
    name: str
    email: str
    feedback_type: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Advisory Questions Schemas
# ---------------------------------------------------------------------------
class AdvisoryQuestionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., max_length=100)


class AdvisoryQuestionResponse(BaseModel):
    id: str
    author_name: str
    title: str
    description: str
    category: str
    status: str
    expert_answer: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sugarcane Market & Mandi Rates Schemas
# ---------------------------------------------------------------------------
class DailyMarketRateItem(BaseModel):
    date: str
    date_label_mr: str
    date_label_en: str
    day_name_mr: str
    day_name_en: str
    avg_price: float
    min_price: float
    max_price: float
    change: float
    arrival_tonnes: int
    recovery_percent: float


class MonthlyMarketRateItem(BaseModel):
    month_label_mr: str
    month_label_en: str
    avg_price: float
    min_price: float
    max_price: float


class SugarcaneMandiItem(BaseModel):
    id: str
    name_mr: str
    name_en: str
    district_mr: str
    district_en: str
    base_recovery: float
    current_avg_price: float
    min_price: float
    max_price: float
    daily_change: float
    today_arrival_tonnes: int
    daily_rates: List[DailyMarketRateItem]
    monthly_rates: List[MonthlyMarketRateItem]
    active_factories: List[str]


class MarketRatesResponse(BaseModel):
    national_frp_base_rate: float
    base_recovery_rate: float
    premium_per_point_recovery: float
    updated_at: str
    mandis: List[SugarcaneMandiItem]


# ---------------------------------------------------------------------------
# Notifications Schemas
# ---------------------------------------------------------------------------
class NotificationItem(BaseModel):
    id: str
    title: str
    title_marathi: str
    title_hindi: str
    body: str
    body_marathi: str
    body_hindi: str
    category: str  # "tips", "weather", "reminder", "market", "alert"
    importance: str  # "normal", "high", "urgent"
    timestamp: str
    is_read: bool = False
    action_route: Optional[str] = None
    action_label: Optional[str] = None
    action_label_marathi: Optional[str] = None


class NotificationsResponse(BaseModel):
    total: int
    unread_count: int
    notifications: List[NotificationItem]


# ---------------------------------------------------------------------------
# Agri Product Schemas
# ---------------------------------------------------------------------------
class RecommendedProductItem(BaseModel):
    id: str
    disease_id: str
    name: str
    marathi_name: str
    category_tag: str
    marathi_category_tag: str
    pack_size: str
    verified_mrp: float
    purpose: str
    purpose_marathi: str
    image_asset: str
    active_ingredient: str
    cibrc_registration: str
    dosage_sugarcane: str
    dosage_sugarcane_marathi: str


class AgriProductListResponse(BaseModel):
    disease_id: str
    products: List[RecommendedProductItem]


# ---------------------------------------------------------------------------
# Health Check Schema
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    app_version: str
    model_mode: str  # "real" or "mock"

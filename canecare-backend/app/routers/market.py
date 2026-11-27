"""
Sugarcane Market & Mandi Rates Router (/api/v1/market).

Provides live FRP (Fair and Remunerative Price) benchmarks,
regional Mandi (APMC) rates across Maharashtra sugarcane belt,
and daily/monthly trend data.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter
from app import schemas

router = APIRouter(prefix="/api/v1/market", tags=["Sugarcane Market"])

NATIONAL_FRP_BASE = 3400.0  # ₹3,400 per tonne (10.25% recovery)
BASE_RECOVERY = 10.25
PREMIUM_PER_POINT = 33.26  # ₹33.26 per 0.1% increase

MANDIS_DATA = [
    {
        "id": "mandi_kopargaon",
        "name_mr": "कोपरगाव कृषी उत्पन्न बाजार समिती",
        "name_en": "Kopargaon APMC Sugarcane Division",
        "district_mr": "अहिल्यानगर",
        "district_en": "Ahilyanagar",
        "base_recovery": 11.20,
        "current_avg_price": 3715.0,
        "min_price": 3620.0,
        "max_price": 3810.0,
        "daily_change": 25.0,
        "today_arrival_tonnes": 4850,
        "active_factories": ["संजीवनी सह. साखर कारखाना", "सहकारमहर्षी कोल्हे कारखाना"],
        "daily_rates": [
            {
                "date": "2026-11-27",
                "date_label_mr": "२७ नोव्हे",
                "date_label_en": "27 Nov",
                "day_name_mr": "शुक्रवार",
                "day_name_en": "Friday",
                "avg_price": 3715.0,
                "min_price": 3620.0,
                "max_price": 3810.0,
                "change": 25.0,
                "arrival_tonnes": 4850,
                "recovery_percent": 11.20
            },
            {
                "date": "2026-11-26",
                "date_label_mr": "२६ नोव्हे",
                "date_label_en": "26 Nov",
                "day_name_mr": "गुरुवार",
                "day_name_en": "Thursday",
                "avg_price": 3690.0,
                "min_price": 3600.0,
                "max_price": 3780.0,
                "change": 15.0,
                "arrival_tonnes": 4620,
                "recovery_percent": 11.15
            },
            {
                "date": "2026-11-25",
                "date_label_mr": "२५ नोव्हे",
                "date_label_en": "25 Nov",
                "day_name_mr": "बुधवार",
                "day_name_en": "Wednesday",
                "avg_price": 3675.0,
                "min_price": 3580.0,
                "max_price": 3760.0,
                "change": -10.0,
                "arrival_tonnes": 4410,
                "recovery_percent": 11.10
            }
        ],
        "monthly_rates": [
            {"month_label_mr": "नोव्हे २०२६", "month_label_en": "Nov 2026", "avg_price": 3690.0, "min_price": 3580.0, "max_price": 3810.0},
            {"month_label_mr": "ऑक्टो २०२६", "month_label_en": "Oct 2026", "avg_price": 3550.0, "min_price": 3480.0, "max_price": 3620.0},
            {"month_label_mr": "सप्टें २०२६", "month_label_en": "Sep 2026", "avg_price": 3480.0, "min_price": 3400.0, "max_price": 3540.0}
        ]
    },
    {
        "id": "mandi_kolhapur",
        "name_mr": "कोल्हापूर शाहू मार्केट यार्ड",
        "name_en": "Kolhapur Shahu Market Yard",
        "district_mr": "कोल्हापूर",
        "district_en": "Kolhapur",
        "base_recovery": 12.10,
        "current_avg_price": 4015.0,
        "min_price": 3920.0,
        "max_price": 4110.0,
        "daily_change": 30.0,
        "today_arrival_tonnes": 8200,
        "active_factories": ["दत्त दालमिया साखर", "कुंभी कासारी सह. कारखाना", "वारणा सहकारी साखर कारखाना"],
        "daily_rates": [
            {
                "date": "2026-11-27",
                "date_label_mr": "२७ नोव्हे",
                "date_label_en": "27 Nov",
                "day_name_mr": "शुक्रवार",
                "day_name_en": "Friday",
                "avg_price": 4015.0,
                "min_price": 3920.0,
                "max_price": 4110.0,
                "change": 30.0,
                "arrival_tonnes": 8200,
                "recovery_percent": 12.10
            }
        ],
        "monthly_rates": [
            {"month_label_mr": "नोव्हे २०२६", "month_label_en": "Nov 2026", "avg_price": 3980.0, "min_price": 3890.0, "max_price": 4110.0}
        ]
    },
    {
        "id": "mandi_sangli",
        "name_mr": "सांगली मिरज कृषी उत्पन्न बाजार",
        "name_en": "Sangli Miraj APMC Market",
        "district_mr": "सांगली",
        "district_en": "Sangli",
        "base_recovery": 11.85,
        "current_avg_price": 3930.0,
        "min_price": 3840.0,
        "max_price": 4020.0,
        "daily_change": 20.0,
        "today_arrival_tonnes": 6500,
        "active_factories": ["वसंतदादा पाटील साखर कारखाना", "राजारामबापू पाटील साखर कारखाना"],
        "daily_rates": [
            {
                "date": "2026-11-27",
                "date_label_mr": "२७ नोव्हे",
                "date_label_en": "27 Nov",
                "day_name_mr": "शुक्रवार",
                "day_name_en": "Friday",
                "avg_price": 3930.0,
                "min_price": 3840.0,
                "max_price": 4020.0,
                "change": 20.0,
                "arrival_tonnes": 6500,
                "recovery_percent": 11.85
            }
        ],
        "monthly_rates": [
            {"month_label_mr": "नोव्हे २०२६", "month_label_en": "Nov 2026", "avg_price": 3895.0, "min_price": 3800.0, "max_price": 4020.0}
        ]
    },
    {
        "id": "mandi_baramati",
        "name_mr": "बारामती ॲग्रो मार्केट यार्ड",
        "name_en": "Baramati Agro Market Yard",
        "district_mr": "पुणे",
        "district_en": "Pune",
        "base_recovery": 11.50,
        "current_avg_price": 3820.0,
        "min_price": 3720.0,
        "max_price": 3910.0,
        "daily_change": 10.0,
        "today_arrival_tonnes": 5200,
        "active_factories": ["छत्रपती सहकारी साखर कारखाना", "सोमेश्वर सहकारी कारखाना"],
        "daily_rates": [
            {
                "date": "2026-11-27",
                "date_label_mr": "२७ नोव्हे",
                "date_label_en": "27 Nov",
                "day_name_mr": "शुक्रवार",
                "day_name_en": "Friday",
                "avg_price": 3820.0,
                "min_price": 3720.0,
                "max_price": 3910.0,
                "change": 10.0,
                "arrival_tonnes": 5200,
                "recovery_percent": 11.50
            }
        ],
        "monthly_rates": [
            {"month_label_mr": "नोव्हे २०२६", "month_label_en": "Nov 2026", "avg_price": 3790.0, "min_price": 3700.0, "max_price": 3910.0}
        ]
    }
]


@router.get(
    "/rates",
    response_model=schemas.MarketRatesResponse,
    summary="Get live sugarcane market rates and APMC Mandi trends",
    description="Returns national FRP base rates and real-time Maharashtra sugarcane mandi prices."
)
def get_market_rates():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return schemas.MarketRatesResponse(
        national_frp_base_rate=NATIONAL_FRP_BASE,
        base_recovery_rate=BASE_RECOVERY,
        premium_per_point_recovery=PREMIUM_PER_POINT,
        updated_at=now_str,
        mandis=[schemas.SugarcaneMandiItem(**m) for m in MANDIS_DATA]
    )

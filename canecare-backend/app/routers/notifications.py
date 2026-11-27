"""
Notifications Router (/api/v1/notifications).

Provides real-time notifications for:
- Crop diagnostic report readiness
- Weather spraying advisories
- Plot treatment progress reminders
- Market price alert updates
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from app import schemas, security, models

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=schemas.NotificationsResponse,
    summary="Get user notifications & agricultural alerts",
    description="Returns crop reports, weather spray advisories, and sugarcane market notifications."
)
def get_notifications(current_user: Optional[models.User] = Depends(security.get_optional_user)):
    now = datetime.now(timezone.utc)
    farmer_name = current_user.full_name if current_user else "शेतकरी मित्र"

    items = [
        schemas.NotificationItem(
            id="notif_report_ready_1",
            title=f"Crop Health Report Ready for {farmer_name}",
            title_marathi=f"ऊस पीक आरोग्य अहवाल तयार आहे ({farmer_name})",
            title_hindi=f"फसल स्वास्थ्य रिपोर्ट तैयार है ({farmer_name})",
            body="Your 1-page Sugarcane Diagnostic & Prescription Report is saved and ready to download.",
            body_marathi="तुमच्या शेताचा १ पानाचा अचूक निदान व फवारणी अहवाल तयार आहे. येथून डाउनलोड करा.",
            body_hindi="आपकी फसल की १ पेज की निदान और छिड़काव रिपोर्ट तैयार है। यहां से डाउनलोड करें।",
            category="tips",
            importance="normal",
            timestamp=(now - timedelta(minutes=25)).isoformat(),
            is_read=False,
            action_route="report",
            action_label="View Report",
            action_label_marathi="अहवाल पाहा"
        ),
        schemas.NotificationItem(
            id="notif_weather_update_2",
            title="Today's Weather: Ideal for Spraying",
            title_marathi="आजचे हवामान: फवारणीसाठी उत्तम दिवस",
            title_hindi="आज का मौसम: छिड़काव के लिए अनुकूल",
            body="Temperature is 28°C with gentle breeze. Clear skies favorable for foliar spray before 11 AM.",
            body_marathi="तापमान २८° से. असून निरभ्र आकाश आहे. सकाळी ११ पूर्वी फवारणी करणे अत्यंत फायदेशीर ठरेल.",
            body_hindi="तापमान २८° से. और मौसम साफ है। सुबह ११ बजे से पहले छिड़काव करना उपयुक्त रहेगा।",
            category="weather",
            importance="normal",
            timestamp=(now - timedelta(hours=2)).isoformat(),
            is_read=False,
            action_route="weather",
            action_label="Check Weather",
            action_label_marathi="हवामान पाहा"
        ),
        schemas.NotificationItem(
            id="notif_scan_reminder_3",
            title="Plot #1: Treatment Progress Check",
            title_marathi="प्लॉट क्र. १: फेरतपासणीची वेळ झाली आहे",
            title_hindi="प्लॉट नं. १: पुनः जांच का समय",
            body="7 days have passed since the last spray. Scan a leaf today to verify crop recovery.",
            body_marathi="मागील फवारणीला ७ दिवस पूर्ण झाले आहेत. आज नवीन फोटो स्कॅन करून पिकाची सुधारणा तपासा.",
            body_hindi="पिछली दवा छिड़काव के ७ दिन पूरे हो गए। फसल सुधार जांचने के लिए आज पत्ती स्कैन करें।",
            category="reminder",
            importance="normal",
            timestamp=(now - timedelta(hours=5)).isoformat(),
            is_read=False,
            action_route="scan",
            action_label="Scan Leaf",
            action_label_marathi="पान स्कॅन करा"
        ),
        schemas.NotificationItem(
            id="notif_market_rate_4",
            title="Sugarcane FRP Benchmark ₹3,400/Tonne Active",
            title_marathi="उसाचा एफआरपी दर ₹३,४००/टन जाहीर",
            title_hindi="गन्ने का एफआरपी भाव ₹३,४००/टन सक्रिय",
            body="Western Maharashtra sugar factories have commenced crushing season with high recovery bonuses.",
            body_marathi="पश्चिम महाराष्ट्रातील साखर कारखान्यांचा गळीत हंगाम सुरू झाला असून रिकव्हरी बोनस उपलब्ध आहे.",
            body_hindi="पश्चिम महाराष्ट्र की चीनी मिलों ने उच्च रिकवरी बोनस के साथ पेराई सत्र शुरू किया है।",
            category="market",
            importance="normal",
            timestamp=(now - timedelta(hours=8)).isoformat(),
            is_read=True,
            action_route="market",
            action_label="Check Rates",
            action_label_marathi="बाजारभाव पाहा"
        )
    ]

    unread = len([i for i in items if not i.is_read])
    return schemas.NotificationsResponse(
        total=len(items),
        unread_count=unread,
        notifications=items
    )

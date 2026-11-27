"""
Agro-Medical Stores & Krishi Seva Kendra Router (/api/v1/shops).

Public and farmer-accessible endpoint to:
1. Search nearest authorized agricultural medicine dealers, bio-control dispensaries, and Krishi Vigyan Kendra depots.
2. Get certified agro-medical products, bio-fungicides & chemical remedies for sugarcane diseases.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Request
from app import schemas
from app.services.shop_service import find_nearest_shops, resolve_farmer_location

router = APIRouter(prefix="/api/v1/shops", tags=["Agro-Medical Stores"])

RECOMMENDED_PRODUCTS_CATALOG = {
    "red_rot": [
        {
            "id": "prod_carbendazim_mancozeb",
            "disease_id": "red_rot",
            "name": "Carbendazim 12% + Mancozeb 63% WP",
            "marathi_name": "कार्बेन्डाझिम १२% + मॅन्कोझेब ६३% (SAAF)",
            "category_tag": "BROAD SPECTRUM SYSTEMIC FUNGICIDE",
            "marathi_category_tag": "व्यापक आंतरप्रवाही व स्पर्शजन्य बुरशीनाशक",
            "pack_size": "500 gm Pack",
            "verified_mrp": 420.0,
            "purpose": "Controls fungal infection in root zone and internal vascular cane bundles.",
            "purpose_marathi": "मुळाजवळील बुरशीचा संसर्ग रोखण्यासाठी व ऊसाच्या अंतर्गत भागाचे रक्षण करण्यासाठी.",
            "image_asset": "assets/images/product_fungicide_saaf.jpg",
            "active_ingredient": "Carbendazim 12% + Mancozeb 63% WP",
            "cibrc_registration": "CIR-112,842/2018-Carbendazim+Mancozeb(WP)-124",
            "dosage_sugarcane": "2.0 gm per liter of water (400 gm per acre in 200L water).",
            "dosage_sugarcane_marathi": "२.० ग्रॅम प्रति लिटर पाणी (४०० ग्रॅम प्रति एकर २०० लिटर पाण्यात)."
        },
        {
            "id": "prod_trichoderma_harzianum",
            "disease_id": "red_rot",
            "name": "Trichoderma harzianum Bio-Fungicide",
            "marathi_name": "ट्रायकोडर्मा हार्झियानम (जैविक बुरशीनाशक)",
            "category_tag": "BIO-CONTROL AGENT",
            "marathi_category_tag": "सेंद्रिय जैविक बुरशीनाशक",
            "pack_size": "1 kg Pack",
            "verified_mrp": 210.0,
            "purpose": "Bio-antagonist that destroys pathogenic mycelium in soil.",
            "purpose_marathi": "मातीतील घातक बुरशी नष्ट करून पिकाची प्रतिकारशक्ती वाढवणे.",
            "image_asset": "assets/images/product_trichoderma.jpg",
            "active_ingredient": "Trichoderma harzianum 2x10^6 CFU/g",
            "cibrc_registration": "CIR-143,291/2021-Trichoderma(WP)-89",
            "dosage_sugarcane": "2.5 to 3.0 kg per acre mixed with 200 kg FYM.",
            "dosage_sugarcane_marathi": "२.५ ते ३ किलो प्रति एकर २०० किलो चांगल्या कुजलेल्या शेणखतात मिसळून देणे."
        }
    ],
    "rust": [
        {
            "id": "prod_mancozeb_75",
            "disease_id": "rust",
            "name": "Mancozeb 75% WP (Dithane M-45)",
            "marathi_name": "मॅन्कोझेब ७५% डब्ल्यूपी (डायथेन एम-४५)",
            "category_tag": "CONTACT FUNGICIDE",
            "marathi_category_tag": "स्पर्शजन्य बुरशीनाशक",
            "pack_size": "1 kg Pack",
            "verified_mrp": 380.0,
            "purpose": "Forms a protective shield on leaf surface preventing rust spore germination.",
            "purpose_marathi": "पानांच्या पृष्ठभागावर संरक्षक थर तयार करून तांबेऱ्याचे बीजाणू रोखणे.",
            "image_asset": "assets/images/product_mancozeb.jpg",
            "active_ingredient": "Mancozeb 75% WP",
            "cibrc_registration": "CIR-45,612/2015-Mancozeb(WP)-34",
            "dosage_sugarcane": "2.5 gm per liter of water (500 gm per acre).",
            "dosage_sugarcane_marathi": "२.५ ग्रॅम प्रति लिटर पाणी (५०० ग्रॅम प्रति एकर २०० लिटर पाण्यात)."
        },
        {
            "id": "prod_propiconazole_25",
            "disease_id": "rust",
            "name": "Propiconazole 25% EC (Tilt)",
            "marathi_name": "प्रोपिकोनाझोल २५% ईसी (टिल्ट)",
            "category_tag": "SYSTEMIC TRIAZOLE FUNGICIDE",
            "marathi_category_tag": "आंतरप्रवाही बुरशीनाशक",
            "pack_size": "250 ml Pack",
            "verified_mrp": 485.0,
            "purpose": "Deep systemic translaminar action stopping rapid rust spread within 48 hours.",
            "purpose_marathi": "४८ तासांत पानांच्या पेशींमध्ये जाऊन तांबेऱ्याचा फैलाव पूर्णपणे थांबवणे.",
            "image_asset": "assets/images/product_propiconazole.jpg",
            "active_ingredient": "Propiconazole 25% EC",
            "cibrc_registration": "CIR-67,890/2017-Propiconazole(EC)-56",
            "dosage_sugarcane": "1.0 ml per liter of water (200 ml per acre).",
            "dosage_sugarcane_marathi": "१.० मिली प्रति लिटर पाणी (२०० मिली प्रति एकर २०० लिटर पाण्यात फवारणी)."
        }
    ],
    "yellow_leaf": [
        {
            "id": "prod_imidacloprid_178",
            "disease_id": "yellow_leaf",
            "name": "Imidacloprid 17.8% SL (Confidor)",
            "marathi_name": "इमिडाक्लोप्रिड १७.८% एसएल (कॉन्फिडॉर)",
            "category_tag": "SYSTEMIC INSECTICIDE (APHID CONTROL)",
            "marathi_category_tag": "मावा व रसशोषक कीड नियंत्रक",
            "pack_size": "250 ml Pack",
            "verified_mrp": 395.0,
            "purpose": "Controls sugarcane aphids which are primary vectors transmitting Yellow Leaf Virus.",
            "purpose_marathi": "पिवळा पान रोग पसरवणाऱ्या मावा व रसशोषक किडींचे संपूर्ण नियंत्रण.",
            "image_asset": "assets/images/product_imidacloprid.jpg",
            "active_ingredient": "Imidacloprid 17.8% SL",
            "cibrc_registration": "CIR-55,234/2016-Imidacloprid(SL)-78",
            "dosage_sugarcane": "0.5 ml per liter of water (100 ml per acre).",
            "dosage_sugarcane_marathi": "०.५ मिली प्रति लिटर पाणी (१०० मिली प्रति एकर फवारणी)."
        },
        {
            "id": "prod_micronutrient_grade2",
            "disease_id": "yellow_leaf",
            "name": "Maharashtra Grade II Micronutrient Foliar Spray",
            "marathi_name": "महाराष्ट्र ग्रेड-२ सुक्ष्म अन्नद्रव्ये",
            "category_tag": "CROP NUTRITION BOOST",
            "marathi_category_tag": "सूक्ष्म अन्नद्रव्य टॉनिक",
            "pack_size": "1 Liter",
            "verified_mrp": 290.0,
            "purpose": "Restores chlorophyll synthesis in chlorotic leaves providing Iron, Zinc & Magnesium.",
            "purpose_marathi": "पानांमधील हरितद्रव्य वाढवून पिवळेपणा दूर करण्यासाठी जस्त, लोह व मॅग्नेशियम देणे.",
            "image_asset": "assets/images/product_micronutrients.jpg",
            "active_ingredient": "Fe 2.5%, Zn 3.0%, Mn 1.0%, Cu 0.5%, B 0.5%",
            "cibrc_registration": "MAH-FCO/MN-Grade-II/2019",
            "dosage_sugarcane": "2.5 ml per liter of water.",
            "dosage_sugarcane_marathi": "२.५ मिली प्रति लिटर पाण्यात मिसळून फवारणी करणे."
        }
    ],
    "mosaic": [
        {
            "id": "prod_thiamethoxam_25",
            "disease_id": "mosaic",
            "name": "Thiamethoxam 25% WG (Actara)",
            "marathi_name": "थायमेथोक्साम २५% डब्ल्यूजी (अक्टारा)",
            "category_tag": "VECTOR CONTROL INSECTICIDE",
            "marathi_category_tag": "व्हायरस वाहक कीटकनाशक",
            "pack_size": "100 gm Pack",
            "verified_mrp": 320.0,
            "purpose": "Eliminates aphids and planthoppers responsible for mosaic virus transmission.",
            "purpose_marathi": "मोझॅक विषाणू पसरवणाऱ्या मावा व तुडतुड्यांचा समूळ नायनाट करणे.",
            "image_asset": "assets/images/product_thiamethoxam.jpg",
            "active_ingredient": "Thiamethoxam 25% WG",
            "cibrc_registration": "CIR-98,712/2019-Thiamethoxam(WG)-45",
            "dosage_sugarcane": "0.5 gm per liter of water (100 gm per acre).",
            "dosage_sugarcane_marathi": "०.५ ग्रॅम प्रति लिटर पाणी (१०० ग्रॅम प्रति एकर २०० लिटर पाण्यात फवारणी)."
        }
    ],
    "healthy": [
        {
            "id": "prod_trichoderma_healthy",
            "disease_id": "healthy",
            "name": "Trichoderma viride Bio-Fungicide",
            "marathi_name": "ट्रायकोडर्मा व्हिरीडे (जैविक बुरशीनाशक)",
            "category_tag": "PREVENTIVE BIO-CONTROL",
            "marathi_category_tag": "प्रतिबंधात्मक जैविक बुरशीनाशक",
            "pack_size": "1 kg Pack",
            "verified_mrp": 185.0,
            "purpose": "Soil drenching & root zone protection to keep crop vigorous and prevent infections.",
            "purpose_marathi": "मुळाजवळ जैविक बुरशीनाशकाची आळवणी करून निरोगी वाढ टिकवून ठेवणे.",
            "image_asset": "assets/images/product_trichoderma.jpg",
            "active_ingredient": "Trichoderma viride 1.0% WP",
            "cibrc_registration": "CIR-143,291/2021-Trichoderma(WP)-89",
            "dosage_sugarcane": "2.5 to 3.0 kg per acre mixed with 200 kg FYM.",
            "dosage_sugarcane_marathi": "२.५ ते ३ किलो प्रति एकर २०० किलो चांगल्या कुजलेल्या शेणखतात मिसळून द्यावे."
        }
    ]
}


@router.get(
    "",
    response_model=List[schemas.AgroShopItem],
    summary="Find nearest agro-medical stores & Krishi Seva Kendras",
    description="Returns authorized agricultural medicine shops sorted by proximity to the farmer's live location."
)
def get_nearest_agro_shops(
    request: Request,
    latitude: Optional[float] = Query(None, description="Farmer GPS latitude (auto-detected if omitted)"),
    longitude: Optional[float] = Query(None, description="Farmer GPS longitude"),
    district: Optional[str] = Query(None, description="District name (e.g. Kopargaon, Sangli, Kolhapur)"),
    pincode: Optional[str] = Query(None, description="Postal pincode"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of stores to return")
):
    client_ip = request.client.host if request.client else None
    loc = resolve_farmer_location(user_lat=latitude, user_lon=longitude, client_ip=client_ip)

    shops = find_nearest_shops(
        user_lat=loc["latitude"],
        user_lon=loc["longitude"],
        pincode=pincode or loc.get("pincode"),
        district=district or loc.get("district"),
        limit=limit
    )
    return [schemas.AgroShopItem(**s) for s in shops]


@router.get(
    "/products",
    response_model=schemas.AgriProductListResponse,
    summary="Get recommended medicines & fertilizers for disease",
    description="Returns verified agricultural remedies, active ingredients, dosage, and CIBRC registration."
)
def get_products_for_disease(
    disease: str = Query(..., description="Disease code (healthy, red_rot, rust, yellow_leaf, mosaic)")
):
    target = disease.lower().strip()
    products = RECOMMENDED_PRODUCTS_CATALOG.get(target, RECOMMENDED_PRODUCTS_CATALOG["healthy"])
    return schemas.AgriProductListResponse(
        disease_id=target,
        products=[schemas.RecommendedProductItem(**p) for p in products]
    )

"""
Agro-Medical Shop & Medication Service.

Provides:
1. Recommended medicines (chemical & bio-control options) for sugarcane diseases.
2. Nearest Krishi Seva Kendra / Agro-Medical stores calculation using Haversine distance.
"""

import json
import logging
import math
import os
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("canecare.shops")

SHOPS_DATA_PATH = os.path.join(os.path.dirname(__file__), "agro_shops_data.json")

# Default fallback coordinates (Kopargaon / Western Maharashtra Sugarcane Belt)
DEFAULT_LATITUDE = 19.8766
DEFAULT_LONGITUDE = 74.4801
DEFAULT_CITY = "Kopargaon"
DEFAULT_DISTRICT = "Ahilyanagar"
DEFAULT_STATE = "Maharashtra"
DEFAULT_PINCODE = "423601"


def resolve_farmer_location(
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    client_ip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dynamically resolve the farmer's live geographic location:
    1. If GPS coordinates are passed from device, use them directly (source='GPS').
    2. If no GPS coordinates, auto-detect live coordinates from the real client IP (source='IP_auto_detected').
    3. Generate a direct Google Maps search link to find all live shops around the farmer.
    """
    # Case 1: Device GPS coordinates provided
    if user_lat is not None and user_lon is not None:
        lat = round(float(user_lat), 4)
        lon = round(float(user_lon), 4)
        source = "GPS"
        city = None
        district = None
        state = None
        pincode = None

        # Attempt quick reverse geocoding via OpenStreetMap Nominatim
        try:
            geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            res = httpx.get(geo_url, headers={"User-Agent": "CaneCareAI/1.0"}, timeout=3.0)
            if res.status_code == 200:
                address = res.json().get("address", {})
                city = address.get("town") or address.get("city") or address.get("village")
                district = address.get("county") or address.get("state_district")
                state = address.get("state")
                pincode = address.get("postcode")
        except Exception as e:
            logger.debug(f"Reverse geocode lookup skipped: {e}")

        maps_url = f"https://www.google.com/maps/search/Krishi+Seva+Kendra+fertilizers+pesticides/@{lat},{lon},13z"
        return {
            "source": source,
            "latitude": lat,
            "longitude": lon,
            "city": city or "Nearby Region",
            "district": district or "Sugarcane Belt",
            "state": state or "India",
            "pincode": pincode,
            "google_maps_nearby_url": maps_url
        }

    # Case 2: Auto-detect location from IP address
    source = "IP_auto_detected"
    try:
        # Use ip-api to get live location
        ip_query_url = "http://ip-api.com/json/"
        # If client_ip is public and not private/loopback, pass it
        if client_ip and client_ip not in ["127.0.0.1", "localhost", "::1"] and not client_ip.startswith("192.168."):
            ip_query_url = f"http://ip-api.com/json/{client_ip}"

        res = httpx.get(ip_query_url, timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                lat = round(float(data["lat"]), 4)
                lon = round(float(data["lon"]), 4)
                maps_url = f"https://www.google.com/maps/search/Krishi+Seva+Kendra+fertilizers+pesticides/@{lat},{lon},13z"
                return {
                    "source": source,
                    "latitude": lat,
                    "longitude": lon,
                    "city": data.get("city", DEFAULT_CITY),
                    "district": data.get("regionName", DEFAULT_DISTRICT),
                    "state": data.get("regionName", DEFAULT_STATE),
                    "pincode": data.get("zip", DEFAULT_PINCODE),
                    "google_maps_nearby_url": maps_url
                }
    except Exception as e:
        logger.warning(f"Could not auto-detect location from IP: {e}")

    # Case 3: Fallback regional center
    maps_url = f"https://www.google.com/maps/search/Krishi+Seva+Kendra+fertilizers+pesticides/@{DEFAULT_LATITUDE},{DEFAULT_LONGITUDE},13z"
    return {
        "source": "Regional_Default",
        "latitude": DEFAULT_LATITUDE,
        "longitude": DEFAULT_LONGITUDE,
        "city": DEFAULT_CITY,
        "district": DEFAULT_DISTRICT,
        "state": DEFAULT_STATE,
        "pincode": DEFAULT_PINCODE,
        "google_maps_nearby_url": maps_url
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


def load_shops_data() -> List[Dict[str, Any]]:
    """Load agro-medical stores dataset from disk."""
    if not os.path.exists(SHOPS_DATA_PATH):
        return []
    with open(SHOPS_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_recommended_medicines(disease_code: str, lang: str = "en") -> List[Dict[str, Any]]:
    """
    Returns curated, agronomist-standard chemical and bio-control medicines
    for the identified sugarcane disease in the selected language (en, mr, hi).
    """
    code = disease_code.lower().strip()

    medicines_db = {
        "healthy": {
            "en": [
                {
                    "name": "Multi-Micronutrient Foliar Tonic",
                    "type": "Bio-stimulant / Micronutrients",
                    "dosage": "2 to 3 ml per liter of water",
                    "usage_note": "Spray evenly across foliage to maintain lush green vigor and cane growth.",
                    "safety": "Standard protective gear; spray during calm morning hours."
                }
            ],
            "mr": [
                {
                    "name": "सूक्ष्म अन्नद्रव्य टॉनिक (Multi-Micronutrient Spray)",
                    "type": "बायो-स्टिम्युलंट / पोषण टॉनिक",
                    "dosage": "२ ते ३ मिली प्रति लिटर पाणी",
                    "usage_note": "उसाची जोमदार वाढ आणि पानांचा हिरवेपणा टिकवण्यासाठी फवारणी करावी.",
                    "safety": "सकाळी किंवा संध्याकाळी शांत हवेत फवारणी करावी."
                }
            ],
            "hi": [
                {
                    "name": "सूक्ष्म पोषक तत्व टॉनिक (Micronutrient Liquid)",
                    "type": "पोषक तत्व / बायो-स्टिमुलेंट",
                    "dosage": "2 से 3 मिली प्रति लीटर पानी",
                    "usage_note": "फसल की अच्छी बढ़वार और हरियाली बनाए रखने के लिए पत्तियों पर छिड़कें।",
                    "safety": "सुबह या शाम के समय शांत वातावरण में छिड़काव करें।"
                }
            ]
        },
        "red_rot": {
            "en": [
                {
                    "name": "Carbendazim 50% WP (e.g., Bavistin)",
                    "type": "Systemic Fungicide",
                    "dosage": "1.0 to 1.5 g per liter of water",
                    "usage_note": "Apply as root drench around affected cane stools to halt fungal spread.",
                    "safety": "Wear rubber gloves and mask; keep away from water bodies."
                },
                {
                    "name": "Copper Oxychloride 50% WP (e.g., Blitox)",
                    "type": "Broad-Spectrum Contact Fungicide",
                    "dosage": "2.5 to 3.0 g per liter of water",
                    "usage_note": "Drench soil along furrows and spray base of standing stalks.",
                    "safety": "Do not mix with acidic chemicals or direct foliar fertilizers."
                },
                {
                    "name": "Trichoderma viride (Bio-Fungicide)",
                    "type": "Biological Control Agent",
                    "dosage": "2.5 kg mixed with 100 kg compost per acre",
                    "usage_note": "Broadcast around root zone with light irrigation to suppress soil-borne pathogens.",
                    "safety": "100% eco-friendly and non-toxic to humans."
                }
            ],
            "mr": [
                {
                    "name": "कार्बेन्डाझिम ५०% डब्ल्यूपी (Carbendazim 50% WP)",
                    "type": "अंतरप्रवाही बुरशीनाशक",
                    "dosage": "१.० ते १.५ ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "बुरशीचा फैलाव रोखण्यासाठी बाधित उसाच्या बुंध्याशी आळवणी (Drenching) करावी.",
                    "safety": "हातमोजे व मास्क वापरावा; लहान मुले व पाळीव प्राण्यांपासून दूर ठेवावे."
                },
                {
                    "name": "कॉपर ऑक्सिक्लोराईड ५०% डब्ल्यूपी (Copper Oxychloride)",
                    "type": "स्पर्शजन्य बुरशीनाशक",
                    "dosage": "२.५ ते ३.० ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "उसाच्या बुडख्याभोवती जमिनीवर फवारणी किंवा आळवणी करावी.",
                    "safety": "फवारणी करताना तोंडाला रुमाल किंवा मास्क लावावा."
                },
                {
                    "name": "ट्रायकोडर्मा व्हिरीडी (Trichoderma viride)",
                    "type": "जैविक बुरशीनाशक",
                    "dosage": "२.५ किलो प्रति एकर (१०० किलो शेणखतात मिसळून)",
                    "usage_note": "जमिनीतील घातक बुरशी नष्ट करण्यासाठी उसाच्या बुडख्याजवळ द्यावे.",
                    "safety": "पूर्णपणे सुरक्षित व पर्यावरणपूरक."
                }
            ],
            "hi": [
                {
                    "name": "कार्बेन्डाजिम 50% डब्ल्यूपी (Carbendazim 50% WP)",
                    "type": "सर्वांगी फफूंदनाशक",
                    "dosage": "1.0 से 1.5 ग्राम प्रति लीटर पानी",
                    "usage_note": "प्रभावित पौधों की जड़ों के पास मिट्टी में ड्रेंचिंग (सिंचाई) करें।",
                    "safety": "दवा का उपयोग करते समय दस्ताने और मास्क का प्रयोग करें।"
                },
                {
                    "name": "कॉपर ऑक्सीक्लोराइड 50% डब्ल्यूपी (Copper Oxychloride)",
                    "type": "स्पर्श फफूंदनाशक",
                    "dosage": "2.5 से 3.0 ग्राम प्रति लीटर पानी",
                    "usage_note": "गन्ने के तने के निचले हिस्से और मिट्टी पर छिड़काव करें।",
                    "safety": "छिड़काव के बाद हाथ-मुंह साबुन से अच्छी तरह धोएं।"
                },
                {
                    "name": "ट्राइकोडर्मा विरिडी (Trichoderma viride)",
                    "type": "जैविक फफूंदनाशक",
                    "dosage": "2.5 किलोग्राम प्रति एकड़ (गोबर की खाद के साथ)",
                    "usage_note": "मिट्टी में मौजूद हानिकारक फफूंद को समाप्त करने के लिए जड़ों में दें।",
                    "safety": "पूर्णतः जैविक, सुरक्षित और पर्यावरण अनुकूल।"
                }
            ]
        },
        "rust": {
            "en": [
                {
                    "name": "Propiconazole 25% EC (e.g., Tilt)",
                    "type": "Systemic Triazole Fungicide",
                    "dosage": "1.0 ml per liter of water",
                    "usage_note": "Foliar spray covering upper and lower surfaces of leaves when first pustules appear.",
                    "safety": "Do not spray during intense afternoon sun; observe 15-day pre-harvest interval."
                },
                {
                    "name": "Mancozeb 75% WP (e.g., Dithane M-45)",
                    "type": "Contact Protective Fungicide",
                    "dosage": "2.0 to 2.5 g per liter of water",
                    "usage_note": "Spray at 10-14 day intervals to prevent rust spore germination on healthy foliage.",
                    "safety": "Use face protection; avoid inhaling dust particles."
                },
                {
                    "name": "Wettable Sulfur 80% WDG",
                    "type": "Contact Fungicide & Acaricide",
                    "dosage": "3.0 g per liter of water",
                    "usage_note": "Suppresses fungal pustules and provides sulfur nutrition to cane leaves.",
                    "safety": "Avoid spraying if ambient temperature exceeds 35°C to prevent leaf scorch."
                }
            ],
            "mr": [
                {
                    "name": "प्रोपिकोनाझोल २५% ईसी (Propiconazole 25% EC)",
                    "type": "अंतरप्रवाही बुरशीनाशक",
                    "dosage": "१.० मिली प्रति लिटर पाणी",
                    "usage_note": "पानांवर तांबेऱ्याचे लाल ठिपके दिसताच संपूर्ण पानांवर फवारणी करावी.",
                    "safety": "कडक उन्हात फवारणी टाळावी; सुरक्षा किट वापरावी."
                },
                {
                    "name": "मॅन्कोझेब ७५% डब्ल्यूपी (Mancozeb 75% WP)",
                    "type": "स्पर्शजन्य प्रतिबंधक बुरशीनाशक",
                    "dosage": "२.० ते २.५ ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "रोग निरोगी पानांवर पसरू नये म्हणून १०-१२ दिवसांच्या अंतराने फवारणी करावी.",
                    "safety": "फवारणी करताना मास्कचा वापर करावा."
                },
                {
                    "name": "सल्फर ८०% डब्लूडीजी (Wettable Sulphur 80%)",
                    "type": "बुरशीनाशक व गंधक खत",
                    "dosage": "३.० ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "तांबेरा नियंत्रणासोबत पानांना गंधकाचे पोषण मिळते.",
                    "safety": "दुपारी जास्त तापमान असल्यास फवारणी करू नये."
                }
            ],
            "hi": [
                {
                    "name": "प्रोपिकोनाजोल 25% ईसी (Propiconazole 25% EC)",
                    "type": "सर्वांगी कवकनाशी",
                    "dosage": "1.0 मिली प्रति लीटर पानी",
                    "usage_note": "पत्तियों पर रस्ट के धब्बे दिखते ही पत्तियों के दोनों तरफ अच्छी तरह छिड़कें।",
                    "safety": "दोपहर की तेज धूप में छिड़काव न करें; सुरक्षा मास्क पहनें।"
                },
                {
                    "name": "मैंकोजेब 75% डब्ल्यूपी (Mancozeb 75% WP)",
                    "type": "सुरक्षात्मक स्पर्श कवकनाशी",
                    "dosage": "2.0 से 2.5 ग्राम प्रति लीटर पानी",
                    "usage_note": "स्वस्थ पत्तियों पर संक्रमण रोकने हेतु 10-12 दिनों के अंतराल पर छिड़कें।",
                    "safety": "दवा का घोल बनाते समय मास्क और चश्मा लगाएं।"
                },
                {
                    "name": "घुलनशील गंधक / सल्फर 80% डब्लूडीजी",
                    "type": "कवकनाशी एवं गंधक पोषक",
                    "dosage": "3.0 ग्राम प्रति लीटर पानी",
                    "usage_note": "गेरुई रोग को रोकने के साथ-साथ पौधों को आवश्यक गंधक प्रदान करता है।",
                    "safety": "35 डिग्री सेल्सियस से अधिक तापमान में छिड़काव न करें।"
                }
            ]
        },
        "yellow_leaf": {
            "en": [
                {
                    "name": "Imidacloprid 17.8% SL (e.g., Confidor)",
                    "type": "Systemic Insecticide (Vector Control)",
                    "dosage": "0.3 to 0.5 ml per liter of water",
                    "usage_note": "Target sugarcane aphid colonies under leaves that spread yellow leaf virus.",
                    "safety": "Highly toxic to bees; avoid spraying near flowering weed borders."
                },
                {
                    "name": "Neem Oil Extract (Azadirachtin 10,000 ppm)",
                    "type": "Botanical Bio-Insecticide",
                    "dosage": "2.0 to 3.0 ml per liter of water",
                    "usage_note": "Repels aphids and whiteflies naturally without harming beneficial insects.",
                    "safety": "Eco-friendly, safe for farmers and natural predators."
                },
                {
                    "name": "19:19:19 NPK + Zinc Chelate",
                    "type": "Foliar Nutritional Booster",
                    "dosage": "5.0 g NPK + 1.0 g Chelated Zinc per liter of water",
                    "usage_note": "Alleviates chlorophyll deficiency and restores nutritional vigor.",
                    "safety": "Mix in clean water; spray early in the morning."
                }
            ],
            "mr": [
                {
                    "name": "इमिडाक्लोप्रिड १७.८% एसएल (Imidacloprid 17.8% SL)",
                    "type": "अंतरप्रवाही कीटकनाशक (मावा कीड नियंत्रण)",
                    "dosage": "०.३ ते ०.५ मिली प्रति लिटर पाणी",
                    "usage_note": "पिवळा पान रोग पसरवणाऱ्या मावा (Aphid) किडीचा बंदोबस्त करण्यासाठी पानांच्या खाली फवारणी करावी.",
                    "safety": "मधमाश्यांसाठी घातक असल्याने शेताच्या बांधावरील फुलोऱ्यात फवारणी टाळावी."
                },
                {
                    "name": "कडुनिंब अर्क / नीम तेल (Neem Oil 10,000 ppm)",
                    "type": "जैविक कीटकनाशक",
                    "dosage": "२ ते ३ मिली प्रति लिटर पाणी",
                    "usage_note": "मावा व रसशोषक किडींना रोखण्यासाठी नैसर्गिक व प्रभावी उपाय.",
                    "safety": "मित्रकिडींसाठी सुरक्षित आणि पर्यावरणपूरक."
                },
                {
                    "name": "१९:१९:१९ विद्राव्य खत + चिलेटेड झिंक",
                    "type": "पानांवरील पोषण टॉनिक",
                    "dosage": "५ ग्रॅम खत + १ ग्रॅम झिंक प्रति लिटर पाणी",
                    "usage_note": "पानांमधील पिवळेपणा कमी करून क्लोरोफिल वाढवण्यासाठी फवारणी करावी.",
                    "safety": "स्वच्छ पाण्यात विरघळवून सकाळी फवारणी करावी."
                }
            ],
            "hi": [
                {
                    "name": "इमिडाक्लोप्रिड 17.8% एसएल (Imidacloprid 17.8% SL)",
                    "type": "कीटनाशक (माहू/एफिड वाहक नियंत्रण)",
                    "dosage": "0.3 से 0.5 मिली प्रति लीटर पानी",
                    "usage_note": "वायरस फैलाने वाले एफिड कीटों को नियंत्रित करने के लिए पत्तियों के नीचे स्प्रे करें।",
                    "safety": "मधुमक्खियों के लिए हानिकारक; सुरक्षा मास्क पहनें।"
                },
                {
                    "name": "नीम का तेल (Neem Oil 10,000 ppm)",
                    "type": "जैविक वनस्पति कीटनाशक",
                    "dosage": "2 से 3 मिली प्रति लीटर पानी",
                    "usage_note": "कीटों के फैलाव को प्राकृतिक रूप से रोकने हेतु प्रयोग करें।",
                    "safety": "पर्यावरण और मित्र कीटों के लिए पूरी तरह सुरक्षित।"
                },
                {
                    "name": "19:19:19 घुलनशील उर्वरक + जिंक",
                    "type": "पोषक तत्व स्प्रे",
                    "dosage": "5 ग्राम 19:19:19 + 1 ग्राम चिलेटेड जिंक प्रति लीटर पानी",
                    "usage_note": "पीलेपन को दूर कर पौधे में हरित लवक (क्लोरोफिल) बढ़ाने में मदद करता है।",
                    "safety": "साफ पानी में घोलकर सुबह के समय छिड़काव करें।"
                }
            ]
        },
        "mosaic": {
            "en": [
                {
                    "name": "Thiamethoxam 25% WG (e.g., Actara)",
                    "type": "Systemic Insecticide (Aphid Control)",
                    "dosage": "0.2 to 0.3 g per liter of water",
                    "usage_note": "Eliminates sap-sucking vectors carrying mosaic virus from weeds to sugarcane.",
                    "safety": "Wear goggles and gloves; do not spray against the wind."
                },
                {
                    "name": "Neem Seed Kernel Extract 5% (NSKE)",
                    "type": "Organic Repellent & Antifeedant",
                    "dosage": "50 g per liter of water",
                    "usage_note": "Deters insect feeding and egg laying on young sugarcane shoots.",
                    "safety": "Completely non-hazardous organic formulation."
                },
                {
                    "name": "Ferrous Sulfate 19% + Urea Spray",
                    "type": "Corrective Chlorosis Spray",
                    "dosage": "5.0 g Ferrous Sulfate + 10 g Urea per liter of water",
                    "usage_note": "Alleviates leaf chlorosis and mottled appearance in virus-affected leaves.",
                    "safety": "Dissolve properly; apply during early morning hours."
                }
            ],
            "mr": [
                {
                    "name": "थायमेथोक्सम २५% डब्ल्यूजी (Thiamethoxam 25% WG)",
                    "type": "अंतरप्रवाही कीटकनाशक",
                    "dosage": "०.२ ते ०.३ ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "मोझॅक विषाणू पसरवणाऱ्या मावा व तुडतुडे किडींचा तात्काळ नायनाट करण्यासाठी.",
                    "safety": "वाऱ्याच्या दिशेने फवारणी करावी; सुरक्षा किट वापरावी."
                },
                {
                    "name": "निंबोळी अर्क ५% (NSKE)",
                    "type": "सेंद्रिय कीड प्रतिबंधक",
                    "dosage": "५० ग्रॅम प्रति लिटर पाणी",
                    "usage_note": "किडींना उसावर अंडी घालण्यापासून व रस शोषण्यापासून रोखणारा सेंद्रिय उपाय.",
                    "safety": "पर्यावरणपूरक व बिनविषारी."
                },
                {
                    "name": "हिरकास (फेरस सल्फेट) + युरिया फवारणी",
                    "type": "लोह पोषण टॉनिक",
                    "dosage": "५ ग्रॅम फेरस सल्फेट + १० ग्रॅम युरिया प्रति लिटर पाणी",
                    "usage_note": "पानावरील पांढुरके पट्टे कमी करून पाने गर्द हिरवी करण्यासाठी फवारावे.",
                    "safety": "पाण्यात नीट विरघळवून गाळून फवारणी करावी."
                }
            ],
            "hi": [
                {
                    "name": "थायमेथोक्सम 25% डब्ल्यूजी (Thiamethoxam 25% WG)",
                    "type": "सर्वांगी कीटनाशक",
                    "dosage": "0.2 से 0.3 ग्राम प्रति लीटर पानी",
                    "usage_note": "मोज़ेक वायरस फैलाने वाले रसचूसक कीटों (माहू/एफिड) के सफाए हेतु छिड़कें।",
                    "safety": "हवा के विपरीत दिशा में छिड़काव न करें; मास्क पहनें।"
                },
                {
                    "name": "नीम बीज अर्क 5% (NSKE)",
                    "type": "जैविक कीट निवारक",
                    "dosage": "50 ग्राम प्रति लीटर पानी",
                    "usage_note": "कीटों के आक्रमण से गन्ने के नए कल्लरों की सुरक्षा करता है।",
                    "safety": "पूरी तरह जैविक और सुरक्षित।"
                },
                {
                    "name": "फेरस सल्फेट (हरा कसीस) + यूरिया स्प्रे",
                    "type": "आयरन व नाइट्रोजन टॉनिक",
                    "dosage": "5 ग्राम फेरस सल्फेट + 10 ग्राम यूरिया प्रति लीटर पानी",
                    "usage_note": "पत्तियों के चितकबरेपन को कम कर उन्हें पुनः हरा-भरा करने में सहायक।",
                    "safety": "घोल को अच्छी तरह छानकर सुबह के समय छिड़काव करें।"
                }
            ]
        }
    }

    selected_lang = lang if lang in ["en", "mr", "hi"] else "en"
    disease_entries = medicines_db.get(code, medicines_db["healthy"])
    return disease_entries.get(selected_lang, disease_entries.get("en", []))


def find_nearest_shops(
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    pincode: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 4
) -> List[Dict[str, Any]]:
    """
    Search and rank nearest agro-medical stores based on coordinates,
    district match, or pincode.
    """
    all_shops = load_shops_data()
    if not all_shops:
        return []

    # Use coordinates if provided, else use default regional center
    reference_lat = user_lat if user_lat is not None else DEFAULT_LATITUDE
    reference_lon = user_lon if user_lon is not None else DEFAULT_LONGITUDE

    ranked_shops = []
    for shop in all_shops:
        shop_copy = dict(shop)
        dist_km = haversine_distance(
            reference_lat, reference_lon,
            shop_copy["latitude"], shop_copy["longitude"]
        )
        shop_copy["distance_km"] = dist_km
        shop_copy["google_maps_directions_url"] = (
            f"https://www.google.com/maps/dir/?api=1&origin={reference_lat},{reference_lon}"
            f"&destination={shop_copy['latitude']},{shop_copy['longitude']}"
        )
        ranked_shops.append(shop_copy)

    # If district filter provided, prioritize matching district
    if district:
        dist_clean = district.lower().strip()
        matching = [s for s in ranked_shops if dist_clean in s.get("district", "").lower()]
        others = [s for s in ranked_shops if dist_clean not in s.get("district", "").lower()]
        matching.sort(key=lambda s: s["distance_km"])
        others.sort(key=lambda s: s["distance_km"])
        ranked_shops = matching + others
    else:
        # Sort purely by geographical distance
        ranked_shops.sort(key=lambda s: s["distance_km"])

    return ranked_shops[:limit]


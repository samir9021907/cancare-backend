"""
Farmer Advisory & Community Questions Router (/api/v1/advisory).

Enables:
1. Fetching verified crop management questions and expert answers.
2. Farmers submitting new crop questions to agronomists.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/api/v1/advisory", tags=["Farmer Advisory"])

DEFAULT_COMMUNITY_QUESTIONS = [
    {
        "author_name": "सचिन कदम (कोपरगाव)",
        "title": "ऊसाच्या खोडकिडीचा प्रादुर्भाव कसा रोखावा?",
        "description": "रोप लागवडीनंतर पहिल्या ३० दिवसांत खोडकीड आढळत आहे. कोणता सेंद्रिय किंवा रासायनिक उपाय करावा?",
        "category": "ऊस पिकातील रोग",
        "status": "तज्ञांनी उत्तर दिले (Answered)",
        "expert_answer": "लागवडीच्या वेळी ट्रायकोडर्मा किंवा क्लोरँट्रानिलीप्रोल योग्य प्रमाणात द्यावे. सिंचनाचे प्रमाण योग्य ठेवावे.",
    },
    {
        "author_name": "गजानन पाटील (कोल्हापूर)",
        "title": "ठिबक सिंचनातून विद्राव्य खते देण्याची योग्य वेळ कोणती?",
        "description": "अडसाली ऊसासाठी युरिया आणि १९:१९:१९ खते कोणत्या टप्प्यावर द्यावीत?",
        "category": "खत व्यवस्थापन",
        "status": "तज्ञांनी उत्तर दिले (Answered)",
        "expert_answer": "सकाळी ८ ते १० किंवा संध्याकाळी ४ नंतर ठिबकद्वारे विद्राव्य खते द्यावीत जेणेकरून मुळांना त्वरित अन्नद्रव्ये मिळतात.",
    },
    {
        "author_name": "विठ्ठल मोहिते (सातारा)",
        "title": "उन्हाळ्यात ऊसाला पाण्याचा ताण पडल्यास काय करावे?",
        "description": "पाण्याची उपलब्धता कमी आहे. पाचट आच्छादन कितपत फायदेशीर ठरते?",
        "category": "पाणी व्यवस्थापन",
        "status": "तज्ञांनी उत्तर दिले (Answered)",
        "expert_answer": "एकरी २ ते ३ टन पाचटाचे आच्छादन केल्याने जमिनीतील ओलावा ४०% अधिक काळ टिकून राहतो.",
    }
]


@router.get(
    "/questions",
    response_model=List[schemas.AdvisoryQuestionResponse],
    summary="List farmer advisory & community questions",
    description="Returns community questions with agronomist answers sorted newest first."
)
def list_questions(db: Session = Depends(get_db)):
    # Fetch from database
    db_questions = db.query(models.AdvisoryQuestion).order_by(models.AdvisoryQuestion.created_at.desc()).all()
    
    # If database is fresh, seed default expert questions
    if not db_questions:
        for q in DEFAULT_COMMUNITY_QUESTIONS:
            new_q = models.AdvisoryQuestion(
                author_name=q["author_name"],
                title=q["title"],
                description=q["description"],
                category=q["category"],
                status=q["status"],
                expert_answer=q["expert_answer"]
            )
            db.add(new_q)
        db.commit()
        db_questions = db.query(models.AdvisoryQuestion).order_by(models.AdvisoryQuestion.created_at.desc()).all()

    return [schemas.AdvisoryQuestionResponse.model_validate(q) for q in db_questions]


@router.post(
    "/questions",
    response_model=schemas.AdvisoryQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ask a new crop question to agronomist team",
    description="Submits a farmer question for crop advisory and community resolution."
)
def ask_question(
    question_data: schemas.AdvisoryQuestionCreate,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db)
):
    author = current_user.full_name if current_user else "शेतकरी मित्र (Farmer)"
    new_question = models.AdvisoryQuestion(
        user_id=current_user.id if current_user else None,
        author_name=author,
        title=question_data.title.strip(),
        description=question_data.description.strip(),
        category=question_data.category.strip(),
        status="तज्ञांच्या उत्तराची प्रतीक्षा (Pending)",
        expert_answer="आपला प्रश्न कृषी तज्ञांकडे पाठवला आहे. लवकरच सविस्तर उपाय येथे जोडला जाईल."
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return schemas.AdvisoryQuestionResponse.model_validate(new_question)

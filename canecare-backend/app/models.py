"""
Database Models Module.

Defines the tables stored in SQLite using SQLAlchemy ORM with UUID primary keys:
- User: Stores registered users, credentials, role, and preferred language.
- Scan: Stores leaf image uploads performed by a user.
- Prediction: Stores ML model diagnosis, confidence, and top-3 probabilities.
- Feedback: Stores user feedback on diagnosis accuracy.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a standard UUID string for primary keys."""
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    language = Column(String(10), default="en", nullable=False)  # 'en', 'mr', 'hi'
    role = Column(String(20), default="farmer", nullable=False)  # 'farmer', 'officer', 'admin'
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships: One user can have multiple leaf scans
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="scans")
    prediction = relationship("Prediction", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="scan", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    class_label = Column(String(50), nullable=False)  # healthy, red_rot, rust, yellow_leaf, mosaic
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)      # none, low, medium, high
    top3 = Column(JSON, nullable=False)               # list of {"label": ..., "score": ...}
    model_version = Column(String(50), default="mock-v1.0.0", nullable=False)

    # Relationship back to scan
    scan = relationship("Scan", back_populates="prediction")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    true_class = Column(String(50), nullable=True)     # What the user believes the actual disease is
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship back to scan
    scan = relationship("Scan", back_populates="feedback")

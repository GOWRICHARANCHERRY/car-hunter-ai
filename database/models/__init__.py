import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Float, DateTime, JSON, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Car(Base):
    __tablename__ = "cars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    model = Column(String(200), nullable=True, index=True)
    year = Column(Integer, nullable=True)
    price = Column(BigInteger, nullable=True)
    kms = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission = Column(String(50), nullable=True)
    owners = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True, index=True)
    registration = Column(String(50), nullable=True)
    registration_state = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    seller_name = Column(String(200), nullable=True)
    seller_phone = Column(String(50), nullable=True)
    image_urls = Column(JSON, nullable=True)
    listing_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("CarAnalysis", back_populates="car", uselist=False)
    price_history = relationship("CarPriceHistory", back_populates="car", order_by="CarPriceHistory.changed_at.desc()")
    images = relationship("CarImage", back_populates="car")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_source_listing"),
        UniqueConstraint("source", "listing_url", name="uq_listing_url"),
    )


class CarImage(Base):
    __tablename__ = "car_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False)
    original_url = Column(Text, nullable=True)
    storage_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    filename = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    ai_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    car = relationship("Car", back_populates="images")


class CarAnalysis(Base):
    __tablename__ = "car_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, unique=True)
    score = Column(Integer, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    fair_price = Column(BigInteger, nullable=True)
    recommendation = Column(String(100), nullable=True)
    pros = Column(JSON, nullable=True)
    cons = Column(JSON, nullable=True)
    seller_trust_score = Column(Integer, nullable=True)
    raw_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    car = relationship("Car", back_populates="analysis")


class CarPriceHistory(Base):
    __tablename__ = "car_price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False)
    old_price = Column(BigInteger, nullable=True)
    new_price = Column(BigInteger, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)

    car = relationship("Car", back_populates="price_history")


class FavoriteCar(Base):
    __tablename__ = "favorite_cars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, default="default", index=True)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "car_id", name="uq_user_favorite"),
    )


class SearchProfile(Base):
    __tablename__ = "search_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, default="default", index=True)
    profile_name = Column(String(200), nullable=False)
    budget_min = Column(BigInteger, nullable=True)
    budget_max = Column(BigInteger, nullable=True)
    preferred_models = Column(JSON, nullable=True)
    cities = Column(JSON, nullable=True)
    max_kms = Column(Integer, nullable=True)
    fuel_types = Column(JSON, nullable=True)
    transmission = Column(String(50), nullable=True)
    colors = Column(JSON, nullable=True)
    min_year = Column(Integer, nullable=True)
    max_owners = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_name = Column(String(200), nullable=True)
    seller_phone = Column(String(50), nullable=True, index=True)
    seller_email = Column(String(200), nullable=True)
    sources = Column(JSON, nullable=True)
    total_listings = Column(Integer, default=0)
    active_listings = Column(Integer, default=0)
    trust_score = Column(Integer, nullable=True)
    trust_factors = Column(JSON, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, default="default", unique=True)
    budget_min = Column(BigInteger, nullable=True)
    budget_max = Column(BigInteger, nullable=True)
    preferred_models = Column(JSON, nullable=True)
    cities = Column(JSON, nullable=True)
    max_kms = Column(Integer, nullable=True)
    fuel_types = Column(JSON, nullable=True)
    transmission = Column(String(50), nullable=True)
    colors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_key = Column(String(500), nullable=False, index=True)
    year = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    avg_price = Column(BigInteger, nullable=True)
    median_price = Column(BigInteger, nullable=True)
    lowest_price = Column(BigInteger, nullable=True)
    highest_price = Column(BigInteger, nullable=True)
    sample_count = Column(Integer, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, default="default", index=True)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id", ondelete="SET NULL"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    channel = Column(String(50), nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

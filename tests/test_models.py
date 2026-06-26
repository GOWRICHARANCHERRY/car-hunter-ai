import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy import select

from database.models import Car, CarAnalysis, CarPriceHistory


def test_car_model_creation():
    car = Car(
        source="Cars24",
        source_id="test123",
        title="Honda City 2020",
        brand="Honda",
        model="City",
        year=2020,
        price=750000,
        kms=30000,
        fuel_type="Petrol",
        transmission="Automatic",
        owners=1,
        city="Bangalore",
    )
    assert car.source == "Cars24"
    assert car.brand == "Honda"
    assert car.is_active == True
    assert car.id is not None


def test_car_analysis_creation():
    analysis = CarAnalysis(
        car_id="00000000-0000-0000-0000-000000000001",
        score=92,
        fair_price=780000,
        recommendation="Excellent Deal",
        pros=["First owner", "Low mileage"],
        cons=["Insurance expires soon"],
    )
    assert analysis.score == 92
    assert "First owner" in analysis.pros

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from ai.analysis.scorer import calculate_score, estimate_fair_price, format_deal_text


class MockCar:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_score_excellent_deal():
    car = MockCar(
        title="Honda City ZX",
        brand="Honda",
        model="City ZX",
        year=2020,
        price=700000,
        kms=25000,
        fuel_type="Petrol",
        transmission="Automatic",
        owners=1,
        city="Bangalore",
        registration="KA01",
        description="Well maintained with service history",
        listing_url="https://example.com",
    )
    result = calculate_score(car)
    assert result["score"] >= 70
    assert result["recommendation"] in ("Excellent Deal", "Good Deal")
    assert len(result["pros"]) > 0


def test_score_skip():
    car = MockCar(
        title="Old Car",
        brand="Unknown",
        model="Old",
        year=2010,
        price=500000,
        kms=150000,
        fuel_type="Diesel",
        transmission="Manual",
        owners=4,
        city="Delhi",
        description="",
    )
    result = calculate_score(car)
    assert result["score"] < 50


def test_estimate_fair_price():
    car = MockCar(title="Test", brand="Test", model="Test", year=2020, price=800000, kms=30000, owners=1)
    price = estimate_fair_price(car)
    assert price is not None
    assert price > 0


def test_format_deal_text():
    car = MockCar(title="Honda City", year=2020, kms=42000, price=740000, listing_url="https://example.com")
    text = format_deal_text(car, 94, ["First owner", "Low mileage"], ["Insurance expires"])
    assert "Honda City" in text
    assert "94" in text
    assert "First owner" in text

from typing import Dict, Optional, List
from datetime import datetime
import re

from database.models import Car


def calculate_score(car: Car) -> Dict:
    score = 0
    pros = []
    cons = []

    # Market Price (25 pts)
    if car.price and car.year:
        est = estimate_fair_price(car)
        if est and est > 0:
            ratio = car.price / est
            if ratio < 0.8:
                score += 23
                pros.append("Well below market price")
            elif ratio < 0.95:
                score += 20
                pros.append("Below market price")
            elif ratio < 1.05:
                score += 15
            elif ratio < 1.15:
                score += 8
                cons.append("Slightly above market price")
            else:
                score += 3
                cons.append("Overpriced")

    # Mileage (15 pts)
    if car.kms is not None and car.year:
        age = max(1, datetime.utcnow().year - car.year)
        kms_per_year = car.kms / age
        if kms_per_year < 8000:
            score += 14
            pros.append("Very low mileage")
        elif kms_per_year < 12000:
            score += 11
            pros.append("Low mileage")
        elif kms_per_year < 18000:
            score += 8
        elif kms_per_year < 25000:
            score += 4
            cons.append("Higher than average mileage")
        else:
            score += 1
            cons.append("High mileage")

    # Owner Count (15 pts)
    if car.owners is not None:
        if car.owners == 1:
            score += 15
            pros.append("First owner")
        elif car.owners == 2:
            score += 10
        elif car.owners == 3:
            score += 5
        else:
            cons.append(f"{car.owners} owners")

    # Vehicle Condition (20 pts) - based on age + mileage combo
    if car.year and car.kms:
        age = datetime.utcnow().year - car.year
        kms_per_year = car.kms / max(age, 1)
        condition_score = 20
        if age > 10:
            condition_score -= 8
        elif age > 7:
            condition_score -= 4
        elif age <= 3:
            condition_score += 2
        if kms_per_year > 20000:
            condition_score -= 4
        elif kms_per_year < 10000 and age > 3:
            condition_score += 2
        score += max(0, condition_score)

    # Seller Trust (10 pts) - default mid-range, adjusted by owner count
    if car.owners is not None:
        if car.owners == 1:
            score += 9
        elif car.owners <= 2:
            score += 7
        else:
            score += 4
    else:
        score += 5

    # Resale Value (5 pts)
    if car.brand:
        high_resale_brands = ["Toyota", "Honda", "Maruti", "Mercedes", "BMW"]
        medium_resale_brands = ["Hyundai", "Skoda", "Volkswagen", "Kia"]
        if car.brand in high_resale_brands:
            score += 5
            pros.append("Good resale value")
        elif car.brand in medium_resale_brands:
            score += 3
        else:
            score += 1

    # Service History (10 pts) - based on description keywords
    if car.description:
        desc_lower = car.description.lower()
        service_keywords = ["service", "serviced", "maintained", "service history", "warranty"]
        if any(kw in desc_lower for kw in service_keywords):
            score += 8
            pros.append("Service history mentioned")
        else:
            score += 4
    else:
        score += 4

    score = min(score, 100)

    recommendation = "Skip"
    if score >= 85:
        recommendation = "Excellent Deal"
    elif score >= 70:
        recommendation = "Good Deal"
    elif score >= 50:
        recommendation = "Fair Deal"

    return {
        "score": score,
        "fair_price": estimate_fair_price(car),
        "recommendation": recommendation,
        "pros": pros[:4],
        "cons": cons[:3],
        "seller_trust_score": None,
    }


def estimate_fair_price(car: Car) -> Optional[int]:
    if not car.price or not car.year:
        return None

    age = max(1, datetime.utcnow().year - car.year)
    brand_new_est = car.price * 1.3
    depreciation = min(0.85, 0.10 + (age * 0.07))
    fair = int(brand_new_est * (1 - depreciation))

    if car.kms:
        expected = age * 12000
        if car.kms > expected * 1.2:
            fair -= int(fair * 0.05)
        elif car.kms < expected * 0.7:
            fair += int(fair * 0.05)

    if car.owners and car.owners > 1:
        fair -= int(fair * 0.03 * (car.owners - 1))

    return max(fair, 50000)


def format_deal_text(car: Car, score: int, pros: List[str], cons: List[str]) -> str:
    score_emoji = "🔥" if score >= 90 else "✅"
    stars = "⭐" * (score // 20)
    msg = (
        f"{score_emoji} *New Deal Found*\n\n"
        f"*{car.title}*\n"
        f"{car.year} | {car.kms:,} km\n"
        f"💰 ₹{car.price:,}\n\n"
        f"*Score:* {score}/100 {stars}\n"
    )
    if pros:
        msg += "\n*Pros:*\n" + "\n".join(f"✓ {p}" for p in pros[:3]) + "\n"
    if cons:
        msg += "\n*Cons:*\n" + "\n".join(f"⚠️ {c}" for c in cons[:2]) + "\n"
    if car.listing_url:
        msg += f"\n[View Listing]({car.listing_url})"
    return msg

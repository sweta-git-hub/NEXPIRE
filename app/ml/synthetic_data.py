import numpy as np
import pandas as pd


CATEGORIES = ["Dairy", "Bakery", "Produce", "Meat", "Prepared", "Beverages", "General"]
CATEGORY_PERISHABILITY = {
    "Produce": 1.4,
    "Meat": 1.5,
    "Dairy": 1.3,
    "Prepared": 1.4,
    "Bakery": 1.2,
    "Beverages": 0.8,
    "General": 0.7,
}


def generate_synthetic_dataset(num_samples: int = 1500, random_seed: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic dataset for food batch expiration risk & pricing model training."""
    np.random.seed(random_seed)

    categories = np.random.choice(CATEGORIES, size=num_samples)
    days_to_expiry = np.random.uniform(0.1, 20.0, size=num_samples)
    quantity = np.random.randint(1, 150, size=num_samples)
    cost_price = np.round(np.random.uniform(1.0, 30.0, size=num_samples), 2)
    margin_mult = np.random.uniform(1.2, 2.5, size=num_samples)
    original_selling_price = np.round(cost_price * margin_mult, 2)
    temperature_c = np.round(np.random.uniform(18.0, 35.0, size=num_samples), 1)
    historical_demand_factor = np.round(np.random.uniform(0.6, 1.4, size=num_samples), 2)

    risk_scores = []
    optimal_discounts = []

    for i in range(num_samples):
        cat = categories[i]
        days = days_to_expiry[i]
        qty = quantity[i]
        temp = temperature_c[i]
        perishability = CATEGORY_PERISHABILITY.get(cat, 1.0)

        # Base decay function: exp(-k * days)
        time_factor = np.exp(-0.25 * days / perishability)
        
        # Temp factor: higher ambient temp increases urgency for fresh food
        temp_factor = 1.0 + max(0.0, (temp - 25.0) * 0.02)
        
        # Quantity factor: larger stock with short expiration = higher risk of waste
        qty_factor = 1.0 + min(0.5, (qty / 100.0) * 0.2)

        raw_risk = time_factor * temp_factor * qty_factor
        risk_score = float(np.clip(raw_risk + np.random.normal(0, 0.03), 0.05, 0.99))

        # Optimal discount percentage (0% to 90%) based on risk score
        if risk_score < 0.20:
            discount = np.random.uniform(0.0, 10.0)
        elif risk_score < 0.45:
            discount = np.random.uniform(15.0, 30.0)
        elif risk_score < 0.75:
            discount = np.random.uniform(35.0, 60.0)
        else:
            discount = np.random.uniform(65.0, 90.0)

        discount_pct = float(np.clip(discount, 0.0, 90.0))

        risk_scores.append(round(risk_score, 4))
        optimal_discounts.append(round(discount_pct, 2))

    df = pd.DataFrame(
        {
            "days_to_expiry": days_to_expiry,
            "category": categories,
            "quantity": quantity,
            "cost_price": cost_price,
            "original_selling_price": original_selling_price,
            "temperature_c": temperature_c,
            "historical_demand_factor": historical_demand_factor,
            "risk_score": risk_scores,
            "optimal_discount_pct": optimal_discounts,
        }
    )

    return df

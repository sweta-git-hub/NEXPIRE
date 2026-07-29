import os
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from app.ml.trainer import MODEL_ARTIFACT_PATH, train_pricing_model


class PricingPredictor:
    def __init__(self, model_path: str = MODEL_ARTIFACT_PATH):
        self.model_path = model_path
        self.pipeline = None
        self._load_or_train()

    def _load_or_train(self):
        if not Path(self.model_path).exists():
            print(f"ML Model not found at {self.model_path}. Training initial model...")
            train_pricing_model(artifact_path=self.model_path)

        self.pipeline = joblib.load(self.model_path)

    def reload(self):
        """Reload trained model artifact."""
        self._load_or_train()

    def predict(
        self,
        days_to_expiry: float,
        category: str,
        quantity: int,
        cost_price: float,
        original_selling_price: float,
        temperature_c: float = 25.0,
        historical_demand_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Predict risk_score, suggested_discount_percentage, suggested_price, and risk_level."""
        if self.pipeline is None:
            self._load_or_train()

        input_df = pd.DataFrame(
            [
                {
                    "days_to_expiry": max(0.01, days_to_expiry),
                    "category": category,
                    "quantity": quantity,
                    "cost_price": cost_price,
                    "original_selling_price": original_selling_price,
                    "temperature_c": temperature_c,
                    "historical_demand_factor": historical_demand_factor,
                }
            ]
        )

        preds = self.pipeline.predict(input_df)[0]
        raw_risk = float(preds[0])
        raw_discount = float(preds[1])

        risk_score = round(max(0.0, min(1.0, raw_risk)), 4)
        suggested_discount = round(max(0.0, min(90.0, raw_discount)), 2)

        # Ensure suggested price is at least cost_price * 0.9 or original * (1 - discount)
        suggested_price = round(
            original_selling_price * (1.0 - suggested_discount / 100.0), 2
        )

        # Categorize risk level
        if risk_score < 0.25:
            risk_level = "LOW"
        elif risk_score < 0.50:
            risk_level = "MEDIUM"
        elif risk_score < 0.75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            "risk_score": risk_score,
            "suggested_discount_percentage": suggested_discount,
            "suggested_price": suggested_price,
            "risk_level": risk_level,
        }


# Singleton predictor instance
predictor_instance = None


def get_predictor() -> PricingPredictor:
    global predictor_instance
    if predictor_instance is None:
        predictor_instance = PricingPredictor()
    return predictor_instance

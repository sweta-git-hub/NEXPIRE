"""
predictor.py — NEXPIRE Model A (V2)
======================================
FastAPI-compatible predictor singleton.

The predict() interface is fully backward-compatible with V1:
  - All existing callers (API routes, tests) continue to work unchanged.
  - New fields added to the return dict: urgency_score, reasoning_tags.

Internal changes vs. V1:
  - days_to_expiry is now normalized via urgency.py before any model inference.
  - Discount selection delegates to price_engine.py (discrete revenue search).
  - Model artifact format changed to a dict (see trainer.py docstring).
  - Falls back gracefully to cold-start if model is unavailable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ml.price_engine import (
    PriceEngine,
    PriceRecommendation,
    load_engine,
    recommend_discount,
    get_engine,
    CRITICAL_URGENCY_THRESHOLD,
)
from app.ml.urgency import compute_urgency, get_lookup
from app.ml.train_model import MODEL_ARTIFACT_PATH_V2
from app.ml.trainer import MODEL_ARTIFACT_PATH, train_pricing_model


class PricingPredictor:
    """Singleton predictor for the NEXPIRE pricing model.

    Wraps price_engine.py and urgency.py behind the original predict() interface
    so existing FastAPI routes require zero changes.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_ARTIFACT_PATH_V2
        self._engine: Optional[PriceEngine] = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        """Load the V2 model artifact, training it if not yet available."""
        if not Path(self.model_path).exists():
            print(
                f"[PricingPredictor] Model not found at {self.model_path}. "
                "Training initial model (this may take ~30s)..."
            )
            train_pricing_model(artifact_path=self.model_path)

        self._engine = load_engine(model_path=self.model_path)

    def reload(self) -> None:
        """Reload the model artifact from disk (call after retraining)."""
        self._load_or_train()

    def predict(
        self,
        days_to_expiry: float,
        category: str,
        quantity: int,
        cost_price: float,
        original_selling_price: float,
        temperature_c: float = 28.0,
        historical_demand_factor: float = 1.0,
        product_condition: str = "Excellent",
        # Optional extended context (new in V2)
        precip_probability: float = 0.2,
        is_weekend: int = 0,
        is_holiday: int = 0,
        hour_of_day: int = 12,
        store_foot_traffic_index: float = 0.5,
        past_discount_depth: float = 0.0,
        past_sellthrough_rate: float = 0.7,
        local_demand_score: float = 0.5,
        b2b_flag: int = 0,
        force_liquidate: bool = False,
    ) -> Dict[str, Any]:
        """Predict discount recommendation and risk metrics for a product batch.

        Args:
            days_to_expiry: Days until product expires.
            category: Product category string (must match category_shelf_life.json).
            quantity: Current quantity on hand.
            cost_price: Unit cost price (₹).
            original_selling_price: Current selling price before discount (₹).
            temperature_c: Today's ambient temperature (°C). Default 28.
            historical_demand_factor: Historical demand multiplier (0.6–1.4). Default 1.0.
            product_condition: One of "Excellent", "Good", "Fair", "Poor".
            precip_probability: Probability of rain (0–1). Default 0.2.
            is_weekend: 1 if today is Saturday/Sunday. Default 0.
            is_holiday: 1 if today is a public holiday. Default 0.
            hour_of_day: Hour of day (8–20). Default 12.
            store_foot_traffic_index: Foot traffic level (0–1). Default 0.5.
            past_discount_depth: Average historical markdown (%). Default 0.
            past_sellthrough_rate: Historical sell-through fraction (0–1). Default 0.7.
            local_demand_score: Distance-weighted nearby claim activity (0–1). Default 0.5.
            b2b_flag: 1 if batch is for B2B/bulk customer. Default 0.
            force_liquidate: Skip margin floor constraint. Default False.

        Returns:
            dict with keys:
              - risk_score (float 0–1): Urgency-based risk metric.
              - risk_level (str): "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
              - suggested_discount_percentage (float): Recommended discount %.
              - suggested_price (float ₹): Final price after discount.
              - urgency_score (float 0–1): Normalized category-relative urgency.
              - reasoning_tags (List[str]): Human-readable tags.
              - is_cold_start (bool): True if model fallback was used.
        """
        if self._engine is None:
            self._load_or_train()

        # --- Condition multiplier (V1 backward compat) ---
        CONDITION_MULTIPLIERS = {
            "Excellent": 1.0,
            "Good": 1.05,
            "Fair": 1.15,
            "Poor": 1.35,
        }
        condition_mult = CONDITION_MULTIPLIERS.get(product_condition, 1.0)

        # Adjust velocity proxy from historical_demand_factor
        velocity_proxy = historical_demand_factor * 10.0  # map to units/day estimate

        batch_info = {
            "category": category,
            "days_to_expiry": max(0.0, days_to_expiry),
            "current_price": original_selling_price,
            "cost_price": cost_price,
            "qty_on_hand": quantity,
            "avg_daily_velocity_7d": velocity_proxy,
            "avg_daily_velocity_28d": velocity_proxy,
            "temperature_today": temperature_c,
            "precip_probability": precip_probability,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "hour_of_day": hour_of_day,
            "store_foot_traffic_index": store_foot_traffic_index,
            "past_discount_depth": past_discount_depth,
            "past_sellthrough_rate": past_sellthrough_rate,
            "local_demand_score": local_demand_score,
            "b2b_flag": b2b_flag,
        }

        rec: PriceRecommendation = recommend_discount(
            batch_info=batch_info,
            engine=self._engine,
            force_liquidate=force_liquidate,
        )

        # Apply condition multiplier to urgency-based risk_score
        raw_risk = rec.urgency_score * condition_mult
        risk_score = round(max(0.0, min(1.0, raw_risk)), 4)

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
            # V1 fields (preserved for backward compatibility)
            "risk_score": risk_score,
            "suggested_discount_percentage": rec.discount_pct,
            "suggested_price": rec.final_price,
            "risk_level": risk_level,
            # V2 additional fields
            "urgency_score": rec.urgency_score,
            "expected_sell_probability": rec.expected_sell_probability,
            "reasoning_tags": rec.reasoning_tags,
            "is_cold_start": rec.is_cold_start,
        }


# ---------------------------------------------------------------------------
# Singleton predictor instance (matches V1 pattern)
# ---------------------------------------------------------------------------
predictor_instance: Optional[PricingPredictor] = None


def get_predictor() -> PricingPredictor:
    """Return the module-level singleton predictor (lazy-loaded)."""
    global predictor_instance
    if predictor_instance is None:
        predictor_instance = PricingPredictor()
    return predictor_instance

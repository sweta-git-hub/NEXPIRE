import os
import joblib
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline

from app.ml.synthetic_data import generate_synthetic_dataset, CATEGORIES

MODEL_ARTIFACT_PATH = os.environ.get(
    "ML_MODEL_PATH",
    str(Path(__file__).parent / "artifacts" / "pricing_model.joblib"),
)


def train_pricing_model(num_samples: int = 1500, artifact_path: str = MODEL_ARTIFACT_PATH):
    """Train Scikit-Learn multi-output regression model to predict risk_score and optimal_discount_pct."""
    import pandas as pd
    import numpy as np
    from pathlib import Path

    # Check for generated synthetic datasets
    base_path = Path("/app/output/full_dataset")
    if not base_path.exists():
        # local workspace fallbacks
        base_path = Path(__file__).parent.parent.parent / "output" / "full_dataset"

    sales_path = base_path / "sales_history.csv"
    products_path = base_path / "products.csv"
    weather_path = base_path / "weather_history.csv"

    if sales_path.exists() and products_path.exists() and weather_path.exists():
        print(f"Loading generated training data from {base_path}...")
        sales_df = pd.read_csv(sales_path)
        prod_df = pd.read_csv(products_path)
        wx_df = pd.read_csv(weather_path)

        # Merge datasets
        df = sales_df.merge(prod_df, on="sku_id", how="inner")
        df = df.merge(wx_df, on=["store_id", "date"], how="inner")

        # Map feature columns
        df["days_to_expiry"] = df["time_to_expiry_hours_at_sale"] / 24.0
        df["quantity"] = df["units_sold"]
        df["cost_price"] = df["unit_cost_inr"]
        df["original_selling_price"] = df["standard_retail_price_inr"]
        df["temperature_c"] = df["avg_temperature_c"]
        df["historical_demand_factor"] = np.random.uniform(0.6, 1.4, size=len(df))

        # Calculate target columns matching model dynamics
        from app.ml.synthetic_data import CATEGORY_PERISHABILITY
        perish_series = df["category"].map(CATEGORY_PERISHABILITY).fillna(1.0)
        time_factor = np.exp(-0.25 * df["days_to_expiry"] / perish_series)
        temp_factor = 1.0 + np.maximum(0.0, (df["temperature_c"] - 25.0) * 0.02)
        qty_factor = 1.0 + np.minimum(0.5, (df["quantity"] / 100.0) * 0.2)
        
        df["risk_score"] = np.clip(time_factor * temp_factor * qty_factor + np.random.normal(0, 0.03, size=len(df)), 0.05, 0.99)
        df["optimal_discount_pct"] = df["discount_depth_pct"]

        # Select sample
        df = df.sample(n=min(num_samples, len(df)), random_state=42).reset_index(drop=True)
    else:
        print("Generated training data not found. Falling back to synthetic simulation...")
        df = generate_synthetic_dataset(num_samples=num_samples)

    feature_cols = [
        "days_to_expiry",
        "category",
        "quantity",
        "cost_price",
        "original_selling_price",
        "temperature_c",
        "historical_demand_factor",
    ]
    target_cols = ["risk_score", "optimal_discount_pct"]

    X = df[feature_cols]
    y = df[target_cols]

    categorical_features = ["category"]
    numerical_features = [
        "days_to_expiry",
        "quantity",
        "cost_price",
        "original_selling_price",
        "temperature_c",
        "historical_demand_factor",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            (
                "cat",
                OneHotEncoder(categories=[CATEGORIES], handle_unknown="ignore"),
                categorical_features,
            ),
        ]
    )

    regressor = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )

    pipeline.fit(X, y)

    # Ensure artifact directory exists
    artifact_dir = Path(artifact_path).parent
    artifact_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, artifact_path)
    return artifact_path

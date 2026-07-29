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

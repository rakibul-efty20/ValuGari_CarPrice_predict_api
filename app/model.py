import logging
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.schemas import CarFeatures

logger = logging.getLogger(__name__)

RECOGNIZED_MODELS = {
    "model_Vogue": "vogue",
    "model_Harrier": "harrier",
    "model_RX": "rx",
    "model_CR-V": "cr-v",
}


class ModelLoadError(RuntimeError):
    """Raised when the pickled artifact is missing or malformed."""


class CarPriceModel:
    """Wraps the fitted RandomForestRegressor exported from the notebook.

    The pickle is a dict: {"model": <fitted estimator>, "features": [...]}.
    `features` is the exact, ordered list of columns the model was trained
    on — everything here is built around reproducing that shape from raw
    API input, rather than hardcoding column order in two places.
    """

    def __init__(self, model_path: str):
        path = Path(model_path)
        if not path.exists():
            raise ModelLoadError(
                f"Model file not found at '{path.resolve()}'. "
                "Copy car_price_model.pkl into that location before starting the API."
            )
        try:
            artifact = joblib.load(path)
            self.model = artifact["model"]
            self.feature_order: list[str] = artifact["features"]
        except Exception as exc:  # noqa: BLE001 - surface any load failure clearly
            raise ModelLoadError(f"Failed to load model artifact: {exc}") from exc

        logger.info("Model loaded from %s. Expects features: %s", path, self.feature_order)

    def _to_feature_row(self, payload: CarFeatures) -> pd.DataFrame:
        """Derive the 10 engineered columns from raw request fields.

        NOTE: this mapping is coupled to whatever top-10 the notebook's Random
        Forest importance step selected. Model recognition is a simple
        case-insensitive match against the 4 nameplates that made the cut
        (Vogue, Harrier, RX, CR-V) — anything else is treated as "other" and
        the model falls back on engine/mileage/year/condition/brand alone.
        """
        model_key = payload.model.strip().lower()
        brand_key = payload.brand.strip().lower()

        derived = {
            "engine_capacity": payload.engine_capacity,
            "km_run": payload.km_run,
            "man_year": payload.man_year,
            "condition_New": int(payload.condition == "New"),
            "condition_Used": int(payload.condition == "Used"),
            "brand_Toyota": int(brand_key == "toyota"),
        }
        for feature_name, match_value in RECOGNIZED_MODELS.items():
            derived[feature_name] = int(model_key == match_value)

        missing = [f for f in self.feature_order if f not in derived]
        if missing:
            raise KeyError(
                f"Model expects features this endpoint can't derive: {missing}. "
                "Update CarFeatures and _to_feature_row to cover them."
            )
        return pd.DataFrame([[derived[f] for f in self.feature_order]], columns=self.feature_order)

    def predict(self, payload: CarFeatures) -> dict:
        row = self._to_feature_row(payload)

        point_estimate = float(self.model.predict(row)[0])

        # RandomForest has no native confidence interval, but each tree in the
        # ensemble is itself a prediction — their spread is a legitimate,
        # model-derived uncertainty range rather than an invented one.
        per_tree = np.array([tree.predict(row.values)[0] for tree in self.model.estimators_])
        low, high = np.percentile(per_tree, [10, 90])

        return {
            "predicted_price": round(point_estimate, 0),
            "price_range_low": round(float(low), 0),
            "price_range_high": round(float(high), 0),
        }


@lru_cache
def get_model() -> CarPriceModel:
    """FastAPI dependency: loads the model once per process, reused after that."""
    return CarPriceModel(settings.model_path)

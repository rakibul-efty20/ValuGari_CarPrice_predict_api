from typing import Literal

from pydantic import BaseModel, Field


class CarFeatures(BaseModel):
    """Raw car attributes the caller supplies. These map to the 10 engineered
    features the model was actually trained on (see app/model.py)."""

    brand: str = Field(..., description="e.g. Toyota, Honda, BMW, Nissan")
    model: str = Field(..., description="e.g. Corolla, Harrier, Vogue, CR-V")
    engine_capacity: float = Field(..., ge=600, le=6000, description="Engine size, cc")
    km_run: float = Field(..., ge=0, le=500_000, description="Total kilometers driven")
    man_year: int = Field(..., ge=1990, le=2026, description="Manufacture year")
    condition: Literal["New", "Used", "Reconditioned"]

    model_config = {
        "json_schema_extra": {
            "example": {
                "brand": "Toyota",
                "model": "Harrier",
                "engine_capacity": 2000,
                "km_run": 45000,
                "man_year": 2021,
                "condition": "Reconditioned",
            }
        }
    }


class PredictionResponse(BaseModel):
    predicted_price: float = Field(..., description="Point estimate, in Tk")
    price_range_low: float = Field(..., description="~10th percentile across the forest's trees")
    price_range_high: float = Field(..., description="~90th percentile across the forest's trees")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

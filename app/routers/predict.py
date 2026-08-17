import logging

from fastapi import APIRouter, Depends, HTTPException

from app.model import CarPriceModel, get_model
from app.schemas import CarFeatures, HealthResponse, PredictionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict_price(
    payload: CarFeatures,
    model: CarPriceModel = Depends(get_model),
) -> PredictionResponse:
    try:
        result = model.predict(payload)
    except Exception:
        logger.exception("Prediction failed for payload: %s", payload)
        raise HTTPException(status_code=500, detail="Prediction failed") from None
    return PredictionResponse(**result)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    try:
        get_model()
        loaded = True
    except Exception:
        loaded = False
    return HealthResponse(status="ok" if loaded else "degraded", model_loaded=loaded)

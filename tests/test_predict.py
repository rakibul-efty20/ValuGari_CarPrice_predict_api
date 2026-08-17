from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "brand": "Toyota",
    "model": "Harrier",
    "engine_capacity": 2000,
    "km_run": 45000,
    "man_year": 2021,
    "condition": "Reconditioned",
}


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_valid_payload():
    response = client.post("/api/v1/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_price"] > 0
    assert body["price_range_low"] <= body["predicted_price"] <= body["price_range_high"]


def test_predict_unrecognized_model_still_works():
    payload = {**VALID_PAYLOAD, "model": "SomeObscureModelNotInTraining"}
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["predicted_price"] > 0


def test_predict_rejects_bad_condition():
    bad_payload = {**VALID_PAYLOAD, "condition": "Excellent"}
    response = client.post("/api/v1/predict", json=bad_payload)
    assert response.status_code == 422


def test_predict_rejects_out_of_range_engine():
    bad_payload = {**VALID_PAYLOAD, "engine_capacity": 50000}
    response = client.post("/api/v1/predict", json=bad_payload)
    assert response.status_code == 422


def test_predict_rejects_missing_field():
    bad_payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "man_year"}
    response = client.post("/api/v1/predict", json=bad_payload)
    assert response.status_code == 422

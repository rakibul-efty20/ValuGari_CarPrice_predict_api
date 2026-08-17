// Point this at wherever the FastAPI backend is running. Works whether this
// page is opened directly (file://) or served some other way, as long as the
// API's CORS settings allow this page's origin (ships with allow_origins=["*"]).
const API_BASE_URL = "http://127.0.0.1:8000";

const els = {
  statusPill: document.getElementById("statusPill"),
  statusText: document.getElementById("statusText"),
  form: document.getElementById("predictForm"),
  btn: document.getElementById("predictBtn"),
  btnLabel: document.querySelector("#predictBtn .btn-label"),
  resultEmpty: document.getElementById("resultEmpty"),
  resultLoading: document.getElementById("resultLoading"),
  resultError: document.getElementById("resultError"),
  resultReady: document.getElementById("resultReady"),
  errorDetail: document.getElementById("errorDetail"),
  priceValue: document.getElementById("priceValue"),
  rangeFill: document.getElementById("rangeFill"),
  rangeMarker: document.getElementById("rangeMarker"),
  rangeLowLabel: document.getElementById("rangeLowLabel"),
  rangeHighLabel: document.getElementById("rangeHighLabel"),
  apiBaseFooter: document.getElementById("apiBaseFooter"),
};

const RESULT_STATES = [els.resultEmpty, els.resultLoading, els.resultError, els.resultReady];

function showResultState(target) {
  RESULT_STATES.forEach((el) => el.classList.toggle("is-visible", el === target));
}

function setStatus(state, label) {
  els.statusPill.dataset.state = state;
  els.statusText.textContent = label;
}

// South Asian digit grouping (lakh/crore style): 3562218 -> "35,62,218"
function formatTaka(num) {
  const n = Math.round(num);
  const sign = n < 0 ? "-" : "";
  const str = Math.abs(n).toString();
  if (str.length <= 3) return sign + str;
  const last3 = str.slice(-3);
  const rest = str.slice(0, -3);
  const grouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${sign}${grouped},${last3}`;
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, { method: "GET" });
    if (!res.ok) throw new Error("unhealthy");
    const body = await res.json();
    setStatus(body.model_loaded ? "online" : "offline", body.model_loaded ? "API connected" : "Model not loaded");
  } catch {
    setStatus("offline", "API offline");
  }
}

function buildPayload() {
  return {
    brand: document.getElementById("brand").value,
    model: document.getElementById("model").value,
    condition: document.getElementById("condition").value,
    man_year: Number(document.getElementById("manYear").value),
    engine_capacity: Number(document.getElementById("engineCapacity").value),
    km_run: Number(document.getElementById("kmRun").value),
  };
}

function describeApiError(body) {
  if (!body || !body.detail) return "The API rejected the request.";
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail.map((e) => `${(e.loc || []).slice(-1)[0] ?? "field"}: ${e.msg}`).join("; ");
  }
  return "The API rejected the request.";
}

function renderPrediction(result) {
  const { predicted_price: estimate, price_range_low: low, price_range_high: high } = result;

  showResultState(els.resultReady);
  els.priceValue.textContent = formatTaka(estimate);
  els.rangeLowLabel.textContent = `Tk ${formatTaka(low)}`;
  els.rangeHighLabel.textContent = `Tk ${formatTaka(high)}`;

  let span = high - low;
  if (span <= 0) span = Math.max(estimate * 0.1, 1);
  const pad = span * 0.15;
  const barMin = low - pad;
  const barMax = high + pad;
  const barSpan = barMax - barMin || 1;

  const fillLeftPct = ((low - barMin) / barSpan) * 100;
  const fillWidthPct = ((high - low) / barSpan) * 100;
  const markerLeftPct = ((estimate - barMin) / barSpan) * 100;

  // Reset first so the marker/fill transition actually animates on each new result.
  els.rangeFill.style.left = "50%";
  els.rangeFill.style.width = "0%";
  els.rangeMarker.style.left = "50%";
  els.rangeFill.getBoundingClientRect(); // force reflow
  requestAnimationFrame(() => {
    els.rangeFill.style.left = `${fillLeftPct}%`;
    els.rangeFill.style.width = `${fillWidthPct}%`;
    els.rangeMarker.style.left = `${markerLeftPct}%`;
  });
}

async function handleSubmit(event) {
  event.preventDefault();

  els.btn.disabled = true;
  els.btn.classList.add("is-loading");
  els.btnLabel.textContent = "Estimating\u2026";
  showResultState(els.resultLoading);

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    const body = await res.json().catch(() => null);

    if (!res.ok) {
      els.errorDetail.textContent = describeApiError(body);
      showResultState(els.resultError);
    } else {
      renderPrediction(body);
      setStatus("online", "API connected");
    }
  } catch {
    els.errorDetail.textContent = `Couldn't reach ${API_BASE_URL}. Make sure the FastAPI server is running (uvicorn app.main:app --reload).`;
    showResultState(els.resultError);
    setStatus("offline", "API offline");
  } finally {
    els.btn.disabled = false;
    els.btn.classList.remove("is-loading");
    els.btnLabel.textContent = "Estimate price";
  }
}

["engineCapacity", "kmRun"].forEach((id) => {
  document.getElementById(id).addEventListener("input", (e) => {
    e.target.value = e.target.value.replace(/[^0-9]/g, "");
  });
});

els.form.addEventListener("submit", handleSubmit);
els.apiBaseFooter.textContent = API_BASE_URL;
checkHealth();

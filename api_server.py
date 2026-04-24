"""
FastAPI HTTP Server for the Bounded Emotion Memory System.

Exposes the FeedbackSystem as a REST API so the Android app can send
emotion events (received from the EEG inference RunPod endpoint) and
receive LLM-generated feedback over HTTPS.

Endpoints:
  GET  /health          → liveness probe
  GET  /state           → current emotion engine state (debug)
  POST /process-emotion → main endpoint: send emotion + GPS, get feedback
  GET  /docs            → auto-generated Swagger UI (built into FastAPI)
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import FeedbackSystem
from models import ContextData

# ---------------------------------------------------------------------------
# Emotion label normalizer
# ---------------------------------------------------------------------------
# The RunPod EEG inference handler outputs: "neutral", "sadness", "enthusiasm", "fear"
# Our RAG service and state machine use:    "neutral", "sad",     "happy",       "fear"
# This map translates the handler's output to our internal canonical labels.
_EMOTION_NORMALIZER = {
    # Inference handler output → our internal label
    "neutral":    "neutral",
    "sadness":    "sad",
    "enthusiasm": "happy",
    "fear":       "fear",
    # Pass-through for anything already in canonical form
    "sad":        "sad",
    "happy":      "happy",
    "anger":      "anger",
    "angry":      "anger",
}


def normalize_emotion(raw: str) -> str:
    """Translate an inference handler emotion label to our internal label."""
    cleaned = raw.lower().strip()
    return _EMOTION_NORMALIZER.get(cleaned, cleaned)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bounded Emotion Memory – Feedback API",
    description=(
        "LLM + RAG based emotion feedback system. "
        "Receives emotion labels from the EEG inference endpoint, "
        "combines with GPS context, and generates supportive feedback."
    ),
    version="1.0.0",
)

# Allow all origins so the Android app can call this freely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared FeedbackSystem instance — initialised once at startup.
print("[api_server] Initialising FeedbackSystem...")
system = FeedbackSystem()
print("[api_server] FeedbackSystem ready.")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class EmotionRequest(BaseModel):
    """
    Payload sent by the app after each EEG inference result.

    Two modes:
      1. GPS mode  → provide latitude + longitude; context is auto-built.
      2. Manual mode → provide location, time_of_day, weather, weekday manually.

    The emotion field accepts both inference handler labels ("sadness", "enthusiasm")
    and canonical labels ("sad", "happy") — both are normalised automatically.
    """
    emotion: str                              # e.g. "sadness" | "neutral" | "enthusiasm" | "fear"

    # GPS mode (preferred — used by the mobile app)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Manual mode (for testing without a phone)
    location: Optional[str] = "unknown"
    time_of_day: Optional[str] = None        # "YYYY-MM-DD HH:MM:SS"
    weather: Optional[str] = "unknown"
    weekday: Optional[bool] = None           # auto-detected from system time if None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "GPS mode (from app)",
                    "value": {
                        "emotion": "sadness",
                        "latitude": 6.9271,
                        "longitude": 79.8612,
                    },
                },
                {
                    "summary": "Manual mode (for testing)",
                    "value": {
                        "emotion": "sadness",
                        "location": "home",
                        "time_of_day": "2026-04-24 09:00:00",
                        "weather": "rain",
                        "weekday": True,
                    },
                },
            ]
        }


class FeedbackOut(BaseModel):
    """Response returned for each emotion event."""
    generated: bool                          # True if feedback was produced
    feedback: Optional[str] = None          # The feedback message
    emotion_context: Optional[str] = None   # e.g. "sad (5m)" — for debugging
    normalised_emotion: Optional[str] = None  # The label after normalisation


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health():
    """
    Liveness probe.
    RunPod and the app use this to check the service is up before sending data.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/state", tags=["Debug"])
def get_state():
    """
    Returns the current emotion engine state as a human-readable string.
    Useful for debugging — call this from a browser or Postman.
    """
    return {"state": system.get_current_state()}


@app.post("/process-emotion", response_model=FeedbackOut, tags=["Feedback"])
def process_emotion(req: EmotionRequest):
    """
    Main endpoint.

    **GPS mode** (used by the mobile app):
    - Send `emotion` (from the EEG inference result) + `latitude` + `longitude`.
    - Location name, weather, weekday are auto-detected server-side.

    **Manual mode** (for testing without a real device):
    - Send `emotion`, `location`, `time_of_day`, `weather`, `weekday`.

    The emotion label is normalised automatically:
    - `"sadness"` → `"sad"`, `"enthusiasm"` → `"happy"`, `"fear"` → `"fear"`

    Returns `generated: false` if the state machine decides no feedback is needed yet
    (e.g. emotion hasn't changed and the periodic interval hasn't elapsed).
    """
    try:
        # Normalise the label before anything else
        emotion = normalize_emotion(req.emotion)

        if req.latitude is not None and req.longitude is not None:
            # ── GPS mode ──────────────────────────────────────────────────
            response = system.process_emotion_with_gps(
                emotion=emotion,
                latitude=req.latitude,
                longitude=req.longitude,
            )
        else:
            # ── Manual / test mode ────────────────────────────────────────
            now = datetime.now()
            is_weekday = req.weekday if req.weekday is not None else (now.weekday() < 5)

            context = ContextData(
                location=req.location or "unknown",
                time_of_day=req.time_of_day or now.strftime("%Y-%m-%d %H:%M:%S"),
                weather=req.weather or "unknown",
                weekday=is_weekday,
            )
            response = system.process_emotion_detection(emotion, context)

        if response:
            return FeedbackOut(
                generated=True,
                feedback=response.message,
                emotion_context=response.emotion_context,
                normalised_emotion=emotion,
            )
        else:
            return FeedbackOut(generated=False, normalised_emotion=emotion)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Dev entrypoint (not used in Docker — Docker uses start.sh + uvicorn directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)

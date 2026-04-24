# Bounded Emotion Memory System

## Overview

This is the **LLM-based feedback generation module** for the Final Year Project:
**"Emotion & Context-Aware Digital Companion for Mental Wellbeing"**.

The system receives emotion detections from a mobile app, decides *when* to respond based on a set of rules, and generates a short, supportive message using a locally-running AI model (Phi-3 via Ollama). It is **not a chatbot** — it is a one-way nudge system that sends a message only when it's meaningful to do so.

---

## System Architecture

```
Mobile App (Android)
        │
        │  emotion label + GPS coordinates
        ▼
┌─────────────────────────────────────────────────────────┐
│                  FeedbackSystem (main.py)                │
│                                                         │
│  ┌─────────────────┐    ┌───────────────────────────┐  │
│  │  ContextService  │    │       ContextEngine        │  │
│  │ (context_service)│    │        (logic.py)          │  │
│  │                  │    │                            │  │
│  │ GPS → location   │    │  Bounded emotion state     │  │
│  │ GPS → weather    │    │  Trigger evaluation        │  │
│  │ time → time_str  │    │  Prompt context builder    │  │
│  └─────────────────┘    └───────────────────────────┘  │
│                                    │                     │
│                          ┌─────────▼──────────┐         │
│  ┌─────────────────┐     │    LLMInference     │         │
│  │   RAGService     │────▶   (llm_service.py)  │         │
│  │ (rag_service.py) │    │                     │         │
│  │                 │     │  LangChain + Ollama  │         │
│  │ Reads local     │     │  Phi-3 local model  │         │
│  │ rag_docs_v2/    │     └─────────────────────┘         │
│  └─────────────────┘                                     │
└─────────────────────────────────────────────────────────┘
        │
        │  FeedbackResponse (message string)
        ▼
    Mobile App displays message to user
```

---

## Installation

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally
- Phi-3 model pulled: `ollama pull phi3`

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenWeatherMap API key
echo OPENWEATHER_API_KEY=your_key_here > .env
```

### Verify Installation

```bash
python verify_install.py
python verify_ollama.py
```

---

## File-by-File Explanation

### `config.py` — Configuration Constants

Holds all the tunable parameters for the system. All time values are in **minutes**.

| Constant | Default | Description |
|---|---|---|
| `EMOTION_CHECK_INTERVAL` | `5` | How often the mobile app sends emotion detections. Used to detect a "just changed" emotion. |
| `T_RECENT` | `10` | Window within which a previous emotion is still considered relevant for context. If the switch happened more than 10 minutes ago, the previous emotion is ignored. |
| `FEEDBACK_INTERVAL` | `10` | How frequently follow-up nudges are sent when an emotion persists (e.g., every 10 minutes of ongoing stress). |
| `LLM_MODEL` | `"phi3"` | Name of the Ollama model to use. |
| `LLM_TEMPERATURE` | `0.7` | LLM sampling temperature. Higher = more varied responses. |
| `LLM_MAX_OUTPUT_TOKENS` | `150` | Caps response length to keep messages short. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL. |
| `WEATHER_API_KEY` | `None` | Set via `.env` file as `OPENWEATHER_API_KEY`. |
| `WEATHER_API_URL` | OpenWeatherMap endpoint | Used by `ContextService` to fetch live weather. |

---

### `models.py` — Data Models (Pydantic)

Defines all structured data types used throughout the system. Uses [Pydantic](https://docs.pydantic.dev/) for validation.

#### `ContextData`
Represents the contextual snapshot at the moment an emotion is detected.

```python
class ContextData(BaseModel):
    location: str     # Full human-readable address (e.g., "Mount Lavinia, Colombo, Sri Lanka")
    time_of_day: str  # Formatted timestamp string (e.g., "2026-03-19 11:30:00")
    weekday: bool     # True if Monday–Friday
    weather: str      # Weather condition (e.g., "sunny", "rainy")
    latitude: Optional[float]   # Raw GPS (for logging)
    longitude: Optional[float]  # Raw GPS (for logging)
```

#### `EmotionState`
The **core bounded memory** of the system. Only ever holds **two emotions at most**.

```python
class EmotionState(BaseModel):
    current_emotion: str              # The active detected emotion
    current_emotion_start_time: datetime  # When it started

    previous_emotion: Optional[str]           # The emotion before current (None at start)
    previous_emotion_end_time: Optional[datetime]  # When previous ended

    last_feedback_time: Optional[datetime]   # When feedback was last sent
```

> **Design decision**: By limiting memory to 2 emotions, the system avoids user profiling, keeps privacy-safe, and prevents context drift over long sessions.

#### `FeedbackTrigger`
Decision object returned by the trigger evaluation step.

```python
class FeedbackTrigger(BaseModel):
    should_generate: bool   # True = send feedback
    reason: str             # "emotion_change", "periodic (N.Nm)", "no_trigger", "no_state"
```

#### `FeedbackResponse`
The final output returned to the mobile app.

```python
class FeedbackResponse(BaseModel):
    message: str            # The supportive message to show the user
    timestamp: datetime     # When it was generated
    emotion_context: str    # e.g., "stressed (12.0m)" — for logging
```

---

### `logic.py` — ContextEngine (State Machine & Trigger Logic)

This is the **brain** of the system. The `ContextEngine` class manages how emotion state transitions work and whether feedback should be triggered.

#### State Transitions (`update_emotion`)

```
First call:   → Sets current_emotion, no previous
Same emotion: → No change (memory unchanged)
New emotion:  → current → previous, new → current
```

Rules enforced:
- `previous_emotion` and `current_emotion` are **always different**
- Memory updates **only on emotion change**
- Old feedback time is **preserved across changes** (for cooldown logic)

#### Trigger Evaluation (`evaluate_feedback_trigger`)

Two triggers exist:

| Trigger | Condition | Reason string |
|---|---|---|
| **Emotion Change** | `emotion_duration < EMOTION_CHECK_INTERVAL` | `"emotion_change"` |
| **Periodic Nudge** | `time_since_last_feedback >= FEEDBACK_INTERVAL` (or `emotion_duration >= FEEDBACK_INTERVAL` if no prior feedback) | `"periodic (N.Nm)"` |

If neither condition is met, returns `should_generate=False` with reason `"no_trigger"`.

#### Prompt Context Builder (`get_prompt_context`)

Builds the dictionary passed to the LLM. Crucially, **previous emotion is only included if it happened within `T_RECENT` minutes**:

```python
# Result example (previous emotion recent):
{
    "current_emotion": "stressed",
    "duration_minutes": 7.5,
    "include_previous": True,
    "previous_emotion": "calm",
    "minutes_since_change": 7.5
}

# Result example (previous emotion too old or None):
{
    "current_emotion": "stressed",
    "duration_minutes": 25.0,
    "include_previous": False
}
```

---

### `context_service.py` — Automatic Context Detection

The mobile app only needs to send **GPS coordinates**. This service automatically enriches them into full context.

#### `get_time_context(timestamp)`
- Returns a formatted timestamp string (`"YYYY-MM-DD HH:MM:SS"`) and a boolean for weekday.
- Defaults to `datetime.now()` if no timestamp is given.

#### `get_semantic_location(latitude, longitude)`
- Calls **[OpenStreetMap Nominatim](https://nominatim.org/)** reverse geocoding API (free, no key needed).
- Returns a full human-readable address: e.g., `"University of Moratuwa, Katubedda, Moratuwa, Sri Lanka"`.
- Falls back to `"Unknown (lat, lon)"` on API failure.

#### `get_weather(latitude, longitude)`
- Calls **[OpenWeatherMap](https://openweathermap.org/api)** API using the key from `.env`.
- Returns raw condition string: `"clear"`, `"clouds"`, `"rain"`, `"thunderstorm"`, etc.
- Returns `"unknown"` if no API key is configured or the call fails.

#### `build_context(latitude, longitude, timestamp)` ← Main Method
Composes all three into a complete `ContextData` object. This is the method called by `FeedbackSystem`.

```python
context = service.build_context(latitude=6.9271, longitude=79.8612)
# → ContextData(location="...", time_of_day="...", weekday=True, weather="rain", ...)
```

---

### `rag_service.py` — Retrieval-Augmented Generation

Assembles a knowledge-grounded **system prompt** tailored to the user's specific context, feeding it into the LLM. It loads local text documents from `rag_docs_v2/`.

#### Knowledge Retrieval Process
1. **System Guardrails**: Always includes `00_system_guardrails.txt` (safety rules and fallback constraints).
2. **Emotion Rules**: Looks up the document for the current emotion (e.g., `10_emotion_sad.txt`).
3. **Context Extraction**: Pulls exactly the relevant paragraphs from context docs based on:
   - **Time**: `20_context_time_of_day.txt` (e.g., pulling only the `MORNING` section)
   - **Weather**: `21_context_weather.txt` (e.g., `RAIN`)
   - **Location**: `22_context_location.txt` (e.g., `HOME`)
   - **Day Type**: `23_context_day_type.txt` (e.g., `WEEKDAY`)

This dynamically constructed systemic guidance ensures the LLM's responses are perfectly tuned to the situation detected, going far beyond the user prompt alone.

---

### `llm_service.py` — LLM Inference (LangChain + Ollama)

Wraps the local **Phi-3** model (running via Ollama) using **LangChain** to generate the final message.

#### Chain Structure

```
ChatPromptTemplate  →  ChatOllama (Phi-3)  →  StrOutputParser
      │                      │                       │
Dynamic RAG System     Local inference          Raw string
Prompt + User prompt   on localhost             (cleaned up)
```

#### System Prompt (RAG-enriched + Safety Constraints)
The LLM is given strict rules combined with context guidance from `rag_service`:
- ✅ One short, kind message (2–3 sentences max)
- ✅ Calm, non-judgmental, warm tone
- ✅ Plain text only (no markdown, no emojis)
- ❌ No medical advice or diagnosis
- ❌ No questions to the user
- ❌ No formatting

#### User Prompt Template
```
User status:
- Emotion: {current_emotion} (for {duration_minutes} mins)
[- Previous emotion: {previous_emotion} (changed {minutes_since_change} mins ago)]  ← only if relevant
- Location: {location}
- Time: {time_of_day}
- Weather: {weather}

Task: Write a short, supportive message for this user.
```

#### Fallback
If Ollama is unavailable or throws an error, returns a safe default:
> *"Take a moment to breathe. I'm here with you."*

---

### `main.py` — FeedbackSystem (Public API)

The top-level class that external systems (the mobile app) interact with.

#### `process_emotion_with_gps(emotion, latitude, longitude, timestamp)` ← **Primary Method**
For real mobile app use. Accepts a GPS point and auto-builds context.

```python
system = FeedbackSystem()
response = system.process_emotion_with_gps("stressed", 6.9271, 79.8612)
if response:
    print(response.message)  # Show to user
```

#### `process_emotion_detection(emotion, context, timestamp)` ← For Testing
For when context is built manually (simulation/testing).

#### Internal Flow
```
process_emotion_with_gps()
    → ContextService.build_context()           # enrich GPS
    → ContextEngine.update_emotion()           # update state
    → ContextEngine.evaluate_feedback_trigger()# should we?
    → ContextEngine.get_prompt_context()       # what to say about?
    → LLMInference.generate_feedback()         # generate message
    → ContextEngine.mark_feedback_generated()  # update timestamp
    → return FeedbackResponse or None
```

---

### `simulation.py` — Test Scenarios

A standalone script that simulates sequences of emotion detections over simulated time (no real Ollama needed for state testing, but needed for LLM output). Run it to verify the trigger logic works correctly:

```bash
python simulation.py
```

---

### Test Files

| File | Purpose |
|---|---|
| `test_context.py` | Tests for context building (location, time, weather) |
| `test_context_service.py` | Unit tests for `ContextService` |
| `test_llm_service.py` | Tests for LLM prompt construction and response parsing |
| `test_llm_responses.py` | End-to-end LLM response tests |
| `verify_install.py` | Checks all Python dependencies are installed |
| `verify_ollama.py` | Checks Ollama is running and Phi-3 is available |

---

## System Constraints & Design Principles

| Constraint | Reason |
|---|---|
| **Not a chatbot** | No conversation history, no multi-turn dialogue |
| **Not diagnostic** | Explicitly forbidden in system prompt |
| **Bounded memory (2 emotions max)** | Privacy-safe, prevents long-term profiling |
| **Time-aware context** | Previous emotion ignored if transition was > `T_RECENT` ago |
| **Fatigue prevention** | `FEEDBACK_INTERVAL` ensures the system doesn't spam the user |
| **Local LLM (Phi-3)** | No data sent to external servers, runs fully offline |

---

## Environment Variables (`.env`)

```env
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
```

Get a free key at: https://openweathermap.org/api

---

## Quick Integration Reference

```python
from main import FeedbackSystem

system = FeedbackSystem()  # Initialize once

# On each emotion detection (from mobile app):
response = system.process_emotion_with_gps(
    emotion="sad",
    latitude=6.9271,
    longitude=79.8612
)

if response:
    # response.message → show to user
    # response.timestamp → when it was generated
    # response.emotion_context → for logging
    display_to_user(response.message)
# If None → no feedback this cycle (cooldown or no trigger)
```

"""
RAG (Retrieval-Augmented Generation) Service.

Assembles a knowledge-grounded system prompt from rag_docs_v2 based on:
  1. Always: 00_system_guardrails.txt  (hardcoded, never retrieved by similarity)
  2. Emotion: one of 10_emotion_*.txt   (direct lookup by emotion label)
  3. Context: relevant sections from 20_context_*.txt files
              (time of day, weather, location, day type)

The user prompt template in llm_service.py is NOT touched by this service.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

import config


# ---------------------------------------------------------------------------
# Emotion label → file mapping
# ---------------------------------------------------------------------------
_EMOTION_FILE_MAP: Dict[str, str] = {
    # ── Canonical labels (used internally) ──────────────────────
    "sad":        "10_emotion_sad.txt",
    "anger":      "11_emotion_anger.txt",
    "angry":      "11_emotion_anger.txt",
    "neutral":    "12_emotion_neutral.txt",
    "happy":      "13_emotion_happy.txt",

    # ── Inference handler output labels ──────────────────────────
    # The RunPod EEG inference handler outputs these exact strings.
    # Map them to the correct RAG document.
    "sadness":    "10_emotion_sad.txt",    # handler "sadness"    → sad guide
    "fear":       "11_emotion_anger.txt",  # handler "fear"       → anger/fear guide
    "enthusiasm": "13_emotion_happy.txt",  # handler "enthusiasm" → happy guide
}


# Context file names
_CONTEXT_FILES = {
    "time":     "20_context_time_of_day.txt",
    "weather":  "21_context_weather.txt",
    "location": "22_context_location.txt",
    "day_type": "23_context_day_type.txt",
}

# ---------------------------------------------------------------------------
# Section headers inside each context file that map to runtime values
# ---------------------------------------------------------------------------
_TIME_SECTION_MAP: Dict[str, str] = {
    "morning":   "MORNING",
    "midday":    "MIDDAY",
    "afternoon": "MIDDAY / AFTERNOON",
    "evening":   "EVENING",
    "night":     "NIGHT",
}

_WEATHER_SECTION_MAP: Dict[str, str] = {
    "clear":        "CLEAR / SUNNY",
    "sunny":        "CLEAR / SUNNY",
    "clouds":       "CLOUDY",
    "cloudy":       "CLOUDY",
    "rain":         "RAIN",
    "drizzle":      "RAIN",
    "thunderstorm": "THUNDERSTORM / STORM",
    "storm":        "THUNDERSTORM / STORM",
    "hot":          "HOT",
    "cold":         "COLD",
    "unknown":      "UNKNOWN WEATHER",
}

_LOCATION_SECTION_MAP: Dict[str, str] = {
    "home":        "HOME",
    "work":        "WORK / UNIVERSITY / STUDY PLACE",
    "university":  "WORK / UNIVERSITY / STUDY PLACE",
    "study":       "WORK / UNIVERSITY / STUDY PLACE",
    "office":      "WORK / UNIVERSITY / STUDY PLACE",
    "commuting":   "COMMUTING / OUTSIDE / PUBLIC SPACE",
    "outside":     "COMMUTING / OUTSIDE / PUBLIC SPACE",
    "public":      "COMMUTING / OUTSIDE / PUBLIC SPACE",
    "park":        "PARK / NATURE / OUTDOOR GREEN SPACE",
    "nature":      "PARK / NATURE / OUTDOOR GREEN SPACE",
    "unknown":     "UNKNOWN LOCATION",
}

_DAY_SECTION_MAP: Dict[bool, str] = {
    True:  "WEEKDAY",
    False: "WEEKEND",
}


class RAGService:
    """
    Retrieves and assembles knowledge-base content into a system prompt.

    Usage:
        rag = RAGService()
        system_prompt = rag.build_system_prompt(
            emotion="sad",
            location="home",
            time_of_day="2026-03-25 08:30:00",
            weather="rain",
            is_weekday=True
        )
    """

    def __init__(self, docs_dir: Optional[str] = None):
        """
        Args:
            docs_dir: Path to rag_docs_v2 folder. Defaults to config.RAG_DOCS_DIR.
        """
        self.docs_dir = docs_dir or config.RAG_DOCS_DIR
        # Load & cache all doc files once at startup
        self._cache: Dict[str, str] = {}
        self._load_all_docs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_system_prompt(
        self,
        emotion: str,
        location: str,
        time_of_day: str,
        weather: str,
        is_weekday: bool,
    ) -> str:
        """
        Build the full system prompt for the LLM.

        Args:
            emotion:     Detected emotion label (e.g. "sad", "happy").
            location:    Semantic location string from ContextService
                         (e.g. "Mount Lavinia, Colombo, Sri Lanka").
            time_of_day: Formatted timestamp string from ContextService
                         (e.g. "2026-03-25 08:30:00").
            weather:     Weather condition from ContextService
                         (e.g. "rain", "clear", "clouds").
            is_weekday:  True if today is a weekday.

        Returns:
            Complete system prompt string with all retrieved content.
        """
        parts = []
        loaded = []   # track what was loaded for the log line

        # 1. Always-present guardrails
        guardrails = self._get_file("00_system_guardrails.txt")
        if guardrails:
            parts.append("=== SYSTEM GUIDELINES ===")
            parts.append(guardrails.strip())
            loaded.append("guardrails")

        # 2. Emotion-specific guide
        emotion_content = self._get_emotion_doc(emotion)
        if emotion_content:
            parts.append(f"\n=== GUIDANCE FOR EMOTION: {emotion.upper()} ===")
            parts.append(emotion_content.strip())
            loaded.append(f"emotion:{emotion}")
        else:
            print(f"[RAG] WARNING: no emotion doc for '{emotion}'")

        # 3. Context-specific guidance
        time_section = self._get_time_section(time_of_day)
        if time_section:
            parts.append("\n=== TIME OF DAY CONTEXT ===")
            parts.append(time_section.strip())
            loaded.append(f"time:{time_of_day[:10]}")

        weather_section = self._get_weather_section(weather)
        if weather_section:
            parts.append("\n=== WEATHER CONTEXT ===")
            parts.append(weather_section.strip())
            loaded.append(f"weather:{weather}")
        else:
            print(f"[RAG] WARNING: no weather section for '{weather}'")

        location_section = self._get_location_section(location)
        if location_section:
            parts.append("\n=== LOCATION CONTEXT ===")
            parts.append(location_section.strip())
            loaded.append(f"location:{location}")
        else:
            print(f"[RAG] WARNING: no location section for '{location}'")

        day_section = self._get_day_section(is_weekday)
        if day_section:
            parts.append("\n=== DAY TYPE CONTEXT ===")
            parts.append(day_section.strip())
            loaded.append("weekday" if is_weekday else "weekend")

        prompt = "\n\n".join(parts)
        print(f"[RAG] Built system prompt ({len(prompt)} chars) | sections: {', '.join(loaded)}")
        return prompt

    # ------------------------------------------------------------------
    # Internal helpers — document loading
    # ------------------------------------------------------------------

    def _load_all_docs(self):
        """Load all .txt files from docs_dir into the cache."""
        if not os.path.isdir(self.docs_dir):
            print(f"[RAGService] WARNING: docs_dir not found: {self.docs_dir}")
            return

        for filename in os.listdir(self.docs_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.docs_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._cache[filename] = f.read()
                except Exception as e:
                    print(f"[RAGService] WARNING: Could not read {filename}: {e}")

    def _get_file(self, filename: str) -> str:
        """Return cached file content, or empty string if missing."""
        return self._cache.get(filename, "")

    # ------------------------------------------------------------------
    # Internal helpers — retrieval logic
    # ------------------------------------------------------------------

    def _get_emotion_doc(self, emotion: str) -> str:
        """Return the full emotion guide for the given emotion label."""
        emotion_lower = emotion.lower().strip()
        filename = _EMOTION_FILE_MAP.get(emotion_lower, "")
        if not filename:
            print(f"[RAGService] Unknown emotion label: '{emotion}'. Skipping emotion doc.")
            return ""
        return self._get_file(filename)

    def _get_time_section(self, time_of_day: str) -> str:
        """Extract the relevant time-of-day section from the context doc."""
        try:
            # Parse the timestamp string: "2026-03-25 08:30:00"
            dt = datetime.strptime(time_of_day, "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
        except Exception:
            return self._extract_section("20_context_time_of_day.txt", "MORNING")

        if 5 <= hour < 12:
            key = "morning"
        elif 12 <= hour < 17:
            key = "afternoon"
        elif 17 <= hour < 21:
            key = "evening"
        else:
            key = "night"

        section_header = _TIME_SECTION_MAP.get(key, "MORNING")
        return self._extract_section("20_context_time_of_day.txt", section_header)

    def _get_weather_section(self, weather: str) -> str:
        """Extract the relevant weather section from the context doc."""
        weather_lower = weather.lower().strip()
        section_header = _WEATHER_SECTION_MAP.get(weather_lower, "UNKNOWN WEATHER")
        return self._extract_section("21_context_weather.txt", section_header)

    def _get_location_section(self, location: str) -> str:
        """
        Extract the relevant location section from the context doc.

        Because location is a full address string (e.g. "Mount Lavinia, Colombo"),
        we do a keyword scan to find the best matching section.
        """
        location_lower = location.lower()
        for keyword, header in _LOCATION_SECTION_MAP.items():
            if keyword in location_lower:
                return self._extract_section("22_context_location.txt", header)
        
        # Default: unknown location. 
        return self._extract_section("22_context_location.txt", "UNKNOWN LOCATION")

    def _get_day_section(self, is_weekday: bool) -> str:
        """Extract the relevant weekday/weekend section from the context doc."""
        section_header = _DAY_SECTION_MAP.get(is_weekday, "WEEKDAY")
        return self._extract_section("23_context_day_type.txt", section_header)

    def _extract_section(self, filename: str, section_header: str) -> str:
        """
        Extract a named section from a context file.

        Sections are delimited by an ALL-CAPS header line.
        The extraction reads from that header until the next header or end-of-file.

        Args:
            filename:       The filename in docs_dir (e.g. "20_context_time_of_day.txt").
            section_header: The exact header string to look for (e.g. "MORNING").

        Returns:
            The section text including the header, or empty string if not found.
        """
        content = self._get_file(filename)
        if not content:
            return ""

        lines = content.splitlines()
        result_lines = []
        inside = False

        for line in lines:
            stripped = line.strip()

            # Check if this line IS the target section header
            if stripped == section_header:
                inside = True
                result_lines.append(line)
                continue

            if inside:
                # Stop if we hit another ALL-CAPS section header (different section)
                if stripped and stripped == stripped.upper() and len(stripped) > 2 and stripped != section_header:
                    break
                result_lines.append(line)

        return "\n".join(result_lines)

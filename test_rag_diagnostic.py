"""
RAG Diagnostic Test — run this to verify every part of the RAG pipeline.
"""
import sys
sys.path.insert(0, '.')
from rag_service import RAGService

rag = RAGService()

# Test 1: Guardrails
print("=== TEST 1: Guardrails ===")
g = rag._get_file("00_system_guardrails.txt")
print(f"  Loaded: {len(g)} chars" if g else "  FAILED: empty")

# Test 2: Emotion docs for all labels the app sends
print("\n=== TEST 2: Emotion docs ===")
for label in ["neutral", "sadness", "enthusiasm", "fear", "sad", "happy", "anger"]:
    result = rag._get_emotion_doc(label)
    status = f"{len(result)} chars" if result else "MISSING !!!"
    print(f"  {label:<14} -> {status}")

# Test 3: Time sections
print("\n=== TEST 3: Time sections ===")
for ts in ["2026-04-29 06:00:00", "2026-04-29 13:00:00", "2026-04-29 19:00:00", "2026-04-29 23:00:00"]:
    result = rag._get_time_section(ts)
    status = f"{len(result)} chars" if result else "EMPTY !!!"
    print(f"  {ts} -> {status}")

# Test 4: Weather sections
print("\n=== TEST 4: Weather sections ===")
for w in ["clear", "rain", "clouds", "unknown"]:
    result = rag._get_weather_section(w)
    status = f"{len(result)} chars" if result else "EMPTY !!!"
    print(f"  {w:<12} -> {status}")

# Test 5: Location sections (realistic GPS reverse-geocoded strings)
print("\n=== TEST 5: Location sections ===")
for loc in ["home", "Mount Lavinia, Colombo", "Colombo", "unknown location", "work", "university"]:
    result = rag._get_location_section(loc)
    status = f"{len(result)} chars" if result else "EMPTY !!!"
    print(f"  {loc:<30} -> {status}")

# Test 6: Full build_system_prompt
print("\n=== TEST 6: Full prompt build ===")
prompt = rag.build_system_prompt(
    emotion="sad",
    location="Mount Lavinia, Colombo, Sri Lanka",
    time_of_day="2026-04-29 08:00:00",
    weather="clear",
    is_weekday=True
)
print(f"  Total length : {len(prompt)} chars")
print(f"  Has guardrails : {'=== SYSTEM GUIDELINES ===' in prompt}")
print(f"  Has emotion    : {'=== GUIDANCE FOR EMOTION' in prompt}")
print(f"  Has time       : {'=== TIME OF DAY' in prompt}")
print(f"  Has weather    : {'=== WEATHER CONTEXT ===' in prompt}")
print(f"  Has location   : {'=== LOCATION CONTEXT ===' in prompt}")
print(f"  Has day type   : {'=== DAY TYPE CONTEXT ===' in prompt}")

# Test 7: Check the location section extraction in detail
print("\n=== TEST 7: Location section extraction detail ===")
loc_test = "Mount Lavinia, Colombo, Sri Lanka"
loc_lower = loc_test.lower()
from rag_service import _LOCATION_SECTION_MAP
matched_keyword = None
for keyword in _LOCATION_SECTION_MAP:
    if keyword in loc_lower:
        matched_keyword = keyword
        break
print(f"  Input: '{loc_test}'")
print(f"  Matched keyword: '{matched_keyword}'")
print(f"  -> Falls back to: UNKNOWN LOCATION" if not matched_keyword else f"  -> Section: {_LOCATION_SECTION_MAP[matched_keyword]}")

# Test 8: Guardrails section parsing bug check
print("\n=== TEST 8: Guardrails ALL-CAPS header bug check ===")
# The _extract_section stops reading when it hits an ALL-CAPS line.
# The guardrails file has ALL-CAPS headers. Make sure _get_file returns full content.
g_content = rag._get_file("00_system_guardrails.txt")
lines = g_content.splitlines()
caps_lines = [l.strip() for l in lines if l.strip() == l.strip().upper() and len(l.strip()) > 2]
print(f"  ALL-CAPS lines in guardrails: {caps_lines}")
print(f"  (These are fine — guardrails uses _get_file, not _extract_section)")

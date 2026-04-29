import sys
sys.path.insert(0, '.')
from rag_service import RAGService, _LOCATION_SECTION_MAP
from context_service import ContextService
from datetime import datetime

rag = RAGService()
cs = ContextService()

now = datetime.now()
print(f'Current datetime: {now}')
time_str = now.strftime('%Y-%m-%d %H:%M:%S')
section = rag._get_time_section(time_str)
print(f'Time section returned: {repr(section[:80]) if section else "EMPTY!"}')

print()
print('=== Testing context_service.build_context (GPS mode - Colombo, Sri Lanka) ===')
ctx = cs.build_context(6.9271, 79.8612)
print(f'location:   "{ctx.location}"')
print(f'time_of_day: "{ctx.time_of_day}"')
print(f'weather:    "{ctx.weather}"')
print(f'weekday:    {ctx.weekday}')

print()
print('=== Location keyword scan ===')
location_lower = ctx.location.lower()
matched = None
for keyword, header in _LOCATION_SECTION_MAP.items():
    if keyword in location_lower:
        matched = (keyword, header)
        break
print(f'Match result: {matched if matched else "NO MATCH - falls back to UNKNOWN LOCATION"}')

print()
print('=== Full RAG system prompt sections ===')
sp = rag.build_system_prompt('sad', ctx.location, ctx.time_of_day, ctx.weather, ctx.weekday)
for line in sp.split('\n'):
    if line.startswith('==='):
        print(' ', line)

print()
print('=== Weather section test ===')
weather_section = rag._get_weather_section(ctx.weather)
print(f'Weather "{ctx.weather}" → section: {repr(weather_section[:100]) if weather_section else "EMPTY!"}')

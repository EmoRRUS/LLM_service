
import sys
import traceback

try:
    from context_service import ContextService
    
    with open("context_test_result.txt", "w") as f:
        f.write("Initializing ContextService...\n")
        service = ContextService()
        
        f.write("Building context for Colombo (6.9271, 79.8612)...\n")
        context = service.build_context(
            latitude=6.9271,
            longitude=79.8612
        )
        
        f.write("\nSUCCESS: Context Built!\n")
        f.write(f"Address: {context.location}\n")
        f.write(f"Timestamp: {context.time_of_day}\n")
        f.write(f"Weekday: {context.weekday}\n")
        f.write(f"Weather: {context.weather}\n")
        f.write(f"GPS: ({context.latitude}, {context.longitude})\n")

except Exception as e:
    with open("context_test_result.txt", "w") as f:
        f.write(f"\nFAILURE: {e}\n")
        traceback.print_exc(file=f)

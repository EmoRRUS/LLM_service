"""
Test script to verify LLM responses across different scenarios.
This bypasses the logic layer and directly tests the LLM Service.
"""
from datetime import datetime
from llm_service import LLMInference
from models import ContextData

def test_llm_responses():
    print("=" * 80)
    print("LLM RESPONSE QUALITY TEST")
    print("=" * 80)
    
    # Initialize LLM
    llm = LLMInference()
    
    # Define test scenarios
    scenarios = [
        {
            "name": "Stressed at Work (Rainy)",
            "emotion_context": {
                "current_emotion": "stressed",
                "duration_minutes": 15,
                "include_previous": True,
                "previous_emotion": "neutral",
                "minutes_since_change": 15
            },
            "context": ContextData(
                location="Office Building, Colombo 03, Sri Lanka",
                time_of_day="2026-01-23 09:30:00",
                weekday=True,
                weather="rainy"
            )
        },
        {
            "name": "Happy at Home (Sunny Weekend)",
            "emotion_context": {
                "current_emotion": "happy",
                "duration_minutes": 20,
                "include_previous": False
            },
            "context": ContextData(
                location="123 Lotus Road, Colombo, Sri Lanka",
                time_of_day="2026-01-23 14:00:00",
                weekday=False,
                weather="clear"
            )
        },
        {
            "name": "Sad at Night (Stormy)",
            "emotion_context": {
                "current_emotion": "sad",
                "duration_minutes": 30,
                "include_previous": True,
                "previous_emotion": "happy",
                "minutes_since_change": 30
            },
            "context": ContextData(
                location="Mount Lavinia Beach, Colombo, Sri Lanka",
                time_of_day="2026-01-23 22:00:00",
                weekday=True,
                weather="thunderstorm"
            )
        },
        {
            "name": "Anxious in Public Transport",
            "emotion_context": {
                "current_emotion": "anxious",
                "duration_minutes": 10,
                "include_previous": True,
                "previous_emotion": "neutral",
                "minutes_since_change": 10
            },
            "context": ContextData(
                location="Colombo Fort Railway Station, Sri Lanka",
                time_of_day="2026-01-23 08:00:00",
                weekday=True,
                weather="clouds"
            )
        },
        {
            "name": "Calm at Park (Clear Morning)",
            "emotion_context": {
                "current_emotion": "calm",
                "duration_minutes": 25,
                "include_previous": False
            },
            "context": ContextData(
                location="Viharamahadevi Park, Colombo, Sri Lanka",
                time_of_day="2026-01-23 07:00:00",
                weekday=False,
                weather="clear"
            )
        }
    ]
    
    # Test each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Scenario {i}] {scenario['name']}")
        print("-" * 80)
        print(f"Emotion: {scenario['emotion_context']['current_emotion']} "
              f"({scenario['emotion_context']['duration_minutes']} mins)")
        print(f"Location: {scenario['context'].location}")
        print(f"Weather: {scenario['context'].weather}")
        print(f"Time: {scenario['context'].time_of_day}")
        
        try:
            response = llm.generate_feedback(
                scenario['emotion_context'],
                scenario['context']
            )
            
            print(f"\n💬 LLM Response:")
            print(f"   \"{response.message}\"")
            print(f"\n✅ Generated successfully")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    print("\n🧪 Testing LLM Response Quality Across Scenarios\n")
    test_llm_responses()
    print("\n✅ All scenario tests complete!\n")

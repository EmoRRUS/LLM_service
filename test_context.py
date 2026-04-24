"""
Test script for automatic context detection from GPS coordinates.

This tests the context_service.py functionality:
- GPS coordinates → semantic location
- System time → time_of_day + weekday
- GPS coordinates → weather (from API)
"""
from context_service import ContextService
from main import FeedbackSystem
from datetime import datetime


def test_context_service():
    """Test automatic context detection from GPS."""
    print("=" * 80)
    print("TESTING AUTOMATIC CONTEXT DETECTION")
    print("=" * 80)
    
    service = ContextService()
    
    # Test different locations
    test_locations = [
        {
            "name": "Colombo, Sri Lanka",
            "latitude": 6.9271,
            "longitude": 79.8612
        },
        {
            "name": "New York, USA",
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        {
            "name": "London, UK",
            "latitude": 51.5074,
            "longitude": -0.1278
        }
    ]
    
    for loc in test_locations:
        print(f"\n📍 Testing: {loc['name']}")
        print(f"   GPS: ({loc['latitude']}, {loc['longitude']})")
        print("-" * 80)
        
        # Build context from GPS
        context = service.build_context(
            latitude=loc['latitude'],
            longitude=loc['longitude']
        )
        
        # Display results
        print(f"\n✅ Auto-detected context:")
        print(f"   Address:     {context.location}")
        print(f"   Timestamp:   {context.time_of_day}")
        print(f"   Weekday:     {context.weekday}")
        print(f"   Weather:     {context.weather}")
        print(f"   GPS:         ({context.latitude}, {context.longitude})")
        print("\n" + "=" * 80)


def test_full_pipeline_with_gps():
    """Test the complete pipeline using GPS-based context."""
    print("\n" + "=" * 80)
    print("TESTING FULL PIPELINE WITH GPS")
    print("=" * 80)
    
    system = FeedbackSystem()
    
    # Simulate emotion detections with GPS
    print("\n[Scenario 1] User in Colombo, feeling stressed")
    print("-" * 80)
    
    response = system.process_emotion_with_gps(
        emotion="stressed",
        latitude=6.9271,
        longitude=79.8612
    )
    
    if response:
        print(f"\n✅ FEEDBACK GENERATED:")
        print(f"   Message: \"{response.message}\"")
        print(f"   Context: {response.emotion_context}")
        print(f"   Time: {response.timestamp.strftime('%H:%M:%S')}")
    else:
        print("\n⏸️  No feedback generated")
    
    print("\n" + "=" * 80)
    
    # Test with different location
    print("\n[Scenario 2] User in New York, feeling happy")
    print("-" * 80)
    
    response = system.process_emotion_with_gps(
        emotion="happy",
        latitude=40.7128,
        longitude=-74.0060
    )
    
    if response:
        print(f"\n✅ FEEDBACK GENERATED:")
        print(f"   Message: \"{response.message}\"")
        print(f"   Context: {response.emotion_context}")
        print(f"   Time: {response.timestamp.strftime('%H:%M:%S')}")
    else:
        print("\n⏸️  No feedback generated")
    
    print("\n" + "=" * 80)

def test_weather_api():
    """Test weather API integration."""
    print("\n" + "=" * 80)
    print("TESTING WEATHER API")
    print("=" * 80)
    
    service = ContextService()
    
    # Test weather for Colombo
    print("\n🌤️  Fetching weather for Colombo...")
    weather = service.get_weather(6.9271, 79.8612)
    print(f"   Weather: {weather}")
    
    if weather == "unknown":
        print("\n⚠️  Note: Weather API key not configured")
        print("   To enable weather detection:")
        print("   1. Get API key from: https://openweathermap.org/api")
        print("   2. Add to .env: OPENWEATHER_API_KEY=your_key")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🧪 AUTOMATIC CONTEXT DETECTION TESTS\n")
    
    # Test 1: Context service
    #test_context_service()
    
    # Test 2: Weather API
    test_weather_api()
    
    # Test 4: Full pipeline
    #test_full_pipeline_with_gps()
    
    print("\n✅ All tests complete!\n")

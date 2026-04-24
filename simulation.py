"""
Simulation script to verify the Bounded Emotion Memory system.

UPDATED: Tests new 10-minute periodic feedback logic.

This script simulates a sequence of emotion detections over time and verifies:
1. Bounded memory updates correctly
2. Previous emotion temporal relevance
3. NEW: Feedback every 10 minutes (not cooldown-based)
4. LLM integration with weather context
"""
from datetime import datetime, timedelta
from logic import ContextEngine
from llm_service import LLMInference
from models import ContextData
import config


def simulate_scenario():
    """
    Run a comprehensive simulation scenario using real GPS context.
    
    NEW Timeline (10-minute periodic feedback):
    T=0:    neutral (first detection) -> No feedback (system start)
    T=5:    neutral (same) -> No feedback
    T=10:   anger (change) -> FEEDBACK (emotion change)
    T=15:   anger (same) -> No feedback (only 5m since last)
    T=20:   anger (same, 10m since last) -> FEEDBACK (periodic)
    T=25:   anger (same) -> No feedback
    T=30:   anger (same, 10m since last) -> FEEDBACK (periodic)
    T=35:   happy (change) -> FEEDBACK (emotion change)
    T=40:   happy (same) -> No feedback (only 5m since last)
    T=45:   happy (same, 10m since last) -> FEEDBACK (periodic)
    """
    
    print("=" * 80)
    print("BOUNDED EMOTION MEMORY SYSTEM - SIMULATION WITH GPS CONTEXT")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  T_recent: {config.T_RECENT} minutes")
    print(f"  Feedback interval: {config.FEEDBACK_INTERVAL} minutes")
    print(f"  Check interval: {config.EMOTION_CHECK_INTERVAL} minutes")
    print("\n" + "=" * 80 + "\n")
    
    from main import FeedbackSystem
    
    # Initialize the top-level FeedbackSystem instead of just the pieces,
    # as it natively handles GPS -> Context -> LLM flow.
    system = FeedbackSystem()
    
    # Define a set of GPS coordinates around Colombo to test different locations
    colombo_gps = {
        "home_area": (6.8375, 79.8732),        # Mount Lavinia area
        "park_area": (6.9113, 79.8601),        # Viharamahadevi Park area
        "work_area": (6.9271, 79.8612)         # Colombo center area
    }
    
    # Define simulation timeline
    base_time = datetime.now()
    
    # Using only strictly supported RAG emotions: neutral, anger, happy, sad
    scenarios = [
        (0,  "neutral", colombo_gps["home_area"]),
        (5,  "neutral", colombo_gps["home_area"]),
        (10, "anger",   colombo_gps["work_area"]),
        (15, "anger",   colombo_gps["work_area"]),
        (20, "anger",   colombo_gps["work_area"]),
        (25, "anger",   colombo_gps["work_area"]),
        (30, "anger",   colombo_gps["work_area"]),
        (35, "happy",   colombo_gps["park_area"]),
        (40, "happy",   colombo_gps["park_area"]),
        (45, "happy",   colombo_gps["park_area"]),
    ]
    
    for minutes_offset, emotion, gps in scenarios:
        current_time = base_time + timedelta(minutes=minutes_offset)
        lat, lon = gps
        
        print(f"[T+{minutes_offset:3d}m] Emotion detected: {emotion.upper()} near GPS [{lat}, {lon}]")
        print("-" * 80)
        
        # Build context just for logging purposes here, process_emotion_with_gps handles logging it internally usually
        context = system.context_service.build_context(lat, lon, current_time)
        print(f"  Auto-Context: {context.location} | {context.time_of_day} | Weather: {context.weather}")
        
        # Process through main.py workflow
        response = system.process_emotion_with_gps(
            emotion=emotion,
            latitude=lat,
            longitude=lon,
            timestamp=current_time
        )
        
        print(f"  {system.get_current_state()}")
        
        if response is not None:
            trigger_reason = system.engine.evaluate_feedback_trigger(current_time) # Just evaluating again to print reason
            print(f"\n  ✅ FEEDBACK GENERATED:")
            print(f"     \"{response.message}\"")
        else:
            print(f"  ⏸️  No feedback necessary currently")
            
        print("\n" + "=" * 80 + "\n")


def test_temporal_relevance():
    """
    Test that previous emotion is ignored when too old.
    """
    print("\n" + "=" * 80)
    print("TEST: TEMPORAL RELEVANCE OF PREVIOUS EMOTION")
    print("=" * 80 + "\n")
    
    engine = ContextEngine()
    base_time = datetime.now()
    
    # T=0: Happy
    engine.update_emotion("happy", base_time)
    print(f"[T+0] Emotion: happy")
    
    # T=5: Stressed (change)
    engine.update_emotion("stressed", base_time + timedelta(minutes=5))
    print(f"[T+5] Emotion: stressed (changed from happy)")
    
    # T=10: Check context (previous should be included)
    context_t10 = engine.get_prompt_context(base_time + timedelta(minutes=10))
    print(f"\n[T+10] Context check:")
    print(f"  Include previous: {context_t10.get('include_previous')}")
    if context_t10.get('include_previous'):
        print(f"  ✅ Previous emotion IS included (5m < T_recent={config.T_RECENT}m)")
    
    # T=20: Check context (previous should still be included if T_recent >= 15)
    context_t20 = engine.get_prompt_context(base_time + timedelta(minutes=20))
    print(f"\n[T+20] Context check:")
    print(f"  Include previous: {context_t20.get('include_previous')}")
    if context_t20.get('include_previous'):
        print(f"  ✅ Previous emotion IS included (15m <= T_recent={config.T_RECENT}m)")
    else:
        print(f"  ✅ Previous emotion NOT included (15m > T_recent={config.T_RECENT}m)")
    
    print("\n" + "=" * 80 + "\n")


def test_periodic_feedback():
    """
    Test that feedback is generated every 10 minutes.
    """
    print("\n" + "=" * 80)
    print("TEST: 10-MINUTE PERIODIC FEEDBACK")
    print("=" * 80 + "\n")
    
    engine = ContextEngine()
    base_time = datetime.now()
    
    # T=0: Stressed (first)
    engine.update_emotion("stressed", base_time)
    trigger_t0 = engine.evaluate_feedback_trigger(base_time)
    print(f"[T+0] Stressed detected: Trigger = {trigger_t0.should_generate} ({trigger_t0.reason})")
    if trigger_t0.should_generate:
        engine.mark_feedback_generated(base_time)
    
    # T=5: Still stressed
    trigger_t5 = engine.evaluate_feedback_trigger(base_time + timedelta(minutes=5))
    print(f"[T+5] Still stressed: Trigger = {trigger_t5.should_generate} ({trigger_t5.reason})")
    
    # T=10: Still stressed (should trigger - 10m since last)
    trigger_t10 = engine.evaluate_feedback_trigger(base_time + timedelta(minutes=10))
    print(f"[T+10] Still stressed: Trigger = {trigger_t10.should_generate} ({trigger_t10.reason})")
    if trigger_t10.should_generate:
        print("  ✅ Periodic feedback triggered at 10 minutes!")
        engine.mark_feedback_generated(base_time + timedelta(minutes=10))
    
    # T=15: Still stressed
    trigger_t15 = engine.evaluate_feedback_trigger(base_time + timedelta(minutes=15))
    print(f"[T+15] Still stressed: Trigger = {trigger_t15.should_generate} ({trigger_t15.reason})")
    
    # T=20: Still stressed (should trigger - 10m since last)
    trigger_t20 = engine.evaluate_feedback_trigger(base_time + timedelta(minutes=20))
    print(f"[T+20] Still stressed: Trigger = {trigger_t20.should_generate} ({trigger_t20.reason})")
    if trigger_t20.should_generate:
        print("  ✅ Periodic feedback triggered at 20 minutes!")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    # Run temporal relevance test first
    #test_temporal_relevance()
    
    # Run periodic feedback test
    #test_periodic_feedback()
    
    # Run full simulation
    simulate_scenario()
    
    print("\n✅ Simulation complete!")

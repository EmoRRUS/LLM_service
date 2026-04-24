"""
Main entry point for the Bounded Emotion Memory System.

This module provides a clean API for integration with mobile apps or other services.
"""
from datetime import datetime
from typing import Optional
from logic import ContextEngine
from llm_service import LLMInference
from context_service import ContextService
from models import ContextData, FeedbackResponse


class FeedbackSystem:
    """
    Main system interface for emotion-based feedback generation.
    
    This is the primary class that external systems (e.g., mobile apps) should interact with.
    """
    
    def __init__(self):
        """Initialize the feedback system."""
        self.engine = ContextEngine()
        self.llm = LLMInference()
        self.context_service = ContextService()
    
    #for testing
    def process_emotion_detection(
        self,
        emotion: str,
        context: ContextData,
        timestamp: Optional[datetime] = None
    ) -> Optional[FeedbackResponse]:
        """
        Process a new emotion detection event.
        
        This is the main method called by external systems when a new emotion is detected.
        
        Args:
            emotion: The detected emotion label (e.g., "happy", "stressed", "sad")
            context: Current context information
            timestamp: Time of detection (defaults to now)
            
        Returns:
            FeedbackResponse if feedback was generated, None otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Update emotion state
        self.engine.update_emotion(emotion, timestamp)
        
        # Evaluate if feedback should be generated
        trigger = self.engine.evaluate_feedback_trigger(timestamp)
        
        if not trigger.should_generate:
            return None
        
        # Get prompt context
        prompt_context = self.engine.get_prompt_context(timestamp)
        
        # Generate feedback
        response = self.llm.generate_feedback(prompt_context, context)
        
        # Mark feedback as generated
        self.engine.mark_feedback_generated(timestamp)
        
        return response
    
    #for use with app.
    def process_emotion_with_gps(
        self,
        emotion: str,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> Optional[FeedbackResponse]:
        """
        Process emotion detection with automatic context from GPS.
        
        This is the recommended method for mobile app integration.
        The mobile app just sends GPS coordinates, and this service
        automatically detects location, time, and weather.
        
        Args:
            emotion: The detected emotion label
            latitude: GPS latitude from device
            longitude: GPS longitude from device
            timestamp: Time of detection (defaults to now)
            
        Returns:
            FeedbackResponse if feedback was generated, None otherwise
        """
        # Auto-build context from GPS
        context = self.context_service.build_context(latitude, longitude, timestamp)
        
        # Process with the built context
        return self.process_emotion_detection(emotion, context, timestamp)
    
    def get_current_state(self) -> str:
        """Get human-readable current state (for debugging/monitoring)."""
        return self.engine.get_state_summary()


# Example usage
if __name__ == "__main__":
    print("Bounded Emotion Memory System - Main Module")
    print("=" * 80)
    print("\nThis module provides the FeedbackSystem class for integration.")
    print("\nFor testing, run: python simulation.py")
    print("\nExample usage:")
    print("""
    from main import FeedbackSystem
    from models import ContextData
    
    # Initialize system
    system = FeedbackSystem()
    
    # Process emotion detection
    context = ContextData(
        location="home",
        time_of_day="evening",
        weekday=True
    )
    
    response = system.process_emotion_detection("stressed", context)
    
    if response:
        print(f"Feedback: {response.message}")
    else:
        print("No feedback generated")
    """)

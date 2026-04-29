"""
Data models for the Bounded Emotion Memory System.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field



class ContextData(BaseModel):
    """Context information from sensors/device."""
    location: str = Field(..., description="Full address: street, city, country")
    semantic_location: str = Field("unknown", description="Semantic location mapping (e.g. home, park) for RAG")
    time_of_day: str = Field(..., description="Formatted timestamp string")
    weekday: bool = Field(..., description="True if weekday, False if weekend")
    weather: str = Field(..., description="Weather condition: sunny, cloudy, rainy, etc.")
    
    # Optional: Raw GPS coordinates (for debugging/logging)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EmotionState(BaseModel):
    """
    Bounded emotion memory - maintains ONLY current and previous emotion.
    This is the ONLY state that persists across emotion detections.
    """
    # Current emotion
    current_emotion: str
    current_emotion_start_time: datetime
    
    # Previous emotion (None at system start)
    previous_emotion: Optional[str] = None
    previous_emotion_end_time: Optional[datetime] = None
    
    # Feedback tracking
    last_feedback_time: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FeedbackTrigger(BaseModel):
    """Result of evaluating whether to generate feedback."""
    should_generate: bool
    reason: str  # "change", "persist", "cooldown", "no_trigger"
    
    
class FeedbackResponse(BaseModel):
    """Response from the LLM feedback generation."""
    message: str
    timestamp: datetime
    emotion_context: str  # For logging/debugging

"""
Core logic for Bounded Emotion Memory and Feedback Trigger evaluation.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from models import EmotionState, FeedbackTrigger
import config


class ContextEngine:
    """
    Manages the bounded emotion memory state machine.
    
    CRITICAL RULES:
    1. Maintains EXACTLY 2 emotions: current and previous
    2. previous_emotion and current_emotion must ALWAYS be different
    3. Memory updates ONLY on emotion change
    4. Previous emotion is relevant ONLY if time_since_change <= T_recent
    """
    
    def __init__(self):
        """Initialize with no state (will be set on first emotion detection)."""
        self.state: Optional[EmotionState] = None
    
    def update_emotion(self, new_emotion: str, timestamp: datetime) -> bool:
        """
        Update emotion state following strict transition rules.
        
        Args:
            new_emotion: The newly detected emotion label
            timestamp: Time of detection
            
        Returns:
            True if state changed, False otherwise
        """
        # First emotion detection (system start)
        if self.state is None:
            self.state = EmotionState(
                current_emotion=new_emotion,
                current_emotion_start_time=timestamp,
                previous_emotion=None,
                previous_emotion_end_time=None,
                last_feedback_time=None
            )
            return True
        
        # If emotion is the same, DO NOT update memory
        if new_emotion == self.state.current_emotion:
            return False
        
        # Emotion changed: update bounded memory
        self.state.previous_emotion = self.state.current_emotion
        self.state.previous_emotion_end_time = timestamp
        self.state.current_emotion = new_emotion
        self.state.current_emotion_start_time = timestamp
        
        return True
    
    def evaluate_feedback_trigger(self, timestamp: datetime) -> FeedbackTrigger:
        """
        Evaluate whether feedback should be generated.
        
        NEW LOGIC (Updated):
        1. Emotion just changed → FEEDBACK
        2. Emotion persists for 10, 20, 30... minutes → FEEDBACK
        
        Args:
            timestamp: Current time
            
        Returns:
            FeedbackTrigger with decision and reason
        """
        if self.state is None:
            return FeedbackTrigger(should_generate=False, reason="no_state")
        
        # Calculate current emotion duration
        emotion_duration = (timestamp - self.state.current_emotion_start_time).total_seconds() / 60
        
        # Trigger 1: Emotion just changed (duration is very small)
        # We consider it a "change" if duration < check interval
        if emotion_duration < config.EMOTION_CHECK_INTERVAL:
            return FeedbackTrigger(should_generate=True, reason="emotion_change")
        
        # Trigger 2: Periodic feedback every FEEDBACK_INTERVAL minutes
        # Check if we're at a 10-minute mark (10, 20, 30, etc.)
        if self.state.last_feedback_time is not None:
            time_since_last_feedback = (timestamp - self.state.last_feedback_time).total_seconds() / 60
            
            # Generate feedback if it's been >= FEEDBACK_INTERVAL since last feedback
            if time_since_last_feedback >= config.FEEDBACK_INTERVAL:
                return FeedbackTrigger(should_generate=True, reason=f"periodic ({time_since_last_feedback:.1f}m)")
        else:
            # No feedback yet, check if emotion has persisted for FEEDBACK_INTERVAL
            if emotion_duration >= config.FEEDBACK_INTERVAL:
                return FeedbackTrigger(should_generate=True, reason=f"periodic ({emotion_duration:.1f}m)")
        
        return FeedbackTrigger(should_generate=False, reason="no_trigger")
    
    def get_prompt_context(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Extract context for LLM prompt construction.
        
        CRITICAL: Previous emotion is included ONLY if time_since_change <= T_recent
        
        Args:
            timestamp: Current time
            
        Returns:
            Dictionary with prompt context
        """
        if self.state is None:
            return {}
        
        emotion_duration = (timestamp - self.state.current_emotion_start_time).total_seconds() / 60
        
        context = {
            "current_emotion": self.state.current_emotion,
            "duration_minutes": round(emotion_duration, 1),
            "include_previous": False
        }
        
        # Check if previous emotion is temporally relevant
        if self.state.previous_emotion is not None and self.state.previous_emotion_end_time is not None:
            time_since_change = (timestamp - self.state.previous_emotion_end_time).total_seconds() / 60
            
            if time_since_change <= config.T_RECENT:
                context["include_previous"] = True
                context["previous_emotion"] = self.state.previous_emotion
                context["minutes_since_change"] = round(time_since_change, 1)
        
        return context
    
    def mark_feedback_generated(self, timestamp: datetime):
        """Update last_feedback_time after generating feedback."""
        if self.state is not None:
            self.state.last_feedback_time = timestamp
    
    def get_state_summary(self) -> str:
        """Get human-readable state summary for logging."""
        if self.state is None:
            return "No state initialized"
        
        summary = f"Current: {self.state.current_emotion} (since {self.state.current_emotion_start_time.strftime('%H:%M')})"
        if self.state.previous_emotion:
            summary += f" | Previous: {self.state.previous_emotion}"
        if self.state.last_feedback_time:
            summary += f" | Last feedback: {self.state.last_feedback_time.strftime('%H:%M')}"
        return summary

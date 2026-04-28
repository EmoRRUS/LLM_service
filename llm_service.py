"""
LLM Feedback Generation Service using LangChain and Ollama (Phi-3).
"""
import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from models import FeedbackResponse, ContextData
from rag_service import RAGService
import config


# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)


class LLMInference:
    """
    LangChain-based wrapper for local Phi-3 feedback generation via Ollama.

    CRITICAL CONSTRAINTS:
    - NO medical/psychological advice
    - NO diagnosis
    - NO emotional dependency encouragement
    - Calm, supportive, non-judgmental tone
    - 1-3 sentences maximum
    - Plain text only (no emojis, no markdown)
    """

    def __init__(self):
        """Initialize LangChain components with Ollama and RAG service."""
        self.llm = ChatOllama(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            base_url=config.OLLAMA_BASE_URL,
            # Phi-3 is a small model, we guide it to be concise via prompt
        )

        # RAG service — loads all knowledge base docs once at startup
        self.rag = RAGService()

        # The user prompt template is NOT changed
        self.user_prompt_template = self._get_user_prompt_template()

    def _get_system_prompt(self, rag_content: str) -> str:
        """
        Build the system prompt from RAG-retrieved knowledge base content.

        Args:
            rag_content: Assembled system prompt text from RAGService.

        Returns:
            Full system prompt string.
        """
        return rag_content

    def _get_user_prompt_template(self) -> str:
        """Get the user prompt template."""
        return """User status:
- Emotion: {current_emotion} (for {duration_minutes} mins)
{previous_emotion_context}
- Location: {location}
- Time: {time_of_day}
- Weather: {weather}

Task: Write a short, supportive message for this user."""

    def generate_feedback(
        self,
        emotion_context: Dict[str, Any],
        context_data: ContextData
    ) -> FeedbackResponse:
        """
        Generate feedback using local Phi-3 model with RAG-enriched system prompt.

        Args:
            emotion_context: Output from ContextEngine.get_prompt_context()
            context_data: Current context information

        Returns:
            FeedbackResponse with the generated message
        """
        # --- RAG: retrieve and assemble system prompt from knowledge base ---
        rag_system_prompt = self.rag.build_system_prompt(
            emotion=emotion_context["current_emotion"],
            location=context_data.location,
            time_of_day=context_data.time_of_day,
            weather=context_data.weather,
            is_weekday=context_data.weekday,
        )

        # Build the prompt template with the RAG-enriched system prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt(rag_system_prompt)),
            ("user", self.user_prompt_template)
        ])

        # Create the chain with the current prompt
        chain = prompt_template | self.llm | StrOutputParser()

        # Build previous emotion context string
        previous_emotion_context = ""
        if emotion_context.get("include_previous", False):
            previous_emotion_context = f"- Previous emotion: {emotion_context['previous_emotion']} (changed {emotion_context['minutes_since_change']} mins ago)"

        # Prepare input for the chain
        chain_input = {
            "current_emotion": emotion_context["current_emotion"],
            "duration_minutes": emotion_context["duration_minutes"],
            "previous_emotion_context": previous_emotion_context,
            "location": context_data.location,
            "time_of_day": context_data.time_of_day,
            "day_type": "weekday" if context_data.weekday else "weekend",
            "weather": context_data.weather
        }



        # Invoke the chain
        try:
            message = chain.invoke(chain_input)

            # Clean up the message (remove any accidental formatting or quotes)
            message = message.strip().strip('"')

            # Create response
            return FeedbackResponse(
                message=message,
                timestamp=datetime.now(),
                emotion_context=f"{emotion_context['current_emotion']} ({emotion_context['duration_minutes']}m)"
            )
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return FeedbackResponse(
                message="Take a moment to breathe. I'm here with you.",
                timestamp=datetime.now(),
                emotion_context="error_fallback"
            )


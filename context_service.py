"""
Automatic Context Detection Service.

This service provides automatic detection of:
1. Location (from GPS coordinates → semantic label)
2. Time of day (from system time)
3. Weather (from weather API based on location)
4. Weekday (from system time)

The mobile app sends GPS coordinates, and this service handles the rest.
"""
import os
import requests
from datetime import datetime
from typing import Tuple, Optional
from dotenv import load_dotenv
from models import ContextData
import config


# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)


class ContextService:
    """
    Service for automatic context detection.
    
    Mobile app provides GPS coordinates, this service enriches with:
    - Semantic location label
    - Time of day
    - Weather
    - Weekday
    """
    
    def __init__(self):
        """Initialize the context service."""
        self.weather_api_key = os.getenv("OPENWEATHER_API_KEY", config.WEATHER_API_KEY)
    
    def get_time_context(self, timestamp: Optional[datetime] = None) -> Tuple[str, bool]:
        """
        Get time of day and weekday from timestamp.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Tuple of (time_of_day, is_weekday)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Return formatted date/time string and weekday status
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine if weekday (Monday=0, Sunday=6)
        is_weekday = timestamp.weekday() < 5
        
        return time_str, is_weekday
    
    def get_semantic_location(self, latitude: float, longitude: float) -> str:
        """
        Convert GPS coordinates to a RAG-compatible semantic location label.

        Uses Nominatim reverse geocoding to get the address, then derives a
        semantic category keyword (home / work / university / outside / unknown)
        that the RAG _get_location_section() keyword scanner can actually match.

        The raw display_name is intentionally NOT returned here because the RAG
        scanner looks for keywords like "home", "work", "university" — not street
        addresses.  The LLM receives the raw address via the user prompt only.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Semantic location keyword string for RAG (e.g. "outside", "unknown")
        """
        try:
            headers = {'User-Agent': 'FYP_Emotion_Companion/1.0 (student_project)'}
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "json",
                "lat": latitude,
                "lon": longitude,
                "zoom": 14,   # neighbourhood-level — more stable than building-level
                "addressdetails": 1
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            # ------------------------------------------------------------------
            # Derive a semantic category from the Nominatim 'type' / 'category'
            # and the address components.
            # ------------------------------------------------------------------
            place_type = data.get("type", "").lower()
            category   = data.get("category", "").lower()
            address    = data.get("address", {})
            
            # Keys that suggest the user is at a place of study/work
            study_types = {"university", "college", "school", "hospital",
                           "office", "industrial", "commercial"}
            outdoor_types = {"park", "nature_reserve", "forest", "beach",
                             "garden", "recreation_ground", "pitch"}
            
            if place_type in study_types or category in study_types:
                return "university"
            if place_type in outdoor_types or category in outdoor_types:
                return "park"
            if place_type in {"residential", "house", "apartments"}:
                return "home"
            if category in {"highway", "railway", "public_transport"}:
                return "commuting"
            
            # Fall back to the suburb/city name for the LLM but return
            # "outside" so the RAG at least loads the public-space context.
            display = data.get("display_name", f"({latitude}, {longitude})")
            print(f"[ContextService] location type='{place_type}' → defaulting to 'outside'. Address: {display}")
            return "outside"

        except Exception as e:
            print(f"[ContextService] Warning: Could not fetch address: {e}")
            return "unknown"
    
    def get_weather(self, latitude: float, longitude: float) -> str:
        """
        Get weather condition from OpenWeatherMap API.

        When no API key is configured, falls back to a time-based heuristic
        ("clear" during daytime, "unknown" at night) so the RAG still loads a
        meaningful weather context rather than always picking UNKNOWN WEATHER.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Weather condition string recognised by the RAG weather map:
            one of: clear, sunny, clouds, rain, drizzle, thunderstorm, unknown
        """
        if not self.weather_api_key:
            # Graceful fallback: assume clear during day, unknown at night
            hour = datetime.now().hour
            fallback = "clear" if 6 <= hour < 20 else "unknown"
            print(f"[ContextService] No OPENWEATHER_API_KEY — using fallback weather: '{fallback}'")
            return fallback

        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            response = requests.get(config.WEATHER_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            # OpenWeatherMap "main" values: Clear, Clouds, Rain, Drizzle, etc.
            weather_main = data["weather"][0]["main"].lower()
            return weather_main

        except Exception as e:
            print(f"[ContextService] Warning: Could not fetch weather: {e}")
            return "unknown"
    
    def build_context(
        self, 
        latitude: float, 
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> ContextData:
        """
        Build complete context data from GPS coordinates.
        
        This is the main method called by the system.
        
        Args:
            latitude: GPS latitude from mobile device
            longitude: GPS longitude from mobile device
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Complete ContextData object
        """
        # Get time context
        time_of_day, is_weekday = self.get_time_context(timestamp)
        
        # Get semantic location
        location = self.get_semantic_location(latitude, longitude)
        
        # Get weather
        weather = self.get_weather(latitude, longitude)
        
        return ContextData(
            location=location,
            time_of_day=time_of_day,
            weekday=is_weekday,
            weather=weather,
            latitude=latitude,
            longitude=longitude
        )


# Example usage
if __name__ == "__main__":
    service = ContextService()
    
    # Example: User in Colombo, Sri Lanka
    context = service.build_context(
        latitude=6.9271,
        longitude=79.8612
    )
    
    print("Auto-detected context:")
    print(f"  Location: {context.location}")
    print(f"  Time of day: {context.time_of_day}")
    print(f"  Weekday: {context.weekday}")
    print(f"  Weather: {context.weather}")
    print(f"  GPS: ({context.latitude}, {context.longitude})")

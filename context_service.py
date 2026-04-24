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
        Convert GPS coordinates to specific address using OpenStreetMap (Nominatim).
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            Detailed address string (e.g., "Mount Lavinia, Colombo, Sri Lanka")
        """
        try:
            # Nominatim API requires a User-Agent to avoid blocking
            headers = {
                'User-Agent': 'FYP_Emotion_Companion/1.0 (student_project)'
            }
            
            # API URL for reverse geocoding
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "json",
                "lat": latitude,
                "lon": longitude,
                "zoom": 18,
                "addressdetails": 1
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Return the full display name (e.g., "123 Street, City, Country")
            return data.get("display_name", "Unknown Location")
            
        except Exception as e:
            print(f"Warning: Could not fetch address: {e}")
            return f"Unknown ({latitude}, {longitude})"
    
    def get_weather(self, latitude: float, longitude: float) -> str:
        """
        Get weather condition from OpenWeatherMap API.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            Weather condition: "sunny", "cloudy", "rainy", "stormy", etc.
        """
        if not self.weather_api_key:
            return "unknown"  # No API key configured
        
        try:
            # Call OpenWeatherMap API
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            response = requests.get(config.WEATHER_API_URL, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract weather condition
            weather_main = data["weather"][0]["main"].lower()
            
            # Return raw API value as requested
            return weather_main
        
        except Exception as e:
            print(f"Warning: Could not fetch weather: {e}")
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

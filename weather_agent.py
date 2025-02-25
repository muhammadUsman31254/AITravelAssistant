import os
import requests
from datetime import datetime
from crewai import Agent, Task

# Use actual OpenWeatherMap API key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

class WeatherAgent:
    def __init__(self):
        self.agent = Agent(
            role="Weather Information Specialist",
            goal="Provide accurate weather information for the travel destination",
            backstory="""You are a meteorologist who specializes in travel weather forecasting.
                        You provide accurate weather information to help travelers pack 
                        appropriately and plan their activities.""",
            verbose=True
        )
    
    def create_task(self, destination):
        """Create a task for the weather agent"""
        return Task(
            description=f"""
                Provide the current weather and 7-day forecast for {destination}.
                Include:
                - Current temperature, conditions, and precipitation chance
                - Daily high and low temperatures for the next 7 days
                - General weather conditions for each day
                - Packing suggestions based on the weather
            """,
            agent=self.agent,
            expected_output="""A detailed weather report for the destination including
                              current conditions, 7-day forecast, and packing suggestions."""
        )
    
    def get_weather_info(self, destination):
        """
        Get current weather and forecast for the destination using OpenWeatherMap API
        """
        try:
            # Fetch current weather
            current_url = f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={WEATHER_API_KEY}&units=metric"
            current_response = requests.get(current_url)
            current_data = current_response.json()

            current_temp = current_data["main"]["temp"]
            current_condition = current_data["weather"][0]["description"].capitalize()

            # Fetch 7-day forecast
            lat = current_data["coord"]["lat"]
            lon = current_data["coord"]["lon"]
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            
            forecast = []
            for i in range(0, len(forecast_data["list"]), 8):  # Every 8th entry (~24 hours apart)
                day_data = forecast_data["list"][i]
                date = datetime.utcfromtimestamp(day_data["dt"]).strftime("%Y-%m-%d")
                condition = day_data["weather"][0]["description"].capitalize()
                high_temp = day_data["main"]["temp_max"]
                low_temp = day_data["main"]["temp_min"]
                precipitation = day_data.get("pop", 0) * 100  # Probability of precipitation
                
                forecast.append({
                    "date": date,
                    "description": condition,
                    "high": high_temp,
                    "low": low_temp,
                    "precipitation": f"{precipitation}%"
                })
            
            weather_info = {
                "destination": destination,
                "current": f"{current_temp}°C, {current_condition}",
                "forecast": forecast
            }
            return weather_info
        
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return {"current": "Not available", "forecast": []}
    
    def get_packing_suggestions(self, weather_info):
        """Generate packing suggestions based on weather forecast"""
        avg_high = sum(day["high"] for day in weather_info["forecast"]) / len(weather_info["forecast"])
        avg_low = sum(day["low"] for day in weather_info["forecast"]) / len(weather_info["forecast"])
        conditions = [day["description"] for day in weather_info["forecast"]]

        suggestions = ["Comfortable walking shoes"]

        # Temperature-based suggestions
        if avg_high > 30:
            suggestions.extend(["Lightweight clothing", "Sunscreen", "Sunglasses", "Hat"])
        elif avg_high > 20:
            suggestions.extend(["Light layers", "Long and short sleeve options"])
        elif avg_high > 10:
            suggestions.extend(["Medium layers", "Light jacket or sweater"])
        else:
            suggestions.extend(["Warm clothing", "Heavy jacket", "Gloves", "Scarf"])

        # Weather condition-based suggestions
        if any("rain" in cond.lower() or "thunderstorm" in cond.lower() for cond in conditions):
            suggestions.extend(["Umbrella", "Waterproof jacket", "Waterproof shoes"])
        
        return suggestions

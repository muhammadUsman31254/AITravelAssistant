from crewai import Agent, Task
from cerebras_client import CerebrasClient

class ChatAssistantAgent:
    def __init__(self):
        self.agent = Agent(
            role="Travel Chat Assistant",
            goal="Answer travel-related questions and provide helpful information",
            backstory="""You are a knowledgeable travel assistant who can answer
                        questions about destinations, activities, travel tips, and more.
                        You provide personalized advice based on the traveler's itinerary.""",
            verbose=True
        )
        
        # Initialize Cerebras client
        self.cerebras = CerebrasClient()
    
    def create_task(self):
        """Create a task for the chat assistant agent"""
        return Task(
            description="""
                Answer the user's travel-related questions based on their:
                - Destination
                - Itinerary
                - Weather information
                - Flight and hotel options
                
                Provide helpful, relevant, and personalized information that
                enhances their travel experience.
            """,
            agent=self.agent,
            expected_output="""Informative and helpful responses to
                              the user's travel-related questions."""
        )
    
    def answer_question(self, question, destination, itinerary, weather_info):
        """
        Generate a response to the user's travel question using Cerebras LLM
        """
        # Create context for the model
        context = {
            "destination": destination,
            "itinerary_summary": self._summarize_itinerary(itinerary),
            "weather": self._summarize_weather(weather_info)
        }
        
        # Generate response using Cerebras
        response = self.cerebras.answer_travel_question(question, context)
        
        return response
    
    def _summarize_itinerary(self, itinerary):
        """Create a brief summary of the itinerary for context"""
        if isinstance(itinerary, str):
            return itinerary[:500] + "..." if len(itinerary) > 500 else itinerary
        
        # If itinerary is a more structured object, summarize accordingly
        # This would depend on your actual data structure
        return str(itinerary)
    
    def _summarize_weather(self, weather_info):
        """Create a brief summary of the weather for context"""
        if not weather_info:
            return "Weather information not available"
        
        current = weather_info.get("current", "Not available")
        forecast_summary = ", ".join([
            f"{day['date']}: {day['description']}, {day['high']}°C/{day['low']}°C" 
            for day in weather_info.get("forecast", [])[:3]
        ])
        
        return f"Current: {current}. Forecast: {forecast_summary}"
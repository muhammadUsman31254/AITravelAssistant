from crewai import Agent, Task
from cerebras_client import CerebrasClient
from datetime import timedelta

class TravelPlannerAgent:
    def __init__(self):
        self.agent = Agent(
            role="Travel Planner",
            goal="Create a personalized travel itinerary based on user preferences",
            backstory="""You are an experienced travel planner who specializes in 
                        creating custom itineraries for travelers around the world.
                        You understand different travel styles, budgets, and preferences.""",
            verbose=True
        )
        
        # Initialize Cerebras client
        self.cerebras = CerebrasClient()
    
    def create_task(self, destination, departure_date, return_date, budget, num_travelers):
        """Create a task for the travel planner agent"""
        return Task(
            description=f"""
                Create a detailed itinerary for a trip to {destination} from 
                {departure_date} to {return_date} with a budget of ${budget} for {num_travelers} travelers.
                
                The itinerary should include:
                1. Daily activities and attractions to visit
                2. Suggested times for each activity
                3. Estimated costs for activities
                4. Restaurant recommendations for each day
                
                Format the itinerary as a day-by-day plan that is easy to follow.
            """,
            agent=self.agent,
            expected_output="""A detailed day-by-day itinerary with activities, 
                              times, estimated costs, and restaurant recommendations."""
        )
    
    def generate_itinerary(self, user_preferences):
        """Generate a travel itinerary based on user preferences using Cerebras LLM"""
        departure_date_str = user_preferences["departure_date"].strftime("%Y-%m-%d")
        return_date_str = user_preferences["return_date"].strftime("%Y-%m-%d")
        
        # Use Cerebras to generate the itinerary
        itinerary = self.cerebras.generate_itinerary(
            destination=user_preferences["destination"],
            departure_date=departure_date_str,
            return_date=return_date_str,
            budget=user_preferences["budget"],
            num_travelers=user_preferences["num_travelers"]
        )
        
        return itinerary
import os
from cerebras.cloud.sdk import Cerebras

class CerebrasClient:
    def __init__(self):
        """Initialize the Cerebras client with API key"""
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable is not set")
        
        self.client = Cerebras(api_key=api_key)
        self.model = os.environ.get("CEREBRAS_MODEL", "llama3.1-8b")
    
    def generate_response(self, prompt, system_prompt=None, temperature=0.7):
        """
        Generate a response using the Cerebras LLM
        
        Args:
            prompt (str): User's prompt/question
            system_prompt (str, optional): System instructions for the model
            temperature (float, optional): Controls randomness in generation
            
        Returns:
            str: Generated response from the model
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Generate completion
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=temperature
            )
            
            # Extract and return the generated response
            return chat_completion.choices[0].message.content
        except Exception as e:
            # Log error and return fallback response
            print(f"Cerebras API error: {str(e)}")
            return f"I'm sorry, but I encountered an issue generating a response. Please try again later."
    
    def generate_itinerary(self, destination, departure_date, return_date, budget, num_travelers):
        """
        Generate a travel itinerary using the Cerebras LLM
        
        Args:
            destination (str): Travel destination
            departure_date (str): Departure date
            return_date (str): Return date
            budget (int): Travel budget
            num_travelers (int): Number of travelers
            
        Returns:
            str: Generated itinerary
        """
        prompt = f"""
        Create a detailed travel itinerary for a trip to {destination} from {departure_date} to {return_date} 
        with a budget of ${budget} for {num_travelers} travelers.
        
        The itinerary should include:
        1. Daily activities and attractions to visit
        2. Suggested times for each activity
        3. Estimated costs for activities
        4. Restaurant recommendations for each day
        
        Format the itinerary as a day-by-day plan.
        """
        
        system_prompt = """
        You are an expert travel planner. Create a detailed, realistic, and helpful travel itinerary
        based on the provided destination, dates, budget, and number of travelers.
        Include varied activities, local attractions, and dining options.
        Ensure the itinerary is well-structured, practical, and stays within budget.
        """
        
        return self.generate_response(prompt, system_prompt)
    
    def answer_travel_question(self, question, context=None):
        """
        Answer a travel-related question using the Cerebras LLM
        
        Args:
            question (str): User's travel question
            context (dict, optional): Contextual information (itinerary, weather, etc.)
            
        Returns:
            str: Generated answer
        """
        prompt = question
        
        if context:
            # Format context information as part of the prompt
            context_str = "\n".join([f"{key.title()}: {value}" for key, value in context.items()])
            prompt = f"Context information:\n{context_str}\n\nQuestion: {question}"
        
        system_prompt = """
        You are a helpful travel assistant with extensive knowledge about destinations worldwide.
        Provide accurate, helpful, and concise answers to travel-related questions.
        If you don't have specific information, provide general guidance based on
        travel best practices. Be friendly and conversational in your responses.
        """
        
        return self.generate_response(prompt, system_prompt)
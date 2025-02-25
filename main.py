import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st

from travel_planner import TravelPlannerAgent
from flight_hotel_finder import FlightHotelFinderAgent
from weather_agent import WeatherAgent
from chat_assistant import ChatAssistantAgent

# Load environment variables
load_dotenv()

def main():
    # Set page config for a wider layout and custom title
    st.set_page_config(
        page_title="AI Travel Assistant",
        page_icon="✈️",
        layout="wide",
    )
    
    # Custom CSS for improved styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #0066cc;
        text-align: center;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .hackathon-header {
        font-size: 1.4rem;
        color: #ff6b6b;
        text-align: center;
        margin-top: 0;
        padding-top: 0;
        margin-bottom: 2rem;
    }
    .subheader {
        font-size: 1.8rem;
        color: #4a4a4a;
    }
    .tab-subheader {
        font-size: 1.5rem;
        color: #0066cc;
        margin-bottom: 1rem;
    }
    .welcome-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sidebar-header {
        font-size: 1.5rem;
        color: #0066cc;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title with hackathon branding
    st.markdown('<h1 class="main-header">✈️ AI Travel Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="hackathon-header">Cerebras + CrewAI Agents Hackathon! 🤖</h2>', unsafe_allow_html=True)
    
    # Sidebar for user inputs with improved styling
    with st.sidebar:
        st.markdown('<h2 class="sidebar-header">🗺️ Plan Your Trip</h2>', unsafe_allow_html=True)
        destination = st.text_input("🏙️ Destination")
        departure_date = st.date_input("🛫 Departure Date")
        return_date = st.date_input("🛬 Return Date")
        budget = st.slider("💰 Budget ($)", 0, 1000, 100, 50)
        num_travelers = st.number_input("👥 Number of Travelers", 1, 10, 1)
        
        # Use a more attractive button style
        plan_button = st.button("🚀 Plan My Trip", use_container_width=True)
        
        if plan_button:
            if not destination:
                st.error("⚠️ Please enter a destination")
                return
            
            if departure_date >= return_date:
                st.error("⚠️ Return date must be after departure date")
                return
                
            st.session_state.planning_started = True
            st.session_state.destination = destination
            st.session_state.departure_date = departure_date
            st.session_state.return_date = return_date
            st.session_state.budget = budget
            st.session_state.num_travelers = num_travelers
    
    # Initialize session state
    if 'planning_started' not in st.session_state:
        st.session_state.planning_started = False
        st.session_state.messages = []

    # Display welcome message when app starts with better styling
    if not st.session_state.planning_started:
        st.markdown("""
        <div class="welcome-container">
            <h1>👋 Welcome to the AI Travel Assistant!</h1>
            <h3>✨ Powered by Cerebras + CrewAI ✨</h3>
            <p>Enter your travel details in the sidebar to start planning your dream vacation.</p>
            <p>Our AI agents will work together to create a personalized travel experience just for you!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add some features preview
        st.markdown("### 🌟 What Our Assistant Can Do For You")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("#### 📅 Itinerary Planning")
            st.markdown("Customized day-by-day plans for your destination")
        
        with col2:
            st.markdown("#### ✈️ Flight Options")
            st.markdown("Find the best flight deals for your dates")
            
        with col3:
            st.markdown("#### 🏨 Hotel Suggestions")
            st.markdown("Accommodations that match your preferences")
            
        with col4:
            st.markdown("#### 🌤️ Weather Forecasts")
            st.markdown("Know what to pack with accurate weather data")
            
        return
    
    # Create and run the agent crew when planning starts
    if st.session_state.planning_started and 'itinerary' not in st.session_state:
        with st.spinner("🔃 Our AI agents are planning your perfect trip..."):
            try:
                # Initialize agents
                travel_planner = TravelPlannerAgent()
                flight_hotel_finder = FlightHotelFinderAgent()
                weather_agent = WeatherAgent()
                chat_assistant = ChatAssistantAgent()
                
                # Create user preferences
                user_preferences = {
                    "destination": st.session_state.destination,
                    "departure_date": st.session_state.departure_date,
                    "return_date": st.session_state.return_date,
                    "budget": st.session_state.budget,
                    "num_travelers": st.session_state.num_travelers
                }
                
                # Generate itinerary using travel planner
                st.session_state.itinerary = travel_planner.generate_itinerary(user_preferences)
                
                # Get flight and hotel options
                st.session_state.flight_options = flight_hotel_finder.get_flight_options(
                    st.session_state.destination, 
                    st.session_state.departure_date,
                    st.session_state.return_date,
                    st.session_state.num_travelers
                )
                
                st.session_state.hotel_options = flight_hotel_finder.get_hotel_options(
                    st.session_state.destination, 
                    st.session_state.departure_date,
                    st.session_state.return_date,
                    st.session_state.num_travelers
                )
                
                # Get weather information
                st.session_state.weather_info = weather_agent.get_weather_info(st.session_state.destination)
                
            except Exception as e:
                st.error(f"⚠️ An error occurred: {str(e)}")
                st.session_state.planning_started = False
                return
    
    # Display results with improved formatting
    if st.session_state.planning_started and 'itinerary' in st.session_state:
        # Create tabs for different sections with icons
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Itinerary", "✈️ Flights", "🏨 Hotels", "🌤️ Weather"])
        
        with tab1:
            st.markdown(f'<h2 class="tab-subheader">Your {st.session_state.destination} Adventure</h2>', unsafe_allow_html=True)
            st.write(st.session_state.itinerary)
        
        with tab2:
            st.markdown('<h2 class="tab-subheader">✈️ Flight Options</h2>', unsafe_allow_html=True)
            for i, flight in enumerate(st.session_state.flight_options):
                with st.expander(f"Option {i+1}: {flight['airline']} - ${flight['price']}"):
                    st.write(f"**Departure:** 🛫 {flight['departure_time']} - **Arrival:** 🛬 {flight['arrival_time']}")
                    st.write(f"**Duration:** ⏱️ {flight['duration']}")
                    st.write(f"**Stops:** 🛑 {flight['stops']}")
        
        with tab3:
            st.markdown('<h2 class="tab-subheader">🏨 Hotel Options</h2>', unsafe_allow_html=True)
            for i, hotel in enumerate(st.session_state.hotel_options):
                with st.expander(f"Option {i+1}: {hotel['name']} - ${hotel['price']}/night"):
                    st.write(f"**Rating:** ⭐ {hotel['rating']}/5")
                    st.write(f"**Location:** 📍 {hotel['location']}")
                    st.write(f"**Amenities:** 🛎️ {', '.join(hotel['amenities'])}")
        
        with tab4:
            st.markdown(f'<h2 class="tab-subheader">🌤️ Weather in {st.session_state.destination}</h2>', unsafe_allow_html=True)
            st.write(f"**Current:** 🌡️ {st.session_state.weather_info['current']}")
            st.write("**Forecast:** 📊")
            for day in st.session_state.weather_info['forecast']:
                st.write(f"- 📆 {day['date']}: {day['description']}, High: 🔺 {day['high']}°C, Low: 🔻 {day['low']}°C")
    
    # Chat interface with improved styling
    if st.session_state.planning_started:
        st.markdown('<h2 class="subheader">💬 Chat with Your Travel Assistant</h2>', unsafe_allow_html=True)
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a travel question... 🔍"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    if 'itinerary' in st.session_state:
                        chat_agent = ChatAssistantAgent()
                        response = chat_agent.answer_question(
                            question=prompt,
                            destination=st.session_state.destination,
                            itinerary=st.session_state.itinerary,
                            weather_info=st.session_state.weather_info
                        )
                    else:
                        response = "Please plan your trip first using the sidebar options."
                    
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
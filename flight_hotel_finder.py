from crewai import Agent, Task
import os
import requests
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlightHotelFinderAgent:
    def __init__(self):
        # Get Amadeus API credentials from environment variables
        self.amadeus_api_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
        self.access_token = None
        self.token_expiry = None
        
        self.agent = Agent(
            role="Flight and Hotel Finder",
            goal="Find the best flight and hotel options based on user preferences",
            backstory="""You are an expert in finding the best travel deals.
                        You know how to search for flights and hotels that match 
                        the traveler's budget and preferences.""",
            verbose=True
        )
    
    def _get_amadeus_token(self):
        """Get or refresh Amadeus API OAuth token"""
        now = datetime.now()
        
        # Check if token exists and is still valid
        if self.access_token and self.token_expiry and now < self.token_expiry:
            return self.access_token
            
        try:
            # Request new token
            token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.amadeus_api_key,
                "client_secret": self.amadeus_api_secret
            }
            
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Set token expiry (usually 30 minutes, but we'll be conservative)
            self.token_expiry = now + timedelta(seconds=token_data["expires_in"] - 60)
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error obtaining Amadeus token: {str(e)}")
            return None
    
    def create_task(self, destination, departure_date, return_date, budget, num_travelers):
        """Create a task for the flight and hotel finder agent"""
        return Task(
            description=f"""
                Search for the best flight and hotel options for a trip to {destination} from 
                {departure_date} to {return_date} with a budget of ${budget} for {num_travelers} travelers.
                
                For each flight option, provide:
                - Airline
                - Departure and arrival times
                - Duration
                - Number of stops
                - Price
                
                For each hotel option, provide:
                - Hotel name
                - Location
                - Rating
                - Price per night
                - Available amenities
            """,
            agent=self.agent,
            expected_output="""A list of flight and hotel options with
                              detailed information about each option."""
        )
    
    def _get_iata_code(self, city_name):
        """Get IATA city code from city name using Amadeus Location API"""
        token = self._get_amadeus_token()
        if not token:
            logger.error("Failed to get Amadeus token")
            return None
            
        try:
            url = f"https://test.api.amadeus.com/v1/reference-data/locations/cities"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "keyword": city_name,
                "max": 1
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]["iataCode"]
            return None
            
        except Exception as e:
            logger.error(f"Error getting IATA code for {city_name}: {str(e)}")
            return None
            
    def get_flight_options(self, destination, departure_date, return_date, num_travelers):
        """
        Search for flight options using Amadeus Flight Offers Search API
        """
        token = self._get_amadeus_token()
        if not token:
            logger.warning("Using fallback mock data due to missing Amadeus token")
            return self._get_mock_flight_options(destination, departure_date, return_date, num_travelers)
            
        # Format dates for API
        departure_str = departure_date.strftime("%Y-%m-%d")
        return_str = return_date.strftime("%Y-%m-%d")
        
        # Get IATA codes (assuming origin is New York for this example)
        origin_code = "NYC"  # Default to NYC
        destination_code = self._get_iata_code(destination)
        
        if not destination_code:
            logger.warning(f"Could not find IATA code for {destination}, using fallback data")
            return self._get_mock_flight_options(destination, departure_date, return_date, num_travelers)
        
        try:
            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "originLocationCode": origin_code,
                "destinationLocationCode": destination_code,
                "departureDate": departure_str,
                "returnDate": return_str,
                "adults": num_travelers,
                "max": 5,
                "currencyCode": "USD"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            flight_options = []
            for offer in data.get("data", [])[:3]:  # Limit to 3 options
                try:
                    price = float(offer["price"]["total"])
                    itineraries = offer["itineraries"]
                    
                    # Get outbound flight details
                    outbound = itineraries[0]["segments"][0]
                    carrier_code = outbound["carrierCode"]
                    departure_time = outbound["departure"]["at"].split("T")[1][:5]
                    arrival_time = outbound["arrival"]["at"].split("T")[1][:5]
                    duration_parts = outbound["duration"].replace("PT", "").replace("H", "h ").replace("M", "m")
                    
                    # Count stops
                    stops = len(itineraries[0]["segments"]) - 1
                    
                    # Get airline name (simplified)
                    airlines = {
                        "AA": "American Airlines",
                        "UA": "United Airlines",
                        "DL": "Delta Airlines",
                        "LH": "Lufthansa",
                        "BA": "British Airways",
                        "AF": "Air France",
                        "EK": "Emirates",
                        "QR": "Qatar Airways"
                    }
                    airline = airlines.get(carrier_code, carrier_code)
                    
                    flight = {
                        "airline": airline,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time,
                        "duration": duration_parts,
                        "stops": stops,
                        "price": round(price)
                    }
                    flight_options.append(flight)
                except (KeyError, IndexError) as e:
                    logger.error(f"Error parsing flight offer: {str(e)}")
                    continue
            
            if flight_options:
                return flight_options
            else:
                logger.warning("No valid flight options found, using fallback data")
                return self._get_mock_flight_options(destination, departure_date, return_date, num_travelers)
                
        except Exception as e:
            logger.error(f"Error fetching flight data: {str(e)}")
            return self._get_mock_flight_options(destination, departure_date, return_date, num_travelers)
    
    def get_hotel_options(self, destination, check_in_date, check_out_date, num_travelers):
        """
        Search for hotel options using Amadeus Hotel Search API
        """
        token = self._get_amadeus_token()
        if not token:
            logger.warning("Using fallback mock data due to missing Amadeus token")
            return self._get_mock_hotel_options(destination, check_in_date, check_out_date, num_travelers)
            
        # Format dates for API
        check_in_str = check_in_date.strftime("%Y-%m-%d")
        check_out_str = check_out_date.strftime("%Y-%m-%d")
        
        # Get IATA city code for destination
        city_code = self._get_iata_code(destination)
        
        if not city_code:
            logger.warning(f"Could not find IATA code for {destination}, using fallback data")
            return self._get_mock_hotel_options(destination, check_in_date, check_out_date, num_travelers)
        
        try:
            # First get a list of hotels
            hotel_list_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {
                "cityCode": city_code,
                "radius": 5,
                "radiusUnit": "KM",
                "hotelSource": "ALL"
            }
            
            response = requests.get(hotel_list_url, headers=headers, params=params)
            response.raise_for_status()
            hotels_data = response.json()
            
            if not hotels_data.get("data") or len(hotels_data["data"]) == 0:
                logger.warning(f"No hotels found in {destination}, using fallback data")
                return self._get_mock_hotel_options(destination, check_in_date, check_out_date, num_travelers)
            
            # Get hotel IDs for search (limit to first 3 hotels)
            hotel_ids = [hotel["hotelId"] for hotel in hotels_data["data"][:3]]
            
            hotel_options = []
            
            # Get offers for each hotel
            for hotel_id in hotel_ids:
                try:
                    offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
                    params = {
                        "hotelIds": hotel_id,
                        "adults": num_travelers,
                        "checkInDate": check_in_str,
                        "checkOutDate": check_out_str,
                        "roomQuantity": 1,
                        "currency": "USD"
                    }
                    
                    offers_response = requests.get(offers_url, headers=headers, params=params)
                    offers_response.raise_for_status()
                    offers_data = offers_response.json()
                    
                    if not offers_data.get("data") or len(offers_data["data"]) == 0:
                        continue
                    
                    hotel_data = offers_data["data"][0]["hotel"]
                    offer = offers_data["data"][0]["offers"][0]
                    
                    # Extract hotel details
                    name = hotel_data.get("name", f"{destination} Hotel")
                    location = f"{hotel_data.get('address', {}).get('cityName', destination)}"
                    
                    # Extract rating (convert to 5-point scale)
                    rating_raw = hotel_data.get("rating", "3")
                    try:
                        rating = float(rating_raw)
                    except ValueError:
                        # Handle non-numeric ratings
                        rating_map = {"ECONOMY": 2.0, "STANDARD": 3.0, "SUPERIOR": 4.0, "DELUXE": 5.0}
                        rating = rating_map.get(rating_raw, 3.0)
                    
                    # Extract price
                    price_per_night = float(offer["price"]["total"]) / (check_out_date - check_in_date).days
                    
                    # Extract amenities
                    amenities = []
                    for amenity in hotel_data.get("amenities", []):
                        amenity_name = amenity.replace("_", " ").title()
                        amenities.append(amenity_name)
                    
                    if not amenities:
                        amenities = ["Wi-Fi", "Breakfast"]
                    
                    hotel = {
                        "name": name,
                        "location": location,
                        "rating": round(rating, 1),
                        "price": round(price_per_night),
                        "total_price": round(float(offer["price"]["total"])),
                        "amenities": amenities[:5]  # Limit to 5 amenities
                    }
                    
                    hotel_options.append(hotel)
                    
                except Exception as e:
                    logger.error(f"Error fetching hotel offers for {hotel_id}: {str(e)}")
                    continue
            
            if hotel_options:
                return hotel_options
            else:
                logger.warning("No valid hotel options found, using fallback data")
                return self._get_mock_hotel_options(destination, check_in_date, check_out_date, num_travelers)
                
        except Exception as e:
            logger.error(f"Error fetching hotel data: {str(e)}")
            return self._get_mock_hotel_options(destination, check_in_date, check_out_date, num_travelers)
    
    def _get_mock_flight_options(self, destination, departure_date, return_date, num_travelers):
        """Provide mock flight options as fallback"""
        import random
        
        airlines = ["Delta", "United", "American", "Southwest", "JetBlue"]
        flight_options = []
        
        for i in range(3):  # Generate 3 flight options
            # Generate random flight details for demonstration
            airline = random.choice(airlines)
            dep_hour = random.randint(6, 22)
            duration_hours = random.randint(2, 8)
            arr_hour = (dep_hour + duration_hours) % 24
            stops = random.randint(0, 2)
            price = random.randint(300, 800) * num_travelers
            
            flight = {
                "airline": airline,
                "departure_time": f"{dep_hour:02d}:00",
                "arrival_time": f"{arr_hour:02d}:00",
                "duration": f"{duration_hours}h {random.randint(0, 59)}m",
                "stops": stops,
                "price": price
            }
            flight_options.append(flight)
        
        return flight_options
    
    def _get_mock_hotel_options(self, destination, check_in_date, check_out_date, num_travelers):
        """Provide mock hotel options as fallback"""
        import random
        
        hotel_names = [
            f"{destination} Grand Hotel", 
            f"{destination} Plaza", 
            f"The {destination} Inn", 
            f"Luxury Suites {destination}"
        ]
        
        amenities_options = [
            ["Wi-Fi", "Pool", "Gym", "Restaurant", "Bar"],
            ["Wi-Fi", "Breakfast", "Parking", "Room Service"],
            ["Wi-Fi", "Spa", "Restaurant", "Conference Room"],
            ["Wi-Fi", "Pool", "Breakfast", "Airport Shuttle"]
        ]
        
        hotel_options = []
        
        for i in range(3):  # Generate 3 hotel options
            # Generate random hotel details for demonstration
            name = random.choice(hotel_names)
            rating = round(random.uniform(3.0, 5.0), 1)
            price_per_night = random.randint(80, 300)
            amenities = random.choice(amenities_options)
            
            hotel = {
                "name": name,
                "location": f"Downtown {destination}",
                "rating": rating,
                "price": price_per_night,
                "total_price": price_per_night * (check_out_date - check_in_date).days,
                "amenities": amenities
            }
            hotel_options.append(hotel)
        
        return hotel_options
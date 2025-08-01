"""
Amadeus API Integration

This module provides real flight data integration using the Amadeus API
for actual flight searches, pricing, and availability.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from dataclasses import dataclass

try:
    from amadeus import Client, ResponseError
except ImportError:
    print("Warning: Amadeus SDK not installed. Install with: pip install amadeus")
    Client = None
    ResponseError = Exception


@dataclass
class FlightOffer:
    """Data class for flight offers from Amadeus API"""
    id: str
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    airline: str = ""
    flight_number: str = ""
    duration: str = ""
    stops: int = 0
    cabin_class: str = "ECONOMY"
    segments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.segments is None:
            self.segments = []


class AmadeusClient:
    """
    Client for interacting with Amadeus API to get real flight data.
    
    This class handles authentication, flight searches, and data processing
    for the rewards redemption optimizer.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Amadeus client.
        
        Args:
            api_key: Amadeus API key (defaults to environment variable)
            api_secret: Amadeus API secret (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv('AMADEUS_API_KEY')
        self.api_secret = api_secret or os.getenv('AMADEUS_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            print("Warning: Amadeus API credentials not found.")
            print("Set AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables")
            print("Or get free API key from: https://developers.amadeus.com/")
            self.client = None
        else:
            try:
                self.client = Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret
                )
                print("✅ Amadeus API client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Amadeus client: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Amadeus API is available and configured."""
        return self.client is not None
    
    def search_flights(self, origin: str, destination: str, 
                      departure_date: date, return_date: Optional[date] = None,
                      adults: int = 1, max_offers: int = 10) -> List[FlightOffer]:
        """
        Search for available flights using Amadeus API.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date
            return_date: Return date (optional for one-way)
            adults: Number of adult passengers
            max_offers: Maximum number of offers to return
            
        Returns:
            List of FlightOffer objects
        """
        if not self.is_available():
            return self._get_mock_flights(origin, destination, departure_date, return_date)
        
        try:
            # Format dates for API
            departure_str = departure_date.strftime('%Y-%m-%d')
            return_str = return_date.strftime('%Y-%m-%d') if return_date else None
            
            # Search for flight offers
            response = self.client.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_str,
                returnDate=return_str,
                adults=adults,
                max=max_offers,
                currencyCode="USD"
            )
            
            return self._parse_flight_offers(response.data)
            
        except ResponseError as e:
            print(f"Amadeus API error: {e}")
            return self._get_mock_flights(origin, destination, departure_date, return_date)
        except Exception as e:
            print(f"Error searching flights: {e}")
            return self._get_mock_flights(origin, destination, departure_date, return_date)
    
    def _parse_flight_offers(self, offers_data: List[Dict[str, Any]]) -> List[FlightOffer]:
        """Parse Amadeus API response into FlightOffer objects."""
        offers = []
        
        for offer in offers_data:
            try:
                # Extract basic info
                flight_offer = FlightOffer(
                    id=offer.get('id', ''),
                    origin=offer['itineraries'][0]['segments'][0]['departure']['iataCode'],
                    destination=offer['itineraries'][0]['segments'][-1]['arrival']['iataCode'],
                    departure_date=offer['itineraries'][0]['segments'][0]['departure']['at'][:10],
                    price=float(offer['price']['total']),
                    currency=offer['price']['currency'],
                    airline=offer['itineraries'][0]['segments'][0]['carrierCode'],
                    flight_number=offer['itineraries'][0]['segments'][0]['number'],
                    duration=offer['itineraries'][0]['duration'],
                    stops=len(offer['itineraries'][0]['segments']) - 1,
                    cabin_class=offer['travelerPricings'][0]['fareDetailsBySegment'][0]['cabin'],
                    segments=offer['itineraries'][0]['segments']
                )
                
                # Add return date if exists
                if len(offer['itineraries']) > 1:
                    flight_offer.return_date = offer['itineraries'][1]['segments'][0]['departure']['at'][:10]
                
                offers.append(flight_offer)
                
            except (KeyError, IndexError) as e:
                print(f"Error parsing flight offer: {e}")
                continue
        
        return offers
    
    def _get_mock_flights(self, origin: str, destination: str, 
                         departure_date: date, return_date: Optional[date] = None) -> List[FlightOffer]:
        """Generate mock flight data when API is not available."""
        print("Using mock flight data (Amadeus API not available)")
        
        # Calculate distance for realistic pricing
        distance = self._calculate_distance(origin, destination)
        base_price = distance * 0.15  # Rough estimate: $0.15 per mile
        
        mock_offers = [
            FlightOffer(
                id="mock_1",
                origin=origin,
                destination=destination,
                departure_date=departure_date.strftime('%Y-%m-%d'),
                return_date=return_date.strftime('%Y-%m-%d') if return_date else None,
                price=base_price * 0.8,  # Economy
                currency="USD",
                airline="AA",
                flight_number="123",
                duration=f"PT{distance//500 + 1}H",
                stops=0,
                cabin_class="ECONOMY",
                segments=[{
                    'departure': {'iataCode': origin, 'at': f"{departure_date}T10:00:00"},
                    'arrival': {'iataCode': destination, 'at': f"{departure_date}T13:00:00"},
                    'carrierCode': 'AA',
                    'number': '123'
                }]
            ),
            FlightOffer(
                id="mock_2",
                origin=origin,
                destination=destination,
                departure_date=departure_date.strftime('%Y-%m-%d'),
                return_date=return_date.strftime('%Y-%m-%d') if return_date else None,
                price=base_price * 1.5,  # Premium economy
                currency="USD",
                airline="DL",
                flight_number="456",
                duration=f"PT{distance//500 + 1}H",
                stops=1,
                cabin_class="PREMIUM_ECONOMY",
                segments=[
                    {
                        'departure': {'iataCode': origin, 'at': f"{departure_date}T08:00:00"},
                        'arrival': {'iataCode': 'ORD', 'at': f"{departure_date}T10:00:00"},
                        'carrierCode': 'DL',
                        'number': '456'
                    },
                    {
                        'departure': {'iataCode': 'ORD', 'at': f"{departure_date}T11:30:00"},
                        'arrival': {'iataCode': destination, 'at': f"{departure_date}T14:30:00"},
                        'carrierCode': 'DL',
                        'number': '789'
                    }
                ]
            )
        ]
        
        return mock_offers
    
    def _calculate_distance(self, origin: str, destination: str) -> int:
        """Calculate approximate distance between airports."""
        # Simplified distance calculation
        distances = {
            ('JFK', 'LAX'): 2475,
            ('JFK', 'ORD'): 740,
            ('JFK', 'ATL'): 760,
            ('JFK', 'DFW'): 1389,
            ('LAX', 'ORD'): 1744,
            ('LAX', 'ATL'): 1947,
            ('LAX', 'DFW'): 1235,
            ('ORD', 'ATL'): 606,
            ('ORD', 'DFW'): 802,
            ('ATL', 'DFW'): 731,
        }
        
        route = (origin, destination)
        reverse_route = (destination, origin)
        
        if route in distances:
            return distances[route]
        elif reverse_route in distances:
            return distances[reverse_route]
        else:
            return 1000  # Default distance
    
    def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """
        Get airport information from Amadeus API.
        
        Args:
            airport_code: Airport IATA code
            
        Returns:
            Dictionary with airport information
        """
        if not self.is_available():
            return {
                'name': f'Airport {airport_code}',
                'city': 'Unknown',
                'country': 'Unknown'
            }
        
        try:
            response = self.client.reference_data.locations.get(
                keyword=airport_code,
                subType="AIRPORT"
            )
            
            if response.data:
                airport = response.data[0]
                return {
                    'name': airport.get('name', ''),
                    'city': airport.get('address', {}).get('cityName', ''),
                    'country': airport.get('address', {}).get('countryName', '')
                }
            
        except Exception as e:
            print(f"Error getting airport info: {e}")
        
        return {
            'name': f'Airport {airport_code}',
            'city': 'Unknown',
            'country': 'Unknown'
        }
    
    def search_hotels(self, city_code: str, check_in: date, check_out: date,
                     adults: int = 1) -> List[Dict[str, Any]]:
        """
        Search for hotels using Amadeus API.
        
        Args:
            city_code: City code
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            
        Returns:
            List of hotel offers
        """
        if not self.is_available():
            return self._get_mock_hotels(city_code, check_in, check_out)
        
        try:
            response = self.client.shopping.hotel_offers.get(
                cityCode=city_code,
                checkInDate=check_in.strftime('%Y-%m-%d'),
                checkOutDate=check_out.strftime('%Y-%m-%d'),
                adults=adults,
                currency="USD"
            )
            
            return response.data
            
        except Exception as e:
            print(f"Error searching hotels: {e}")
            return self._get_mock_hotels(city_code, check_in, check_out)
    
    def _get_mock_hotels(self, city_code: str, check_in: date, check_out: date) -> List[Dict[str, Any]]:
        """Generate mock hotel data."""
        nights = (check_out - check_in).days
        
        return [
            {
                'hotel': {
                    'name': f'Mock Hotel {city_code}',
                    'rating': '4',
                    'hotelId': 'mock_1'
                },
                'offers': [{
                    'price': {
                        'total': str(150 * nights),
                        'currency': 'USD'
                    },
                    'room': {
                        'type': 'STANDARD'
                    }
                }]
            },
            {
                'hotel': {
                    'name': f'Luxury Hotel {city_code}',
                    'rating': '5',
                    'hotelId': 'mock_2'
                },
                'offers': [{
                    'price': {
                        'total': str(300 * nights),
                        'currency': 'USD'
                    },
                    'room': {
                        'type': 'DELUXE'
                    }
                }]
            }
        ] 
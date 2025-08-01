"""
Part 2: Synthetic Routing Logic

Core functionality to find optimal flight routes including direct flights
and synthetic routing through major hub airports, now with Amadeus API integration.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
import json

from .amadeus_client import AmadeusClient, FlightOffer


@dataclass
class FlightRoute:
    """Data class to represent a flight route"""
    origin: str
    destination: str
    route_type: str  # 'direct', 'layover', 'multi_stop'
    total_miles: int
    total_fees: float
    segments: List[Dict[str, Any]]
    duration_hours: float
    layover_airports: List[str] = None
    cash_price: float = 0.0
    airline: str = ""
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost including miles and fees"""
        return self.total_miles + self.total_fees
    
    @property
    def route_description(self) -> str:
        """Get human-readable route description"""
        if self.route_type == 'direct':
            return f"{self.origin} → {self.destination}"
        else:
            stops = " → ".join([self.origin] + self.layover_airports + [self.destination])
            return stops


class RouteOptimizer:
    """
    Optimizer for finding the best flight routes including synthetic routing.
    
    This class provides methods to find direct routes, generate layover options,
    and calculate the value of different routing strategies using real Amadeus API data.
    """
    
    def __init__(self, amadeus_client: Optional[AmadeusClient] = None):
        """Initialize the route optimizer with Amadeus client"""
        self.major_hubs = ['ATL', 'DFW', 'ORD', 'LAX', 'JFK', 'LHR', 'CDG', 'NRT', 'HKG', 'SIN']
        self.regional_hubs = ['DEN', 'MIA', 'SEA', 'SFO', 'BOS', 'IAH', 'MSP', 'DTW', 'PHX', 'LAS']
        self.all_hubs = self.major_hubs + self.regional_hubs
        
        # Initialize Amadeus client
        self.amadeus_client = amadeus_client or AmadeusClient()
        
        # Load mock award chart data
        self.award_charts = self._load_award_charts()
    
    def _load_award_charts(self) -> Dict[str, Any]:
        """Load mock award chart data for different airlines"""
        return {
            'domestic': {
                'zone_1': 7500,   # 0-500 miles
                'zone_2': 12500,  # 501-1000 miles
                'zone_3': 20000,  # 1001-1500 miles
                'zone_4': 25000,  # 1501-2000 miles
                'zone_5': 35000,  # 2001+ miles
            },
            'international': {
                'zone_1': 30000,  # North America
                'zone_2': 40000,  # Europe
                'zone_3': 50000,  # Asia
                'zone_4': 60000,  # South America
                'zone_5': 70000,  # Africa/Oceania
            }
        }
    
    def _calculate_distance(self, origin: str, destination: str) -> int:
        """
        Mock distance calculation between airports.
        In a real implementation, this would use actual airport coordinates.
        """
        # Simplified distance calculation for demo purposes
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
        
        # Check both directions
        route = (origin, destination)
        reverse_route = (destination, origin)
        
        if route in distances:
            return distances[route]
        elif reverse_route in distances:
            return distances[reverse_route]
        else:
            # Default distance calculation (very rough approximation)
            return 1000
    
    def _get_award_cost(self, origin: str, destination: str, is_international: bool = False) -> int:
        """
        Get award miles cost based on distance and route type.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            is_international: Whether this is an international route
            
        Returns:
            Award miles cost
        """
        distance = self._calculate_distance(origin, destination)
        
        if is_international:
            chart = self.award_charts['international']
            if distance < 2000:
                return chart['zone_1']
            elif distance < 4000:
                return chart['zone_2']
            elif distance < 6000:
                return chart['zone_3']
            elif distance < 8000:
                return chart['zone_4']
            else:
                return chart['zone_5']
        else:
            chart = self.award_charts['domestic']
            if distance <= 500:
                return chart['zone_1']
            elif distance <= 1000:
                return chart['zone_2']
            elif distance <= 1500:
                return chart['zone_3']
            elif distance <= 2000:
                return chart['zone_4']
            else:
                return chart['zone_5']
    
    def find_direct_routes(self, origin: str, destination: str, 
                          travel_date: date) -> List[FlightRoute]:
        """
        Find direct flight routes between origin and destination using Amadeus API.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            travel_date: Date of travel
            
        Returns:
            List of direct flight routes
        """
        direct_routes = []
        
        # Search for real flights using Amadeus API
        flight_offers = self.amadeus_client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=travel_date,
            max_offers=5
        )
        
        for offer in flight_offers:
            # Only include direct flights (0 stops)
            if offer.stops == 0:
                # Calculate award miles cost
                distance = self._calculate_distance(origin, destination)
                is_international = distance > 2000
                award_cost = self._get_award_cost(origin, destination, is_international)
                
                # Convert duration string to hours
                duration_hours = self._parse_duration(offer.duration)
                
                direct_routes.append(FlightRoute(
                    origin=origin,
                    destination=destination,
                    route_type='direct',
                    total_miles=award_cost,
                    total_fees=50.0,  # Mock fees
                    segments=offer.segments,
                    duration_hours=duration_hours,
                    layover_airports=[],
                    cash_price=offer.price,
                    airline=offer.airline
                ))
        
        return direct_routes
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse ISO 8601 duration string to hours."""
        try:
            # Remove 'PT' prefix and parse hours
            if duration_str.startswith('PT'):
                duration_str = duration_str[2:]
            
            hours = 0
            if 'H' in duration_str:
                hours = int(duration_str.split('H')[0])
            
            return float(hours)
        except:
            return 5.0  # Default duration
    
    def find_layover_routes(self, origin: str, destination: str, 
                           travel_date: date, 
                           hub_airports: Optional[List[str]] = None) -> List[FlightRoute]:
        """
        Find routes with layovers through major hub airports.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            travel_date: Date of travel
            hub_airports: List of hub airports to consider (defaults to major hubs)
            
        Returns:
            List of layover flight routes
        """
        if hub_airports is None:
            hub_airports = self.major_hubs[:3]  # Limit to top 3 hubs for performance
        
        layover_routes = []
        
        for hub in hub_airports:
            # Skip if hub is the same as origin or destination
            if hub in [origin, destination]:
                continue
            
            # Search for real flights to hub
            segment1_offers = self.amadeus_client.search_flights(
                origin=origin,
                destination=hub,
                departure_date=travel_date,
                max_offers=1
            )
            
            # Search for real flights from hub to destination
            segment2_offers = self.amadeus_client.search_flights(
                origin=hub,
                destination=destination,
                departure_date=travel_date,
                max_offers=1
            )
            
            if segment1_offers and segment2_offers:
                segment1 = segment1_offers[0]
                segment2 = segment2_offers[0]
                
                # Calculate costs for each segment
                segment1_cost = self._get_award_cost(origin, hub)
                segment2_cost = self._get_award_cost(hub, destination)
                
                # Total cost is sum of both segments
                total_miles = segment1_cost + segment2_cost
                total_fees = 75.0  # Higher fees for layover routes
                
                # Calculate total duration
                duration1 = self._parse_duration(segment1.duration)
                duration2 = self._parse_duration(segment2.duration)
                total_duration = duration1 + duration2 + 2.0  # Add 2 hours for layover
                
                # Combine segments
                combined_segments = segment1.segments + segment2.segments
                
                layover_routes.append(FlightRoute(
                    origin=origin,
                    destination=destination,
                    route_type='layover',
                    total_miles=total_miles,
                    total_fees=total_fees,
                    segments=combined_segments,
                    duration_hours=total_duration,
                    layover_airports=[hub],
                    cash_price=segment1.price + segment2.price,
                    airline=f"{segment1.airline}/{segment2.airline}"
                ))
        
        return layover_routes
    
    def calculate_synthetic_savings(self, direct_cost: float, layover_cost: float) -> Dict[str, Any]:
        """
        Calculate potential savings from synthetic routing.
        
        Args:
            direct_cost: Cost of direct route (miles + fees)
            layover_cost: Cost of layover route (miles + fees)
            
        Returns:
            Dictionary with savings analysis
        """
        savings = direct_cost - layover_cost
        savings_percentage = (savings / direct_cost) * 100 if direct_cost > 0 else 0
        
        return {
            'direct_cost': direct_cost,
            'layover_cost': layover_cost,
            'savings': savings,
            'savings_percentage': savings_percentage,
            'is_worthwhile': savings > 0 and savings_percentage > 10  # 10% threshold
        }
    
    def rank_routes_by_value(self, routes_list: List[FlightRoute]) -> List[Dict[str, Any]]:
        """
        Rank routes by value (lowest cost first).
        
        Args:
            routes_list: List of FlightRoute objects
            
        Returns:
            List of ranked routes with value analysis
        """
        ranked_routes = []
        
        for route in routes_list:
            # Calculate value metrics
            value_analysis = {
                'route': route,
                'total_cost': route.total_cost,
                'cost_per_mile': route.total_miles / route.duration_hours if route.duration_hours > 0 else 0,
                'efficiency_score': 1000 / route.total_cost if route.total_cost > 0 else 0,  # Higher is better
                'complexity_penalty': len(route.segments) * 0.1  # Penalty for more segments
            }
            
            # Adjust efficiency score for complexity
            value_analysis['final_score'] = value_analysis['efficiency_score'] - value_analysis['complexity_penalty']
            
            ranked_routes.append(value_analysis)
        
        # Sort by final score (highest first)
        ranked_routes.sort(key=lambda x: x['final_score'], reverse=True)
        
        return ranked_routes
    
    def find_optimal_routes(self, origin: str, destination: str, 
                           travel_date: date, max_routes: int = 5) -> Dict[str, Any]:
        """
        Find the optimal routes combining direct and layover options using real Amadeus data.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            travel_date: Date of travel
            max_routes: Maximum number of routes to return
            
        Returns:
            Dictionary with optimal routes and analysis
        """
        print(f"🔍 Searching for flights from {origin} to {destination} on {travel_date}")
        
        # Find direct routes using Amadeus API
        direct_routes = self.find_direct_routes(origin, destination, travel_date)
        print(f"Found {len(direct_routes)} direct routes")
        
        # Find layover routes using Amadeus API
        layover_routes = self.find_layover_routes(origin, destination, travel_date)
        print(f"Found {len(layover_routes)} layover routes")
        
        # Combine all routes
        all_routes = direct_routes + layover_routes
        
        if not all_routes:
            return {
                'routes': [],
                'best_route': None,
                'savings_opportunities': [],
                'message': 'No routes available for the specified criteria.'
            }
        
        # Rank routes by value
        ranked_routes = self.rank_routes_by_value(all_routes)
        
        # Limit to max_routes
        top_routes = ranked_routes[:max_routes]
        
        # Find savings opportunities
        savings_opportunities = []
        if len(direct_routes) > 0 and len(layover_routes) > 0:
            direct_cost = direct_routes[0].total_cost
            for layover_route in layover_routes:
                savings = self.calculate_synthetic_savings(direct_cost, layover_route.total_cost)
                if savings['is_worthwhile']:
                    savings_opportunities.append({
                        'layover_route': layover_route,
                        'savings_analysis': savings
                    })
        
        return {
            'routes': top_routes,
            'best_route': top_routes[0] if top_routes else None,
            'savings_opportunities': savings_opportunities,
            'total_routes_found': len(all_routes),
            'direct_routes_count': len(direct_routes),
            'layover_routes_count': len(layover_routes)
        } 
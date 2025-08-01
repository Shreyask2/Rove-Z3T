"""
Part 3: Recommendation Engine

Core functionality to generate comprehensive redemption recommendations
combining flights, hotels, and alternative redemption options with Amadeus API integration.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
import json

from .calculator import RedemptionCalculator, RedemptionOption
from .route_optimizer import RouteOptimizer, FlightRoute
from .amadeus_client import AmadeusClient


@dataclass
class UserPreferences:
    """Data class to represent user preferences"""
    maximize_value: bool = True
    minimize_fees: bool = False
    prefer_direct_flights: bool = True
    max_layovers: int = 1
    hotel_preference: str = "any"  # "any", "luxury", "budget", "mid-range"
    include_alternatives: bool = True
    min_value_per_mile: float = 1.0


class RedemptionRecommender:
    """
    Comprehensive recommendation engine for redemption optimization.
    
    This class combines flight routing, hotel options, and alternative
    redemptions to provide the best overall recommendations using real Amadeus API data.
    """
    
    def __init__(self, amadeus_client: Optional[AmadeusClient] = None):
        """Initialize the recommender with calculator and route optimizer"""
        self.calculator = RedemptionCalculator()
        self.amadeus_client = amadeus_client or AmadeusClient()
        self.route_optimizer = RouteOptimizer(self.amadeus_client)
        self.hotel_data = self._load_hotel_data()
        self.alternative_data = self._load_alternative_data()
    
    def _load_hotel_data(self) -> Dict[str, Any]:
        """Load mock hotel redemption data"""
        return {
            'marriott': {
                'category_1': {'points': 7500, 'cash_value': 75},
                'category_2': {'points': 12500, 'cash_value': 125},
                'category_3': {'points': 17500, 'cash_value': 175},
                'category_4': {'points': 25000, 'cash_value': 250},
                'category_5': {'points': 35000, 'cash_value': 350},
                'category_6': {'points': 50000, 'cash_value': 500},
                'category_7': {'points': 70000, 'cash_value': 700},
                'category_8': {'points': 100000, 'cash_value': 1000},
            },
            'hilton': {
                'category_1': {'points': 10000, 'cash_value': 60},
                'category_2': {'points': 20000, 'cash_value': 120},
                'category_3': {'points': 30000, 'cash_value': 180},
                'category_4': {'points': 40000, 'cash_value': 240},
                'category_5': {'points': 50000, 'cash_value': 300},
                'category_6': {'points': 60000, 'cash_value': 360},
                'category_7': {'points': 70000, 'cash_value': 420},
                'category_8': {'points': 80000, 'cash_value': 480},
            },
            'hyatt': {
                'category_1': {'points': 3500, 'cash_value': 70},
                'category_2': {'points': 6500, 'cash_value': 130},
                'category_3': {'points': 9000, 'cash_value': 180},
                'category_4': {'points': 12000, 'cash_value': 240},
                'category_5': {'points': 17000, 'cash_value': 340},
                'category_6': {'points': 21000, 'cash_value': 420},
                'category_7': {'points': 25000, 'cash_value': 500},
                'category_8': {'points': 30000, 'cash_value': 600},
            }
        }
    
    def _load_alternative_data(self) -> Dict[str, Any]:
        """Load mock alternative redemption data"""
        return {
            'gift_cards': {
                'amazon': {'points': 10000, 'value': 100},
                'target': {'points': 10000, 'value': 100},
                'walmart': {'points': 10000, 'value': 100},
                'starbucks': {'points': 10000, 'value': 100},
                'uber': {'points': 10000, 'value': 100},
            },
            'transfers': {
                'chase_ur_to_hyatt': {'ratio': 1.0, 'bonus': 0.25},
                'chase_ur_to_marriott': {'ratio': 1.0, 'bonus': 0.0},
                'amex_mr_to_hilton': {'ratio': 1.0, 'bonus': 0.0},
                'amex_mr_to_marriott': {'ratio': 1.0, 'bonus': 0.0},
            },
            'statement_credits': {
                'chase_pay_yourself_back': {'value_per_point': 1.25},
                'amex_statement_credit': {'value_per_point': 0.6},
            }
        }
    
    def get_flight_options(self, origin: str, destination: str, 
                          travel_date: date, available_miles: int) -> List[Dict[str, Any]]:
        """
        Get available flight options for the given route using Amadeus API.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            travel_date: Date of travel
            available_miles: Available miles for redemption
            
        Returns:
            List of flight options with value analysis
        """
        print(f"✈️ Searching for flight options from {origin} to {destination}")
        
        # Get optimal routes using Amadeus API
        route_results = self.route_optimizer.find_optimal_routes(origin, destination, travel_date)
        
        flight_options = []
        
        for route_analysis in route_results['routes']:
            route = route_analysis['route']
            
            # Check if user has enough miles
            if route.total_miles <= available_miles:
                # Use real cash price from Amadeus API
                cash_price = route.cash_price if route.cash_price > 0 else route.total_miles * 0.02
                
                # Calculate value
                value_calc = self.calculator.calculate_flight_value(
                    route.total_miles, 
                    cash_price,
                    route.total_fees
                )
                
                flight_options.append({
                    'type': 'flight',
                    'subtype': route.route_type,
                    'cost_miles': route.total_miles,
                    'cash_equivalent': value_calc['cash_price'],
                    'fees': route.total_fees,
                    'value_per_mile': value_calc['value_per_mile'],
                    'route': route.route_description,
                    'savings_vs_cash': value_calc['savings_vs_cash'],
                    'duration_hours': route.duration_hours,
                    'segments': route.segments,
                    'airline': route.airline,
                    'is_affordable': True
                })
        
        print(f"Found {len(flight_options)} affordable flight options")
        return flight_options
    
    def get_hotel_options(self, destination: str, available_points: int, 
                         preferences: UserPreferences) -> List[Dict[str, Any]]:
        """
        Get available hotel options for the destination.
        
        Args:
            destination: Destination city/airport
            available_points: Available points for redemption
            preferences: User preferences for hotel selection
            
        Returns:
            List of hotel options with value analysis
        """
        print(f"🏨 Searching for hotel options in {destination}")
        
        hotel_options = []
        
        # Generate mock hotel options based on available chains
        for chain, categories in self.hotel_data.items():
            for category, data in categories.items():
                if data['points'] <= available_points:
                    # Calculate value
                    value_calc = self.calculator.calculate_hotel_value(
                        data['points'],
                        data['cash_value']
                    )
                    
                    hotel_options.append({
                        'type': 'hotel',
                        'chain': chain,
                        'category': category,
                        'cost_points': data['points'],
                        'cash_equivalent': data['cash_value'],
                        'fees': 0.0,
                        'value_per_point': value_calc['value_per_point'],
                        'location': destination,
                        'savings_vs_cash': value_calc['savings_vs_cash'],
                        'is_affordable': True
                    })
        
        # Sort by value per point
        hotel_options.sort(key=lambda x: x['value_per_point'], reverse=True)
        
        print(f"Found {len(hotel_options)} affordable hotel options")
        return hotel_options[:5]  # Return top 5 options
    
    def get_alternative_redemptions(self, available_points: int) -> List[Dict[str, Any]]:
        """
        Get alternative redemption options.
        
        Args:
            available_points: Available points for redemption
            
        Returns:
            List of alternative redemption options
        """
        print("🎁 Searching for alternative redemption options")
        
        alternative_options = []
        
        # Gift card options
        for merchant, data in self.alternative_data['gift_cards'].items():
            if data['points'] <= available_points:
                value_calc = self.calculator.calculate_giftcard_value(
                    data['points'],
                    data['value']
                )
                
                alternative_options.append({
                    'type': 'giftcard',
                    'merchant': merchant,
                    'cost_points': data['points'],
                    'cash_equivalent': data['value'],
                    'fees': 0.0,
                    'value_per_point': value_calc['value_per_point'],
                    'savings_vs_cash': value_calc['savings_vs_cash'],
                    'is_affordable': True
                })
        
        # Statement credit options
        for program, data in self.alternative_data['statement_credits'].items():
            # Mock points requirement
            points_required = 10000
            if points_required <= available_points:
                cash_value = points_required * data['value_per_point'] / 100
                
                alternative_options.append({
                    'type': 'statement_credit',
                    'program': program,
                    'cost_points': points_required,
                    'cash_equivalent': cash_value,
                    'fees': 0.0,
                    'value_per_point': data['value_per_point'],
                    'savings_vs_cash': cash_value,
                    'is_affordable': True
                })
        
        print(f"Found {len(alternative_options)} alternative redemption options")
        return alternative_options
    
    def generate_recommendations(self, origin_airport: str, destination_airport: str,
                                travel_date: date, available_miles: int,
                                user_preferences: Optional[UserPreferences] = None) -> Dict[str, Any]:
        """
        Generate comprehensive redemption recommendations using Amadeus API data.
        
        Args:
            origin_airport: Origin airport code
            destination_airport: Destination airport code
            travel_date: Date of travel
            available_miles: Available miles/points
            user_preferences: User preferences for optimization
            
        Returns:
            Dictionary with comprehensive recommendations
        """
        if user_preferences is None:
            user_preferences = UserPreferences()
        
        print(f"\n🚀 Generating recommendations for {available_miles:,} miles")
        
        # Get all available options
        flight_options = self.get_flight_options(origin_airport, destination_airport, 
                                                travel_date, available_miles)
        
        hotel_options = self.get_hotel_options(destination_airport, available_miles, 
                                              user_preferences)
        
        alternative_options = []
        if user_preferences.include_alternatives:
            alternative_options = self.get_alternative_redemptions(available_miles)
        
        # Combine all options
        all_options = flight_options + hotel_options + alternative_options
        
        print(f"Total options found: {len(all_options)}")
        
        # Filter by minimum value threshold
        filtered_options = [
            option for option in all_options 
            if option.get('value_per_mile', option.get('value_per_point', 0)) >= user_preferences.min_value_per_mile
        ]
        
        print(f"Options meeting minimum value threshold: {len(filtered_options)}")
        
        # Sort by value (highest first)
        if user_preferences.maximize_value:
            filtered_options.sort(key=lambda x: x.get('value_per_mile', x.get('value_per_point', 0)), reverse=True)
        elif user_preferences.minimize_fees:
            filtered_options.sort(key=lambda x: x.get('fees', 0))
        
        # Limit to top 5 recommendations
        top_recommendations = filtered_options[:5]
        
        # Find best overall and best value per mile
        best_overall = top_recommendations[0] if top_recommendations else None
        best_value_per_mile = None
        
        if top_recommendations:
            best_value_per_mile = max(top_recommendations, 
                                    key=lambda x: x.get('value_per_mile', x.get('value_per_point', 0)))
        
        # Generate summary statistics
        total_options_found = len(all_options)
        affordable_options = len([opt for opt in all_options if opt.get('is_affordable', False)])
        
        return {
            'recommendations': top_recommendations,
            'best_overall': best_overall,
            'best_value_per_mile': best_value_per_mile,
            'summary': {
                'total_options_found': total_options_found,
                'affordable_options': affordable_options,
                'recommendations_generated': len(top_recommendations),
                'average_value_per_mile': sum(opt.get('value_per_mile', opt.get('value_per_point', 0)) 
                                            for opt in top_recommendations) / len(top_recommendations) if top_recommendations else 0
            },
            'search_criteria': {
                'origin': origin_airport,
                'destination': destination_airport,
                'travel_date': travel_date.isoformat(),
                'available_miles': available_miles,
                'preferences': {
                    'maximize_value': user_preferences.maximize_value,
                    'minimize_fees': user_preferences.minimize_fees,
                    'include_alternatives': user_preferences.include_alternatives
                }
            }
        }
    
    def get_insufficient_miles_recommendations(self, available_miles: int, 
                                             required_miles: int) -> Dict[str, Any]:
        """
        Generate recommendations when user has insufficient miles.
        
        Args:
            available_miles: Available miles
            required_miles: Required miles for desired redemption
            
        Returns:
            Dictionary with alternative recommendations
        """
        miles_short = required_miles - available_miles
        
        return {
            'type': 'insufficient_miles',
            'available_miles': available_miles,
            'required_miles': required_miles,
            'miles_short': miles_short,
            'recommendations': [
                {
                    'type': 'earn_more_miles',
                    'description': f'You need {miles_short:,} more miles',
                    'suggestions': [
                        'Apply for a new credit card with sign-up bonus',
                        'Use shopping portals for bonus miles',
                        'Dine at partner restaurants',
                        'Transfer points from other programs'
                    ]
                },
                {
                    'type': 'alternative_redemption',
                    'description': 'Consider alternative redemptions with your current miles',
                    'options': self.get_alternative_redemptions(available_miles)
                }
            ]
        } 
"""
Part 1: Value Calculator

Core functionality to calculate the value of different redemption options
and compare them to find the best value-per-mile/point.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RedemptionOption:
    """Data class to represent a redemption option"""
    type: str
    name: str
    miles_cost: int
    cash_equivalent: float
    taxes_fees: float = 0.0
    description: str = ""
    
    @property
    def net_cash_value(self) -> float:
        """Calculate net cash value after fees"""
        return self.cash_equivalent - self.taxes_fees
    
    @property
    def value_per_mile(self) -> float:
        """Calculate cents per mile/point"""
        if self.miles_cost <= 0:
            return 0.0
        return (self.net_cash_value / self.miles_cost) * 100


class RedemptionCalculator:
    """
    Core calculator for determining the value of different redemption options.
    
    This class provides methods to calculate the value-per-mile for flights,
    hotels, gift cards, and other redemption options.
    """
    
    def __init__(self):
        """Initialize the calculator with default values"""
        self.minimum_value_threshold = 0.5  # Minimum cents per mile to consider "good" value
    
    def calculate_flight_value(self, miles_cost: int, cash_price: float, 
                             taxes_fees: float = 0.0) -> Dict[str, Any]:
        """
        Calculate the value of a flight redemption.
        
        Args:
            miles_cost: Number of miles/points required
            cash_price: Cash price of the flight
            taxes_fees: Taxes and fees associated with the redemption
            
        Returns:
            Dictionary containing value calculations
        """
        net_value = cash_price - taxes_fees
        value_per_mile = (net_value / miles_cost) * 100 if miles_cost > 0 else 0
        
        return {
            'type': 'flight',
            'miles_cost': miles_cost,
            'cash_price': cash_price,
            'taxes_fees': taxes_fees,
            'net_value': net_value,
            'value_per_mile': value_per_mile,
            'is_good_value': value_per_mile >= self.minimum_value_threshold,
            'savings_vs_cash': net_value
        }
    
    def calculate_hotel_value(self, points_cost: int, cash_price: float, 
                            taxes_fees: float = 0.0) -> Dict[str, Any]:
        """
        Calculate the value of a hotel redemption.
        
        Args:
            points_cost: Number of points required
            cash_price: Cash price of the hotel stay
            taxes_fees: Taxes and fees associated with the redemption
            
        Returns:
            Dictionary containing value calculations
        """
        net_value = cash_price - taxes_fees
        value_per_point = (net_value / points_cost) * 100 if points_cost > 0 else 0
        
        return {
            'type': 'hotel',
            'points_cost': points_cost,
            'cash_price': cash_price,
            'taxes_fees': taxes_fees,
            'net_value': net_value,
            'value_per_point': value_per_point,
            'is_good_value': value_per_point >= self.minimum_value_threshold,
            'savings_vs_cash': net_value
        }
    
    def calculate_giftcard_value(self, points_cost: int, giftcard_value: float) -> Dict[str, Any]:
        """
        Calculate the value of a gift card redemption.
        
        Args:
            points_cost: Number of points required
            giftcard_value: Value of the gift card
            
        Returns:
            Dictionary containing value calculations
        """
        value_per_point = (giftcard_value / points_cost) * 100 if points_cost > 0 else 0
        
        return {
            'type': 'giftcard',
            'points_cost': points_cost,
            'giftcard_value': giftcard_value,
            'taxes_fees': 0.0,
            'net_value': giftcard_value,
            'value_per_point': value_per_point,
            'is_good_value': value_per_point >= self.minimum_value_threshold,
            'savings_vs_cash': giftcard_value
        }
    
    def compare_redemptions(self, redemption_options: List[RedemptionOption]) -> List[Dict[str, Any]]:
        """
        Compare multiple redemption options and rank them by value.
        
        Args:
            redemption_options: List of RedemptionOption objects
            
        Returns:
            List of dictionaries with ranked options by value-per-mile/point
        """
        comparisons = []
        
        for option in redemption_options:
            if option.type == 'flight':
                calc_result = self.calculate_flight_value(
                    option.miles_cost, option.cash_equivalent, option.taxes_fees
                )
            elif option.type == 'hotel':
                calc_result = self.calculate_hotel_value(
                    option.miles_cost, option.cash_equivalent, option.taxes_fees
                )
            elif option.type == 'giftcard':
                calc_result = self.calculate_giftcard_value(
                    option.miles_cost, option.cash_equivalent
                )
            else:
                continue
            
            comparisons.append({
                'option': option,
                'calculation': calc_result,
                'value_per_unit': calc_result.get('value_per_mile', calc_result.get('value_per_point', 0))
            })
        
        # Sort by value per mile/point (highest first)
        comparisons.sort(key=lambda x: x['value_per_unit'], reverse=True)
        
        return comparisons
    
    def get_value_rating(self, value_per_mile: float) -> str:
        """
        Get a human-readable rating for the value.
        
        Args:
            value_per_mile: Cents per mile/point
            
        Returns:
            String rating (Excellent, Good, Fair, Poor)
        """
        if value_per_mile >= 2.0:
            return "Excellent"
        elif value_per_mile >= 1.5:
            return "Good"
        elif value_per_mile >= 1.0:
            return "Fair"
        else:
            return "Poor"
    
    def analyze_sample_data(self) -> Dict[str, Any]:
        """
        Analyze the sample data provided in the requirements.
        
        Returns:
            Dictionary with analysis of sample redemption options
        """
        sample_options = [
            RedemptionOption(
                type='flight',
                name='JFK to LAX Direct',
                miles_cost=25000,
                cash_equivalent=400,
                taxes_fees=50,
                description='American Airlines direct flight'
            ),
            RedemptionOption(
                type='hotel',
                name='Marriott Hotel Night',
                miles_cost=30000,
                cash_equivalent=300,
                taxes_fees=0,
                description='Marriott Bonvoy redemption'
            ),
            RedemptionOption(
                type='giftcard',
                name='Amazon Gift Card',
                miles_cost=10000,
                cash_equivalent=100,
                taxes_fees=0,
                description='Amazon gift card redemption'
            )
        ]
        
        comparisons = self.compare_redemptions(sample_options)
        
        return {
            'sample_analysis': comparisons,
            'best_value': comparisons[0] if comparisons else None,
            'worst_value': comparisons[-1] if comparisons else None,
            'average_value': sum(c['value_per_unit'] for c in comparisons) / len(comparisons) if comparisons else 0
        } 
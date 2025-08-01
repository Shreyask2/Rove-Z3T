#!/usr/bin/env python3
"""
Rewards Redemption Optimizer - Interactive Mode

This script provides an interactive interface for the Rewards Redemption Optimizer
with real Amadeus API integration for actual flight data and pricing.
"""

import json
import os
from datetime import date, datetime
from typing import Dict, Any
import sys

from redemption_optimizer.calculator import RedemptionCalculator, RedemptionOption
from redemption_optimizer.route_optimizer import RouteOptimizer
from redemption_optimizer.recommender import RedemptionRecommender, UserPreferences
from redemption_optimizer.amadeus_client import AmadeusClient


def print_header(title: str, width: int = 80):
    """Print a formatted header"""
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)


def print_subheader(title: str, width: int = 80):
    """Print a formatted subheader"""
    print("\n" + "-" * width)
    print(f" {title} ".center(width, "-"))
    print("-" * width)


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_miles(miles: int) -> str:
    """Format miles with commas"""
    return f"{miles:,}"


def setup_amadeus_api():
    """Guide user through Amadeus API setup"""
    print_header("AMADEUS API SETUP")
    print("To get real flight data, you need an Amadeus API key.")
    print("1. Go to: https://developers.amadeus.com/")
    print("2. Sign up for a free account")
    print("3. Create a new application to get your API key and secret")
    print("4. Set environment variables or enter them below")
    
    use_env = input("\nDo you have AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables set? (y/n): ").strip().lower()
    
    if use_env == 'y':
        if os.getenv('AMADEUS_API_KEY') and os.getenv('AMADEUS_API_SECRET'):
            print("✅ Environment variables found!")
            return None, None
        else:
            print("❌ Environment variables not found. Please enter your credentials:")
    
    api_key = input("Enter your Amadeus API Key: ").strip()
    api_secret = input("Enter your Amadeus API Secret: ").strip()
    
    if api_key and api_secret:
        return api_key, api_secret
    else:
        print("⚠️ No API credentials provided. Will use mock data.")
        return None, None


def get_user_input():
    print_header("INTERACTIVE REWARDS REDEMPTION OPTIMIZER")
    print("Enter your trip and points details below. Press Enter to use defaults in brackets.")
    
    origin = input("Origin airport code (e.g. JFK): ").strip().upper() or "JFK"
    destination = input("Destination airport code (e.g. LAX): ").strip().upper() or "LAX"
    date_str = input("Travel date (YYYY-MM-DD) [2024-06-15]: ").strip() or "2024-06-15"
    try:
        travel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        print("Invalid date format. Using default 2024-06-15.")
        travel_date = date(2024, 6, 15)
    
    try:
        available_miles = int(input("Available miles/points [50000]: ").strip() or "50000")
    except Exception:
        print("Invalid number. Using default 50000.")
        available_miles = 50000
    
    maximize_value = input("Maximize value? (y/n) [y]: ").strip().lower() or "y"
    minimize_fees = input("Minimize fees? (y/n) [n]: ").strip().lower() or "n"
    include_alternatives = input("Include alternative redemptions (gift cards, etc)? (y/n) [y]: ").strip().lower() or "y"
    try:
        min_value_per_mile = float(input("Minimum value per mile/point in cents [1.0]: ").strip() or "1.0")
    except Exception:
        min_value_per_mile = 1.0
    
    preferences = UserPreferences(
        maximize_value=(maximize_value == "y"),
        minimize_fees=(minimize_fees == "y"),
        include_alternatives=(include_alternatives == "y"),
        min_value_per_mile=min_value_per_mile
    )
    return origin, destination, travel_date, available_miles, preferences


def interactive_mode():
    # Setup Amadeus API
    api_key, api_secret = setup_amadeus_api()
    
    # Initialize components with Amadeus client
    amadeus_client = AmadeusClient(api_key, api_secret)
    recommender = RedemptionRecommender(amadeus_client)
    
    origin, destination, travel_date, available_miles, preferences = get_user_input()
    
    print_subheader(f"Searching for best redemptions: {origin} to {destination} on {travel_date}")
    
    try:
        recommendations = recommender.generate_recommendations(
            origin, destination, travel_date, available_miles, preferences
        )
        
        print(f"\n📊 Results Summary:")
        print(f"  • Total options found: {recommendations['summary']['total_options_found']}")
        print(f"  • Affordable options: {recommendations['summary']['affordable_options']}")
        print(f"  • Recommendations generated: {recommendations['summary']['recommendations_generated']}")
        print(f"  • Average value: {recommendations['summary']['average_value_per_mile']:.2f}¢ per mile/point")
        
        if recommendations['recommendations']:
            print("\n🏆 Top Recommendations:")
            for i, rec in enumerate(recommendations['recommendations'], 1):
                print(f"\n{i}. {rec['type'].title()} - {rec.get('subtype', rec.get('chain', rec.get('merchant', '')))}")
                print(f"   Cost: {format_miles(rec.get('cost_miles', rec.get('cost_points', 0)))} miles/points")
                print(f"   Cash Value: {format_currency(rec['cash_equivalent'])}")
                print(f"   Fees: {format_currency(rec['fees'])}")
                print(f"   Value: {rec.get('value_per_mile', rec.get('value_per_point', 0)):.2f}¢ per mile/point")
                print(f"   Savings: {format_currency(rec['savings_vs_cash'])}")
                
                if rec['type'] == 'flight':
                    print(f"   Route: {rec['route']}")
                    print(f"   Duration: {rec['duration_hours']:.1f} hours")
                    if rec.get('airline'):
                        print(f"   Airline: {rec['airline']}")
                elif rec['type'] == 'hotel':
                    print(f"   Location: {rec['location']}")
            
            print("\n🎯 Best Overall Option:")
            best = recommendations['best_overall']
            if best:
                print(f"{best['type'].title()} - {best.get('subtype', best.get('chain', best.get('merchant', '')))}")
                print(f"Value: {best.get('value_per_mile', best.get('value_per_point', 0)):.2f}¢ per mile/point")
                print(f"Savings: {format_currency(best['savings_vs_cash'])}")
            else:
                print("No best option found.")
        else:
            print("\n❌ No recommendations found. Try:")
            print("  • Increasing your available miles")
            print("  • Lowering your minimum value threshold")
            print("  • Checking different dates")
            print("  • Including alternative redemptions")
            
    except Exception as e:
        print(f"\n❌ Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()


def demo_part_1_value_calculator():
    """Demonstrate Part 1: Value Calculator"""
    print_header("PART 1: VALUE CALCULATOR")
    
    calculator = RedemptionCalculator()
    
    # Demo 1: Sample data analysis from requirements
    print_subheader("Sample Data Analysis (from requirements)")
    
    sample_analysis = calculator.analyze_sample_data()
    
    print("Sample redemption options and their values:")
    print(f"{'Option':<25} {'Miles/Points':<15} {'Cash Value':<15} {'Fees':<10} {'Value/Mile':<15} {'Rating':<10}")
    print("-" * 90)
    
    for comparison in sample_analysis['sample_analysis']:
        option = comparison['option']
        calc = comparison['calculation']
        rating = calculator.get_value_rating(calc.get('value_per_mile', calc.get('value_per_point', 0)))
        
        value = calc.get('value_per_mile', calc.get('value_per_point', 0))
        print(f"{option.name:<25} {format_miles(option.miles_cost):<15} "
              f"{format_currency(option.cash_equivalent):<15} "
              f"{format_currency(option.taxes_fees):<10} "
              f"{value:.2f}¢ {rating}")
    
    print(f"\nBest Value: {sample_analysis['best_value']['option'].name}")
    print(f"Average Value: {sample_analysis['average_value']:.2f}¢ per mile/point")
    
    # Demo 2: Custom redemption comparison
    print_subheader("Custom Redemption Comparison")
    
    custom_options = [
        RedemptionOption(
            type='flight',
            name='Premium Economy JFK-LHR',
            miles_cost=40000,
            cash_equivalent=1200,
            taxes_fees=200,
            description='British Airways premium economy'
        ),
        RedemptionOption(
            type='hotel',
            name='Ritz-Carlton Paris',
            miles_cost=70000,
            cash_equivalent=800,
            taxes_fees=0,
            description='Marriott luxury hotel'
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
    
    comparisons = calculator.compare_redemptions(custom_options)
    
    print("Custom redemption options ranked by value:")
    for i, comparison in enumerate(comparisons, 1):
        option = comparison['option']
        calc = comparison['calculation']
        rating = calculator.get_value_rating(calc.get('value_per_mile', calc.get('value_per_point', 0)))
        
        print(f"\n{i}. {option.name}")
        print(f"   Cost: {format_miles(option.miles_cost)} miles/points")
        print(f"   Cash Value: {format_currency(option.cash_equivalent)}")
        print(f"   Fees: {format_currency(option.taxes_fees)}")
        print(f"   Value: {calc.get('value_per_mile', calc.get('value_per_point', 0)):.2f}¢ per mile/point ({rating})")
        print(f"   Savings: {format_currency(calc['savings_vs_cash'])}")


def demo_part_2_route_optimizer():
    """Demonstrate Part 2: Route Optimizer"""
    print_header("PART 2: ROUTE OPTIMIZER")
    
    optimizer = RouteOptimizer()
    
    # Demo 1: NYC to LAX trip
    print_subheader("NYC to LAX Trip Analysis")
    
    origin = "JFK"
    destination = "LAX"
    travel_date = date(2024, 6, 15)
    
    print(f"Searching for routes from {origin} to {destination} on {travel_date}")
    
    # Find direct routes
    direct_routes = optimizer.find_direct_routes(origin, destination, travel_date)
    print(f"\nDirect routes found: {len(direct_routes)}")
    
    for route in direct_routes:
        print(f"  • {route.route_description}")
        print(f"    Miles: {format_miles(route.total_miles)}")
        print(f"    Fees: {format_currency(route.total_fees)}")
        print(f"    Total Cost: {format_currency(route.total_cost)}")
        print(f"    Duration: {route.duration_hours:.1f} hours")
    
    # Find layover routes
    layover_routes = optimizer.find_layover_routes(origin, destination, travel_date)
    print(f"\nLayover routes found: {len(layover_routes)}")
    
    for route in layover_routes:
        print(f"  • {route.route_description}")
        print(f"    Miles: {format_miles(route.total_miles)}")
        print(f"    Fees: {format_currency(route.total_fees)}")
        print(f"    Total Cost: {format_currency(route.total_cost)}")
        print(f"    Duration: {route.duration_hours:.1f} hours")
    
    # Demo 2: Optimal routes analysis
    print_subheader("Optimal Routes Analysis")
    
    optimal_results = optimizer.find_optimal_routes(origin, destination, travel_date)
    
    print(f"Total routes found: {optimal_results['total_routes_found']}")
    print(f"Direct routes: {optimal_results['direct_routes_count']}")
    print(f"Layover routes: {optimal_results['layover_routes_count']}")
    
    if optimal_results['best_route']:
        best_route = optimal_results['best_route']['route']
        print(f"\nBest overall route: {best_route.route_description}")
        print(f"Total cost: {format_currency(best_route.total_cost)}")
        print(f"Efficiency score: {optimal_results['best_route']['final_score']:.2f}")
    
    # Demo 3: Synthetic savings analysis
    print_subheader("Synthetic Savings Analysis")
    
    if len(direct_routes) > 0 and len(layover_routes) > 0:
        direct_cost = direct_routes[0].total_cost
        
        for layover_route in layover_routes[:3]:  # Show top 3
            savings = optimizer.calculate_synthetic_savings(direct_cost, layover_route.total_cost)
            
            print(f"\nRoute: {layover_route.route_description}")
            print(f"Direct cost: {format_currency(savings['direct_cost'])}")
            print(f"Layover cost: {format_currency(savings['layover_cost'])}")
            print(f"Savings: {format_currency(savings['savings'])} ({savings['savings_percentage']:.1f}%)")
            print(f"Worthwhile: {'Yes' if savings['is_worthwhile'] else 'No'}")


def demo_part_3_recommendation_engine():
    """Demonstrate Part 3: Recommendation Engine"""
    print_header("PART 3: RECOMMENDATION ENGINE")
    
    recommender = RedemptionRecommender()
    
    # Demo 1: NYC to LAX with 50,000 miles
    print_subheader("NYC to LAX Trip with 50,000 Miles")
    
    origin = "JFK"
    destination = "LAX"
    travel_date = date(2024, 6, 15)
    available_miles = 50000
    
    # Default preferences
    preferences = UserPreferences(
        maximize_value=True,
        minimize_fees=False,
        prefer_direct_flights=True,
        include_alternatives=True,
        min_value_per_mile=1.0
    )
    
    print(f"Searching for recommendations:")
    print(f"  Origin: {origin}")
    print(f"  Destination: {destination}")
    print(f"  Travel Date: {travel_date}")
    print(f"  Available Miles: {format_miles(available_miles)}")
    print(f"  Preferences: Maximize value, include alternatives")
    
    recommendations = recommender.generate_recommendations(
        origin, destination, travel_date, available_miles, preferences
    )
    
    print(f"\nFound {recommendations['summary']['total_options_found']} total options")
    print(f"Generated {recommendations['summary']['recommendations_generated']} recommendations")
    print(f"Average value: {recommendations['summary']['average_value_per_mile']:.2f}¢ per mile/point")
    
    print("\nTop Recommendations:")
    for i, rec in enumerate(recommendations['recommendations'], 1):
        print(f"\n{i}. {rec['type'].title()} - {rec.get('subtype', rec.get('chain', rec.get('merchant', '')))}")
        print(f"   Cost: {format_miles(rec.get('cost_miles', rec.get('cost_points', 0)))} miles/points")
        print(f"   Cash Value: {format_currency(rec['cash_equivalent'])}")
        print(f"   Fees: {format_currency(rec['fees'])}")
        print(f"   Value: {rec.get('value_per_mile', rec.get('value_per_point', 0)):.2f}¢ per mile/point")
        print(f"   Savings: {format_currency(rec['savings_vs_cash'])}")
        
        if rec['type'] == 'flight':
            print(f"   Route: {rec['route']}")
            print(f"   Duration: {rec['duration_hours']:.1f} hours")
        elif rec['type'] == 'hotel':
            print(f"   Location: {rec['location']}")
    
    # Demo 2: Insufficient miles scenario
    print_subheader("Insufficient Miles Scenario")
    
    insufficient_miles = 15000
    required_miles = 25000
    
    print(f"Available miles: {format_miles(insufficient_miles)}")
    print(f"Required miles: {format_miles(required_miles)}")
    
    insufficient_recs = recommender.get_insufficient_miles_recommendations(
        insufficient_miles, required_miles
    )
    
    print(f"\nMiles short: {format_miles(insufficient_recs['miles_short'])}")
    print("\nRecommendations:")
    
    for rec in insufficient_recs['recommendations']:
        print(f"\n{rec['type'].replace('_', ' ').title()}:")
        print(f"  {rec['description']}")
        
        if 'suggestions' in rec:
            for suggestion in rec['suggestions']:
                print(f"  • {suggestion}")
        
        if 'options' in rec:
            print("  Alternative redemption options:")
            for option in rec['options'][:3]:  # Show top 3
                print(f"    • {option['merchant']} gift card: {format_currency(option['cash_equivalent'])}")


def demo_integration():
    """Demonstrate integration between all three parts"""
    print_header("INTEGRATION DEMO: COMPLETE WORKFLOW")
    
    # Create instances of all components
    calculator = RedemptionCalculator()
    optimizer = RouteOptimizer()
    recommender = RedemptionRecommender()
    
    # Scenario: User wants to optimize their 75,000 miles for a trip
    print_subheader("Complete Optimization Workflow")
    
    origin = "JFK"
    destination = "LAX"
    travel_date = date(2024, 6, 15)
    available_miles = 75000
    
    print(f"User has {format_miles(available_miles)} miles for {origin} to {destination}")
    
    # Step 1: Find optimal routes
    print("\nStep 1: Finding optimal routes...")
    route_results = optimizer.find_optimal_routes(origin, destination, travel_date)
    
    # Step 2: Generate comprehensive recommendations
    print("Step 2: Generating recommendations...")
    preferences = UserPreferences(maximize_value=True, include_alternatives=True)
    recommendations = recommender.generate_recommendations(
        origin, destination, travel_date, available_miles, preferences
    )
    
    # Step 3: Analyze and present results
    print("Step 3: Analyzing results...")
    
    print(f"\nRoute Analysis:")
    print(f"  • Total routes found: {route_results['total_routes_found']}")
    print(f"  • Direct routes: {route_results['direct_routes_count']}")
    print(f"  • Layover routes: {route_results['layover_routes_count']}")
    
    print(f"\nRecommendation Analysis:")
    print(f"  • Total options: {recommendations['summary']['total_options_found']}")
    print(f"  • Affordable options: {recommendations['summary']['affordable_options']}")
    print(f"  • Top recommendations: {recommendations['summary']['recommendations_generated']}")
    
    # Step 4: Present best options with detailed analysis
    print("\nStep 4: Best Options Analysis:")
    
    if recommendations['best_overall']:
        best = recommendations['best_overall']
        print(f"\n🏆 BEST OVERALL: {best['type'].title()}")
        print(f"   Value: {best.get('value_per_mile', best.get('value_per_point', 0)):.2f}¢ per mile/point")
        print(f"   Savings: {format_currency(best['savings_vs_cash'])}")
        
        if best['type'] == 'flight':
            print(f"   Route: {best['route']}")
        elif best['type'] == 'hotel':
            print(f"   Chain: {best['chain']} {best['category']}")
    
    if recommendations['best_value_per_mile']:
        best_value = recommendations['best_value_per_mile']
        print(f"\n💎 BEST VALUE PER MILE: {best_value['type'].title()}")
        print(f"   Value: {best_value.get('value_per_mile', best_value.get('value_per_point', 0)):.2f}¢ per mile/point")
        print(f"   Savings: {format_currency(best_value['savings_vs_cash'])}")


def main():
    """Main function"""
    print_header("REWARDS REDEMPTION OPTIMIZER - INTERACTIVE MODE")
    print("Choose your mode:")
    print("1. Interactive mode (recommended) - Enter your own trip details")
    print("2. Demo mode - See scripted examples")
    
    mode = input("\nMode [interactive/demo]: ").strip().lower()
    
    if mode == "demo":
        try:
            demo_part_1_value_calculator()
            demo_part_2_route_optimizer()
            demo_part_3_recommendation_engine()
            demo_integration()
            print_header("DEMO COMPLETE")
            print("\n✅ All three parts of the Rewards Redemption Optimizer are working!")
            print("\nKey Features Demonstrated:")
            print("• Value calculation for flights, hotels, and gift cards")
            print("• Direct and synthetic routing optimization")
            print("• Comprehensive recommendation generation")
            print("• Integration between all components")
            print("• Realistic mock data and edge case handling")
        except Exception as e:
            print(f"\n❌ Error during demo: {e}")
            import traceback
            traceback.print_exc()
    else:
        interactive_mode()


if __name__ == "__main__":
    main() 
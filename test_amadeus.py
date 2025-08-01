#!/usr/bin/env python3
"""
Test script to demonstrate Amadeus API integration
"""

import os
from datetime import date
from redemption_optimizer.amadeus_client import AmadeusClient
from redemption_optimizer.route_optimizer import RouteOptimizer
from redemption_optimizer.recommender import RedemptionRecommender, UserPreferences

def test_amadeus_integration():
    print("🚀 Testing Amadeus API Integration")
    print("=" * 50)
    
    # Set API credentials
    api_key = "atk652GGOfYtwMgnAoc9qCNW6D5mK7st"
    api_secret = "T5ZWIFuDaG703OI0"
    
    # Initialize Amadeus client
    print("📡 Initializing Amadeus client...")
    amadeus_client = AmadeusClient(api_key, api_secret)
    
    if amadeus_client.is_available():
        print("✅ Amadeus API client initialized successfully!")
    else:
        print("❌ Failed to initialize Amadeus client")
        return
    
    # Test flight search
    print("\n✈️ Testing flight search...")
    origin = "JFK"
    destination = "LAX"
    travel_date = date(2024, 6, 15)
    
    try:
        flight_offers = amadeus_client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=travel_date,
            max_offers=3
        )
        
        print(f"Found {len(flight_offers)} flight offers:")
        for i, offer in enumerate(flight_offers, 1):
            print(f"  {i}. {offer.airline} {offer.flight_number}")
            print(f"     Route: {offer.origin} → {offer.destination}")
            print(f"     Price: ${offer.price:.2f}")
            print(f"     Duration: {offer.duration}")
            print(f"     Stops: {offer.stops}")
            print(f"     Cabin: {offer.cabin_class}")
            print()
    
    except Exception as e:
        print(f"❌ Error searching flights: {e}")
        return
    
    # Test route optimization
    print("🛣️ Testing route optimization...")
    try:
        optimizer = RouteOptimizer(amadeus_client)
        route_results = optimizer.find_optimal_routes(
            origin=origin,
            destination=destination,
            travel_date=travel_date
        )
        
        print(f"Route analysis results:")
        print(f"  • Total routes found: {route_results['total_routes_found']}")
        print(f"  • Direct routes: {route_results['direct_routes_count']}")
        print(f"  • Layover routes: {route_results['layover_routes_count']}")
        
        if route_results['best_route']:
            best_route = route_results['best_route']['route']
            print(f"  • Best route: {best_route.route_description}")
            print(f"  • Total cost: ${best_route.total_cost:,.2f}")
    
    except Exception as e:
        print(f"❌ Error in route optimization: {e}")
        return
    
    # Test recommendation engine
    print("\n🎯 Testing recommendation engine...")
    try:
        recommender = RedemptionRecommender(amadeus_client)
        preferences = UserPreferences(
            maximize_value=True,
            include_alternatives=True,
            min_value_per_mile=1.0
        )
        
        recommendations = recommender.generate_recommendations(
            origin_airport=origin,
            destination_airport=destination,
            travel_date=travel_date,
            available_miles=50000,
            user_preferences=preferences
        )
        
        print(f"Recommendation results:")
        print(f"  • Total options found: {recommendations['summary']['total_options_found']}")
        print(f"  • Recommendations generated: {recommendations['summary']['recommendations_generated']}")
        print(f"  • Average value: {recommendations['summary']['average_value_per_mile']:.2f}¢ per mile/point")
        
        if recommendations['recommendations']:
            print("\nTop recommendations:")
            for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                print(f"  {i}. {rec['type'].title()} - {rec.get('subtype', rec.get('chain', rec.get('merchant', '')))}")
                print(f"     Value: {rec.get('value_per_mile', rec.get('value_per_point', 0)):.2f}¢ per mile/point")
                print(f"     Savings: ${rec['savings_vs_cash']:.2f}")
    
    except Exception as e:
        print(f"❌ Error in recommendation engine: {e}")
        return
    
    print("\n✅ Amadeus API integration test completed successfully!")

if __name__ == "__main__":
    test_amadeus_integration() 
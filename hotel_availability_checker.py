"""
Hotel Availability Checker for Viamigo Travel AI

This utility provides functions to check if hotel data is available for a given city.
Used by frontend to gracefully disable hotel features in cities without data.

Author: Viamigo Development Team
Date: November 7, 2025
"""

import psycopg2
import os
from typing import Dict, List, Optional


class HotelAvailabilityChecker:
    """Check hotel data availability for cities"""

    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")

    def get_connection(self):
        """Create database connection"""
        return psycopg2.connect(self.db_url)

    def get_available_cities(self) -> List[Dict[str, any]]:
        """
        Get list of all cities with hotel data

        Returns:
            List of dicts: [{"city": "Milan", "hotel_count": 161, "avg_rating": 8.4}, ...]
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            city,
            COUNT(*) as hotel_count,
            ROUND(AVG(average_score)::numeric, 1) as avg_rating,
            SUM(total_reviews) as total_reviews,
            COUNT(CASE WHEN average_score >= 9.0 THEN 1 END) as luxury_count,
            COUNT(CASE WHEN average_score >= 8.5 AND average_score < 9.0 THEN 1 END) as premium_count,
            COUNT(CASE WHEN average_score >= 8.0 AND average_score < 8.5 THEN 1 END) as mid_range_count,
            COUNT(CASE WHEN average_score >= 7.0 AND average_score < 8.0 THEN 1 END) as budget_count
        FROM hotel_reviews
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
        GROUP BY city
        ORDER BY hotel_count DESC;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        cities = []
        for row in rows:
            cities.append({
                "city": row[0],
                "hotel_count": row[1],
                "avg_rating": float(row[2]) if row[2] else 0.0,
                "total_reviews": row[3],
                "luxury_count": row[4],
                "premium_count": row[5],
                "mid_range_count": row[6],
                "budget_count": row[7]
            })

        cursor.close()
        conn.close()

        return cities

    def check_city_has_hotels(self, city: str) -> Dict[str, any]:
        """
        Check if a specific city has hotel data

        Args:
            city: City name (e.g., "Milan", "Rome", "Florence")

        Returns:
            Dict with availability info:
            {
                "available": True/False,
                "city": "Milan",
                "hotel_count": 161,
                "message": "Hotel data available" or "No hotels found"
            }
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            COUNT(*) as hotel_count,
            ROUND(AVG(average_score)::numeric, 1) as avg_rating
        FROM hotel_reviews
        WHERE LOWER(city) = LOWER(%s)
        AND latitude IS NOT NULL 
        AND longitude IS NOT NULL;
        """

        cursor.execute(query, (city,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        hotel_count = row[0] if row else 0
        avg_rating = float(row[1]) if row and row[1] else 0.0

        if hotel_count > 0:
            return {
                "available": True,
                "city": city,
                "hotel_count": hotel_count,
                "avg_rating": avg_rating,
                "message": f"Hotel data available for {city}"
            }
        else:
            # Get available cities for the message
            try:
                available_cities = self.get_available_cities()[:3]
                cities_str = ", ".join(
                    [c["city"] for c in available_cities if c and c.get("city")])
            except:
                cities_str = "Milan, Rome"

            return {
                "available": False,
                "city": city,
                "hotel_count": 0,
                "message": f"Hotel data not yet available for {city}. Currently supported cities: {cities_str}"
            }

    def get_city_name_variations(self, city: str) -> List[str]:
        """
        Get common variations of a city name

        Args:
            city: City name (e.g., "Milano" or "Milan")

        Returns:
            List of variations: ["Milan", "Milano"]
        """
        variations = {
            "Milan": ["Milan", "Milano"],
            "Milano": ["Milan", "Milano"],
            "Rome": ["Rome", "Roma"],
            "Roma": ["Rome", "Roma"],
            "Florence": ["Florence", "Firenze"],
            "Firenze": ["Florence", "Firenze"],
            "Venice": ["Venice", "Venezia"],
            "Venezia": ["Venice", "Venezia"],
            "Turin": ["Turin", "Torino"],
            "Torino": ["Turin", "Torino"],
            "Genoa": ["Genoa", "Genova"],
            "Genova": ["Genoa", "Genova"],
            "Naples": ["Naples", "Napoli"],
            "Napoli": ["Naples", "Napoli"]
        }

        return variations.get(city, [city])

    def find_city_in_database(self, city_query: str) -> Optional[str]:
        """
        Try to find a city in the database, checking all name variations

        Args:
            city_query: City name to search for

        Returns:
            Database city name if found, None otherwise
        """
        variations = self.get_city_name_variations(city_query)

        for variation in variations:
            result = self.check_city_has_hotels(variation)
            if result["available"]:
                return variation

        return None


# Standalone utility functions for easy import

def check_hotel_availability(city: str) -> Dict[str, any]:
    """
    Quick function to check if city has hotels

    Usage:
        from hotel_availability_checker import check_hotel_availability

        result = check_hotel_availability('Milan')
        if result['available']:
            # Show hotel features
        else:
            # Hide or disable hotel features
    """
    checker = HotelAvailabilityChecker()
    return checker.check_city_has_hotels(city)


def get_supported_cities() -> List[Dict[str, any]]:
    """
    Get all cities with hotel data

    Usage:
        from hotel_availability_checker import get_supported_cities

        cities = get_supported_cities()
        # [{"city": "Milan", "hotel_count": 161, ...}, ...]
    """
    checker = HotelAvailabilityChecker()
    return checker.get_available_cities()


def normalize_city_name(city: str) -> Optional[str]:
    """
    Convert any city name variation to database format

    Usage:
        from hotel_availability_checker import normalize_city_name

        db_city = normalize_city_name('Milano')  # Returns 'Milan'
        db_city = normalize_city_name('Roma')    # Returns 'Rome'
    """
    checker = HotelAvailabilityChecker()
    return checker.find_city_in_database(city)


# Test function
if __name__ == "__main__":
    print("🏨 Hotel Availability Checker - Test Suite\n")

    checker = HotelAvailabilityChecker()

    # Test 1: Get all available cities
    print("1️⃣ Available Cities:")
    cities = checker.get_available_cities()
    for city_info in cities:
        print(f"   • {city_info['city']}: {city_info['hotel_count']} hotels, "
              f"avg {city_info['avg_rating']}⭐, {city_info['total_reviews']} reviews")
    print()

    # Test 2: Check specific cities
    print("2️⃣ City Availability Checks:")
    test_cities = ['Milan', 'Milano', 'Rome', 'Florence', 'Paris', 'New York']

    for city in test_cities:
        result = checker.check_city_has_hotels(city)
        status = "✅ Available" if result['available'] else "❌ Not Available"
        print(f"   {status}: {city}")
        if result['available']:
            print(
                f"      → {result['hotel_count']} hotels, avg {result['avg_rating']}⭐")
        else:
            print(f"      → {result['message']}")
    print()

    # Test 3: City name normalization
    print("3️⃣ City Name Normalization:")
    test_variations = ['Milano', 'Roma', 'Firenze', 'Venezia']

    for variation in test_variations:
        db_name = checker.find_city_in_database(variation)
        if db_name:
            print(f"   '{variation}' → '{db_name}' ✅")
        else:
            print(f"   '{variation}' → Not found ❌")
    print()

    # Test 4: Standalone functions
    print("4️⃣ Standalone Function Tests:")

    milan_check = check_hotel_availability('Milan')
    print(f"   check_hotel_availability('Milan'): {milan_check['available']}")

    supported = get_supported_cities()
    print(f"   get_supported_cities(): {len(supported)} cities found")

    normalized = normalize_city_name('Milano')
    print(f"   normalize_city_name('Milano'): '{normalized}'")

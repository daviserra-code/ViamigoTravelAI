#!/usr/bin/env python3
"""
Hotels Integration Module for ViamigoTravelAI
Features:
1. Add hotels as accommodation POIs on routes
2. Use hotels as starting/ending points
3. Show nearby hotels for attractions
4. Generate top hotels lists by neighborhood/category
6. Optimize routes based on hotel location
"""

import psycopg2
import os
from typing import List, Dict, Optional, Tuple
import json

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_r9e2PGORqsAx@ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech/neondb?sslmode=require'
)


class HotelsIntegration:
    """Handle hotel data integration with route planning"""

    def __init__(self):
        self.db_url = DATABASE_URL

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def get_hotels_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        min_rating: float = 8.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get hotels near a specific location

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            min_rating: Minimum average score
            limit: Maximum number of results

        Returns:
            List of hotel dictionaries with details
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Using Haversine formula for distance calculation
        query = """
            SELECT 
                hotel_name,
                hotel_address,
                city,
                latitude,
                longitude,
                average_score,
                COUNT(*) as review_count,
                -- Calculate distance in km
                6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(latitude))
                ) as distance_km
            FROM hotel_reviews
            WHERE 
                latitude IS NOT NULL 
                AND longitude IS NOT NULL
                AND average_score >= %s
                AND 6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(latitude))
                ) <= %s
            GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
            ORDER BY average_score DESC, review_count DESC
            LIMIT %s
        """

        cursor.execute(query, (
            latitude, longitude, latitude, min_rating,
            latitude, longitude, latitude, radius_km, limit
        ))

        hotels = []
        for row in cursor.fetchall():
            hotels.append({
                'name': row[0],
                'address': row[1],
                'city': row[2],
                'latitude': float(row[3]),
                'longitude': float(row[4]),
                'rating': float(row[5]),
                'review_count': row[6],
                'distance_km': float(row[7]),
                'type': 'hotel'
            })

        cursor.close()
        conn.close()

        return hotels

    def get_hotel_by_name(self, hotel_name: str, city: str = None) -> Optional[Dict]:
        """
        Get specific hotel details by name

        Args:
            hotel_name: Name of the hotel
            city: Optional city filter

        Returns:
            Hotel dictionary or None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if city:
            query = """
                SELECT 
                    hotel_name,
                    hotel_address,
                    city,
                    latitude,
                    longitude,
                    average_score,
                    COUNT(*) as review_count
                FROM hotel_reviews
                WHERE LOWER(hotel_name) = LOWER(%s)
                AND (city = %s OR LOWER(city) LIKE LOWER(%s))
                GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
                LIMIT 1
            """
            cursor.execute(query, (hotel_name, city, f'%{city}%'))
        else:
            query = """
                SELECT 
                    hotel_name,
                    hotel_address,
                    city,
                    latitude,
                    longitude,
                    average_score,
                    COUNT(*) as review_count
                FROM hotel_reviews
                WHERE LOWER(hotel_name) = LOWER(%s)
                GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
                LIMIT 1
            """
            cursor.execute(query, (hotel_name,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return {
                'name': row[0],
                'address': row[1],
                'city': row[2],
                'latitude': float(row[3]),
                'longitude': float(row[4]),
                'rating': float(row[5]),
                'review_count': row[6],
                'type': 'hotel'
            }
        return None

    def get_top_hotels_by_city(
        self,
        city: str,
        category: str = 'all',
        limit: int = 20
    ) -> List[Dict]:
        """
        Get top hotels in a city by category

        Args:
            city: City name
            category: 'luxury' (9.0+), 'premium' (8.5+), 'mid-range' (8.0+), 'budget' (7.0+), or 'all'
            limit: Maximum number of results

        Returns:
            List of hotel dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Set rating threshold based on category
        rating_thresholds = {
            'luxury': 9.0,
            'premium': 8.5,
            'mid-range': 8.0,
            'budget': 7.0,
            'all': 0.0
        }
        min_rating = rating_thresholds.get(category, 0.0)

        query = """
            SELECT 
                hotel_name,
                hotel_address,
                city,
                latitude,
                longitude,
                average_score,
                COUNT(*) as review_count
            FROM hotel_reviews
            WHERE (city = %s OR LOWER(city) LIKE LOWER(%s))
            AND average_score >= %s
            GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
            ORDER BY average_score DESC, review_count DESC
            LIMIT %s
        """

        cursor.execute(query, (city, f'%{city}%', min_rating, limit))

        hotels = []
        for row in cursor.fetchall():
            # Determine category based on rating
            rating = float(row[5])
            if rating >= 9.0:
                cat = 'luxury'
            elif rating >= 8.5:
                cat = 'premium'
            elif rating >= 8.0:
                cat = 'mid-range'
            else:
                cat = 'budget'

            hotels.append({
                'name': row[0],
                'address': row[1],
                'city': row[2],
                'latitude': float(row[3]),
                'longitude': float(row[4]),
                'rating': rating,
                'review_count': row[6],
                'category': cat,
                'type': 'hotel'
            })

        cursor.close()
        conn.close()

        return hotels

    def search_hotels(
        self,
        city: str,
        search_term: str = None,
        min_rating: float = 8.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search hotels by name or address

        Args:
            city: City name
            search_term: Search query (hotel name or address)
            min_rating: Minimum rating
            limit: Maximum results

        Returns:
            List of matching hotels
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if search_term:
            query = """
                SELECT 
                    hotel_name,
                    hotel_address,
                    city,
                    latitude,
                    longitude,
                    average_score,
                    COUNT(*) as review_count
                FROM hotel_reviews
                WHERE (city = %s OR LOWER(city) LIKE LOWER(%s))
                AND (
                    LOWER(hotel_name) LIKE LOWER(%s)
                    OR LOWER(hotel_address) LIKE LOWER(%s)
                )
                AND average_score >= %s
                GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
                ORDER BY average_score DESC, review_count DESC
                LIMIT %s
            """
            search_pattern = f'%{search_term}%'
            cursor.execute(
                query, (city, f'%{city}%', search_pattern, search_pattern, min_rating, limit))
        else:
            # Just get top hotels if no search term
            query = """
                SELECT 
                    hotel_name,
                    hotel_address,
                    city,
                    latitude,
                    longitude,
                    average_score,
                    COUNT(*) as review_count
                FROM hotel_reviews
                WHERE (city = %s OR LOWER(city) LIKE LOWER(%s))
                AND average_score >= %s
                GROUP BY hotel_name, hotel_address, city, latitude, longitude, average_score
                ORDER BY average_score DESC, review_count DESC
                LIMIT %s
            """
            cursor.execute(query, (city, f'%{city}%', min_rating, limit))

        hotels = []
        for row in cursor.fetchall():
            hotels.append({
                'name': row[0],
                'address': row[1],
                'city': row[2],
                'latitude': float(row[3]),
                'longitude': float(row[4]),
                'rating': float(row[5]),
                'review_count': row[6],
                'type': 'hotel'
            })

        cursor.close()
        conn.close()

        return hotels

    def get_hotels_by_neighborhood(
        self,
        city: str,
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        limit: int = 15
    ) -> List[Dict]:
        """
        Get hotels in a specific neighborhood (defined by center point and radius)

        Args:
            city: City name
            latitude: Neighborhood center latitude
            longitude: Neighborhood center longitude
            radius_km: Neighborhood radius in km
            limit: Maximum results

        Returns:
            List of hotels in the neighborhood
        """
        return self.get_hotels_near_location(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            min_rating=7.0,  # Lower threshold for neighborhood search
            limit=limit
        )

    def format_hotel_for_route(self, hotel: Dict, role: str = 'accommodation') -> Dict:
        """
        Format hotel data for route itinerary

        Args:
            hotel: Hotel dictionary
            role: 'start', 'end', 'accommodation', or 'nearby'

        Returns:
            Formatted itinerary item
        """
        description = f"Rated {hotel['rating']}/10 with {hotel['review_count']:,} reviews"

        if role == 'start':
            title = f"Start: {hotel['name']}"
            item_type = 'start'
        elif role == 'end':
            title = f"End: {hotel['name']}"
            item_type = 'end'
        elif role == 'nearby':
            title = f"Nearby: {hotel['name']}"
            item_type = 'hotel_suggestion'
        else:
            title = hotel['name']
            item_type = 'accommodation'

        return {
            'title': title,
            'name': hotel['name'],
            'description': description,
            'latitude': hotel['latitude'],
            'longitude': hotel['longitude'],
            'lat': hotel['latitude'],
            'lng': hotel['longitude'],
            'type': item_type,
            'context': f"hotel_{hotel['name'].lower().replace(' ', '_')}",
            'rating': hotel['rating'],
            'review_count': hotel['review_count'],
            'address': hotel.get('address', ''),
            'category': hotel.get('category', 'hotel')
        }


# Utility functions for Flask integration

def get_hotels_api():
    """Get hotels integration instance"""
    return HotelsIntegration()


def add_hotel_to_route(route_data: List[Dict], hotel_name: str, city: str, position: str = 'start') -> List[Dict]:
    """
    Add a hotel to a route at specified position

    Args:
        route_data: Existing route itinerary
        hotel_name: Name of hotel to add
        city: City name
        position: 'start' or 'end'

    Returns:
        Modified route with hotel
    """
    hotels = HotelsIntegration()
    hotel = hotels.get_hotel_by_name(hotel_name, city)

    if not hotel:
        return route_data

    hotel_item = hotels.format_hotel_for_route(hotel, role=position)

    if position == 'start':
        return [hotel_item] + route_data
    else:  # end
        return route_data + [hotel_item]


def get_accommodation_suggestions(latitude: float, longitude: float, city: str = 'Milano') -> List[Dict]:
    """
    Get hotel suggestions for a location

    Args:
        latitude: Location latitude
        longitude: Location longitude
        city: City name

    Returns:
        List of formatted hotel suggestions
    """
    hotels = HotelsIntegration()
    nearby_hotels = hotels.get_hotels_near_location(
        latitude=latitude,
        longitude=longitude,
        radius_km=1.5,
        min_rating=8.0,
        limit=5
    )

    return [hotels.format_hotel_for_route(h, role='nearby') for h in nearby_hotels]


if __name__ == '__main__':
    # Test the integration
    print("🏨 Hotels Integration Test\n")

    hotels = HotelsIntegration()

    # Test 1: Get hotels near Duomo
    print("1️⃣ Hotels near Duomo di Milano (45.464, 9.190):")
    duomo_hotels = hotels.get_hotels_near_location(
        45.464, 9.190, radius_km=1.0, limit=5)
    for i, h in enumerate(duomo_hotels, 1):
        print(
            f"   {i}. {h['name']:40s} | ⭐{h['rating']:.1f} | {h['distance_km']:.2f}km | {h['review_count']} reviews")

    # Test 2: Get top luxury hotels
    print("\n2️⃣ Top Luxury Hotels in Milano:")
    luxury = hotels.get_top_hotels_by_city(
        'Milano', category='luxury', limit=5)
    for i, h in enumerate(luxury, 1):
        print(
            f"   {i}. {h['name']:40s} | ⭐{h['rating']:.1f} | {h['review_count']} reviews")

    # Test 3: Search hotels
    print("\n3️⃣ Search 'Gallia':")
    results = hotels.search_hotels('Milano', 'Gallia', limit=3)
    for h in results:
        print(f"   - {h['name']} | {h['address']}")

    # Test 4: Get specific hotel
    print("\n4️⃣ Get 'Hotel Berna':")
    berna = hotels.get_hotel_by_name('Hotel Berna', 'Milan')
    if berna:
        print(f"   ✅ {berna['name']}")
        print(f"      Address: {berna['address']}")
        print(
            f"      Rating: {berna['rating']}/10 ({berna['review_count']} reviews)")
        print(f"      Coords: {berna['latitude']}, {berna['longitude']}")

    print("\n✅ All tests completed!")

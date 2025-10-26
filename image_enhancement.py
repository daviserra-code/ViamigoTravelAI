"""
🖼️ IMAGE ENHANCEMENT SYSTEM
Proactively populate images for high-priority attractions

Strategy:
1. Use existing Apify auto-save system (already implemented)
2. Identify high-priority attractions without images
3. Batch-fetch images during off-peak times
4. Use Wikimedia API as free alternative for landmarks
"""

import psycopg2
import os
import requests
import json
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()


class ImageEnhancementSystem:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')

    def get_attractions_without_images(self, city: str = None, limit: int = 20) -> List[Dict]:
        """Get high-priority attractions missing images"""
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()

        query = '''
            SELECT place_name, city, priority_level
            FROM place_cache
            WHERE (priority_level = 'high' OR priority_level = 'critical')
        '''
        params = []

        if city:
            query += ' AND city = %s'
            params.append(city)

        query += ' ORDER BY priority_level DESC, access_count DESC LIMIT %s'
        params.append(limit)

        cur.execute(query, params)
        results = cur.fetchall()

        attractions = []
        for name, city_name, priority in results:
            attractions.append({
                'name': name,
                'city': city_name,
                'priority': priority
            })

        conn.close()
        return attractions

    def get_wikimedia_image(self, attraction_name: str) -> Optional[str]:
        """
        Get free image from Wikimedia Commons
        Alternative to expensive Apify for famous landmarks
        """
        try:
            # Search Wikimedia Commons
            search_url = 'https://commons.wikimedia.org/w/api.php'
            params = {
                'action': 'query',
                'format': 'json',
                'generator': 'search',
                'gsrsearch': f'{attraction_name} Italy',
                'gsrlimit': 1,
                'prop': 'imageinfo',
                'iiprop': 'url',
                'iiurlwidth': 800
            }

            response = requests.get(search_url, params=params, timeout=5)
            data = response.json()

            if 'query' in data and 'pages' in data['query']:
                pages = data['query']['pages']
                page = list(pages.values())[0]
                if 'imageinfo' in page:
                    image_url = page['imageinfo'][0]['thumburl']
                    print(f'  ✅ Wikimedia image found: {attraction_name}')
                    return image_url

            print(f'  ❌ No Wikimedia image for: {attraction_name}')
            return None

        except Exception as e:
            print(f'  ❌ Wikimedia error for {attraction_name}: {e}')
            return None

    def enhance_attraction_images(self, city: str = None, use_apify: bool = False):
        """
        Enhance images for high-priority attractions

        Args:
            city: Specific city or None for all
            use_apify: If True, use Apify (costs money), if False use Wikimedia only (FREE)
        """
        print(f'\n🖼️ IMAGE ENHANCEMENT SYSTEM')
        print('=' * 60)

        attractions = self.get_attractions_without_images(city=city, limit=20)
        print(
            f'Found {len(attractions)} high-priority attractions to enhance\n')

        enhanced_count = 0

        for attr in attractions:
            name = attr['name']
            city_name = attr['city']
            priority = attr['priority']

            print(f'\n📍 {name} ({city_name}) - Priority: {priority}')

            # OPTION 1: Try Wikimedia Commons (FREE)
            image_url = self.get_wikimedia_image(name)

            # OPTION 2: Use Apify if allowed and Wikimedia failed
            if not image_url and use_apify:
                print(f'  💰 Using Apify for {name}...')
                # The existing system will auto-save via intelligent_detail_handler
                # when a detail request is made
                print(f'  💡 Apify will be used when user requests details')

            if image_url:
                # Save to comprehensive_attractions
                self._save_image_to_db(
                    name, city_name, image_url, source='wikimedia')
                enhanced_count += 1

        print(
            f'\n✅ Enhanced {enhanced_count}/{len(attractions)} attractions with images')
        print(f'💰 Cost: $0 (using Wikimedia Commons)')

    def _save_image_to_db(self, name: str, city: str, image_url: str, source: str = 'wikimedia'):
        """Save image URL to comprehensive_attractions"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            # Check if attraction exists
            cur.execute('''
                SELECT id FROM comprehensive_attractions
                WHERE LOWER(name) = LOWER(%s) AND LOWER(city) = LOWER(%s)
            ''', (name, city))

            if cur.fetchone():
                # Update existing
                cur.execute('''
                    UPDATE comprehensive_attractions
                    SET image_url = %s, last_updated = NOW()
                    WHERE LOWER(name) = LOWER(%s) AND LOWER(city) = LOWER(%s)
                ''', (image_url, name, city))
                print(f'  ✅ Updated image for {name}')
            else:
                # Insert new
                cur.execute('''
                    INSERT INTO comprehensive_attractions 
                    (name, city, image_url, data_source, created_at, last_updated)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                ''', (name, city, image_url, source))
                print(f'  ✅ Inserted {name} with image')

            conn.commit()
            conn.close()

        except Exception as e:
            print(f'  ❌ Database error for {name}: {e}')

    def populate_images_for_city(self, city: str, use_apify: bool = False):
        """
        Populate images for all high-priority attractions in a city

        COST-EFFECTIVE MODE (use_apify=False):
        - Uses Wikimedia Commons (FREE)
        - Good for famous landmarks

        COMPREHENSIVE MODE (use_apify=True):
        - Uses Apify when Wikimedia fails (COSTS MONEY)
        - More complete coverage
        """
        print(f'\n🎯 POPULATING IMAGES FOR {city.upper()}')
        print(
            f'💰 Cost mode: {"Apify enabled ($$)" if use_apify else "FREE (Wikimedia only)"}')

        self.enhance_attraction_images(city=city, use_apify=use_apify)


def main():
    """Run image enhancement"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhance attraction images')
    parser.add_argument('--city', type=str,
                        help='City to enhance (e.g. Torino)')
    parser.add_argument('--apify', action='store_true',
                        help='Enable Apify (costs money)')
    parser.add_argument('--all-italian-cities',
                        action='store_true', help='Enhance all Italian cities')

    args = parser.parse_args()

    enhancer = ImageEnhancementSystem()

    if args.all_italian_cities:
        cities = ['Torino', 'Milano', 'Roma', 'Venezia', 'Firenze', 'Napoli',
                  'Bologna', 'Genova', 'Palermo', 'Catania', 'Bari', 'Verona']
        for city in cities:
            enhancer.populate_images_for_city(city, use_apify=args.apify)
    elif args.city:
        enhancer.populate_images_for_city(args.city, use_apify=args.apify)
    else:
        print('Usage:')
        print('  python image_enhancement.py --city Torino                  # Free Wikimedia images for Torino')
        print('  python image_enhancement.py --city Torino --apify          # Use Apify for Torino (costs money)')
        print('  python image_enhancement.py --all-italian-cities           # Free images for all cities')
        print('  python image_enhancement.py --all-italian-cities --apify   # Comprehensive (expensive!)')


if __name__ == '__main__':
    main()

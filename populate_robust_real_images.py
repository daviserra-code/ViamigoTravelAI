"""
ViamigoTravelAI Robust Real Image Loader
Uses live Wikimedia Commons search API to find actual working images
"""
import psycopg2
import requests
import os
import hashlib
from io import BytesIO
from PIL import Image
import logging
from dotenv import load_dotenv
import time
import json
from urllib.parse import quote

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


def download_and_process_image(url, max_size_mb=3):
    """Download and process image with robust error handling"""
    try:
        headers = {
            'User-Agent': 'ViamigoTravelAI/1.0 (https://viamigo.travel; contact@viamigo.travel)',
            'Accept': 'image/*,*/*;q=0.8'
        }

        logger.info(f"Downloading: {url}")
        response = requests.get(url, headers=headers, timeout=30, stream=True)

        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return None

        # Read content in chunks
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size_mb * 1024 * 1024:
                logger.warning(f"Image too large: {len(content)} bytes")
                return None

        # Verify it's a valid image
        try:
            img = Image.open(BytesIO(content))
            width, height = img.size

            # Skip very small images
            if width < 400 or height < 300:
                logger.warning(f"Image too small: {width}x{height}")
                return None

            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()
                              [-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if too large
            if width > 1200 or height > 800:
                img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                width, height = img.size

            # Save as optimized JPEG
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            img_bytes = output.getvalue()

            return {
                'bytes': img_bytes,
                'width': width,
                'height': height,
                'mime_type': 'image/jpeg',
                'size': len(img_bytes)
            }

        except Exception as e:
            logger.warning(f"Invalid image data: {e}")
            return None

    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


def search_wikimedia_commons(search_terms, limit=5):
    """Search Wikimedia Commons for images"""
    try:
        api_url = "https://commons.wikimedia.org/w/api.php"

        for term in search_terms:
            logger.info(f"Searching Wikimedia Commons for: {term}")

            params = {
                'action': 'query',
                'format': 'json',
                'generator': 'search',
                'gsrsearch': f'filetype:bitmap "{term}"',
                'gsrnamespace': 6,  # File namespace
                'gsrlimit': limit,
                'prop': 'imageinfo',
                'iiprop': 'url|size|mime',
                'iiurlwidth': 800
            }

            response = requests.get(api_url, params=params, timeout=15)
            if response.status_code != 200:
                continue

            data = response.json()
            if 'query' not in data or 'pages' not in data['query']:
                continue

            for page_id, page in data['query']['pages'].items():
                if 'imageinfo' not in page:
                    continue

                for info in page['imageinfo']:
                    # Check if it's a reasonable image size and format
                    if ('mime' in info and info['mime'].startswith('image/') and
                            'size' in info and info['size'] < 5 * 1024 * 1024):  # Less than 5MB

                        # Prefer thumbnail URL if available, otherwise use original
                        if 'thumburl' in info:
                            yield info['thumburl']
                        elif 'url' in info:
                            yield info['url']

    except Exception as e:
        logger.warning(f"Wikimedia search error: {e}")


def search_italian_attractions_images():
    """Get search terms for Italian attractions"""
    attractions_search_terms = [
        # Roma
        ('Roma', 'Colosseo', ['Colosseum Rome Italy',
         'Colosseo Roma', 'Roman Colosseum']),
        ('Roma', 'Fontana di Trevi', [
         'Trevi Fountain Rome', 'Fontana di Trevi Roma', 'Trevi fountain Italy']),
        ('Roma', 'Pantheon', ['Pantheon Rome Italy',
         'Pantheon Roma', 'Roman Pantheon']),
        ('Roma', 'Foro Romano', ['Roman Forum Rome',
         'Foro Romano Roma', 'Roman Forum Italy']),
        ('Roma', 'Castel Sant Angelo', [
         'Castel Sant Angelo Rome', 'Mausoleum Hadrian Rome', 'Sant Angelo Castle']),
        ('Roma', 'Basilica di San Pietro', [
         'St Peter Basilica Vatican', 'Basilica San Pietro Roma', 'Vatican Basilica']),

        # Firenze
        ('Firenze', 'Duomo di Firenze', [
         'Florence Cathedral Italy', 'Duomo Firenze', 'Santa Maria del Fiore Florence']),
        ('Firenze', 'Ponte Vecchio', [
         'Ponte Vecchio Florence', 'Old Bridge Florence Italy', 'Ponte Vecchio Firenze']),
        ('Firenze', 'Uffizi', ['Uffizi Gallery Florence',
         'Uffizi Museum Italy', 'Galleria degli Uffizi']),
        ('Firenze', 'Palazzo Pitti', [
         'Pitti Palace Florence', 'Palazzo Pitti Firenze', 'Pitti Palace Italy']),

        # Venezia
        ('Venezia', 'Piazza San Marco', [
         'St Mark Square Venice', 'Piazza San Marco Venezia', 'Saint Mark Square Italy']),
        ('Venezia', 'Basilica di San Marco', [
         'St Mark Basilica Venice', 'San Marco Cathedral Venice', 'Saint Mark Basilica Italy']),
        ('Venezia', 'Palazzo Ducale', [
         'Doge Palace Venice', 'Palazzo Ducale Venezia', 'Doges Palace Italy']),
        ('Venezia', 'Ponte di Rialto', [
         'Rialto Bridge Venice', 'Ponte Rialto Venezia', 'Rialto Bridge Italy']),
        ('Venezia', 'Canal Grande', [
         'Grand Canal Venice', 'Canal Grande Venezia', 'Venice Grand Canal']),

        # Milano
        ('Milano', 'Duomo di Milano', [
         'Milan Cathedral Italy', 'Duomo Milano', 'Milan Cathedral']),
        ('Milano', 'La Scala', ['La Scala Opera House Milan',
         'Teatro alla Scala Milano', 'La Scala Theatre']),
        ('Milano', 'Castello Sforzesco', [
         'Sforza Castle Milan', 'Castello Sforzesco Milano', 'Sforzesco Castle Italy']),
        ('Milano', 'Galleria Vittorio Emanuele', [
         'Galleria Vittorio Emanuele Milan', 'Milan Shopping Gallery', 'Galleria Milano']),

        # Other cities
        ('Pisa', 'Torre di Pisa', ['Leaning Tower Pisa',
         'Torre Pendente Pisa', 'Pisa Tower Italy']),
        ('Napoli', 'Vesuvio', ['Mount Vesuvius Italy',
         'Vesuvio Napoli', 'Vesuvius volcano Naples']),
        ('Napoli', 'Pompei', ['Pompeii ruins Italy',
         'Pompei archaeological site', 'Pompeii ancient city']),
        ('Bologna', 'Piazza Maggiore', [
         'Piazza Maggiore Bologna', 'Bologna main square', 'Bologna central square']),
        ('Torino', 'Mole Antonelliana', [
         'Mole Antonelliana Turin', 'Mole Antonelliana Torino', 'Turin landmark']),
    ]

    return attractions_search_terms


def add_attraction_image_from_search(city, attraction_name, search_terms, source_name="wikimedia_search"):
    """Add an attraction image from search results"""

    # Get image URLs from search
    image_urls = list(search_wikimedia_commons(search_terms, limit=3))

    if not image_urls:
        logger.warning(f"No images found for {attraction_name}")
        return False

    logger.info(
        f"Found {len(image_urls)} potential images for {attraction_name}")

    for i, url in enumerate(image_urls):
        try:
            logger.info(
                f"Trying image {i+1}/{len(image_urls)} for {attraction_name}")

            # Download and process the image
            image_data = download_and_process_image(url)

            if not image_data:
                logger.info(f"Failed to process image {i+1}")
                continue

            # Save to database
            conn = get_db_connection()
            if not conn:
                continue

            try:
                sha256_hash = hashlib.sha256(image_data['bytes']).hexdigest()

                with conn.cursor() as cur:
                    # Check if image already exists
                    cur.execute(
                        "SELECT id FROM attraction_images WHERE sha256_hash = %s", (sha256_hash,))
                    if cur.fetchone():
                        logger.info(f"Image already exists (duplicate hash)")
                        return True

                    # Insert new image
                    cur.execute("""
                        INSERT INTO attraction_images 
                        (source, city, attraction_name, original_url,
                         img_bytes, mime_type, width, height, sha256_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (sha256_hash) DO NOTHING
                    """, (
                        source_name, city, attraction_name, url,
                        image_data['bytes'], image_data['mime_type'],
                        image_data['width'], image_data['height'], sha256_hash
                    ))

                    conn.commit()
                    logger.info(
                        f"✅ Added {attraction_name} ({image_data['size']} bytes, {image_data['width']}x{image_data['height']})")
                    return True

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error with image {i+1} for {attraction_name}: {e}")
            continue

    logger.warning(
        f"❌ Could not find working image for {attraction_name} in {city}")
    return False


def load_live_search_images():
    """Load real images using live Wikimedia Commons search"""

    attractions = search_italian_attractions_images()
    successful = 0
    failed = 0

    logger.info(
        f"Starting to load {len(attractions)} real attraction images using live search...")

    for i, (city, attraction_name, search_terms) in enumerate(attractions, 1):
        logger.info(
            f"Processing {i}/{len(attractions)}: {attraction_name} in {city}")

        success = add_attraction_image_from_search(
            city, attraction_name, search_terms)

        if success:
            successful += 1
        else:
            failed += 1

        # Be respectful to APIs - longer delay for search
        time.sleep(3)

    logger.info(f"✅ Completed: {successful} successful, {failed} failed")
    return successful, failed


def show_database_stats():
    """Show current database statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return

        with conn.cursor() as cur:
            # Overall stats
            cur.execute("""
                SELECT COUNT(*) as total_images,
                       COUNT(DISTINCT city) as cities_count,
                       SUM(LENGTH(img_bytes)) as total_size,
                       AVG(LENGTH(img_bytes)) as avg_size
                FROM attraction_images
            """)
            overall = cur.fetchone()

            # By city stats
            cur.execute("""
                SELECT city, COUNT(*) as count, 
                       SUM(LENGTH(img_bytes)) as total_bytes,
                       STRING_AGG(attraction_name, ', ') as attractions
                FROM attraction_images 
                GROUP BY city 
                ORDER BY count DESC
            """)
            city_stats = cur.fetchall()

            # By source stats
            cur.execute("""
                SELECT source, COUNT(*) as count
                FROM attraction_images 
                GROUP BY source 
                ORDER BY count DESC
            """)
            source_stats = cur.fetchall()

        conn.close()

        print("\n📊 Database Statistics:")
        print("=" * 50)
        print(f"Total images: {overall[0]}")
        print(f"Cities covered: {overall[1]}")
        print(f"Total size: {overall[2] / 1024 / 1024:.2f} MB")
        print(f"Average size: {overall[3] / 1024:.1f} KB")

        print("\nBy City:")
        for city, count, size_bytes, attractions in city_stats:
            size_mb = size_bytes / 1024 / 1024
            print(f"  {city}: {count} images ({size_mb:.2f} MB)")
            print(f"    Attractions: {attractions}")

        print("\nBy Source:")
        for source, count in source_stats:
            print(f"  {source}: {count} images")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")


if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI ROBUST Real Image Loader")
    print("Using live Wikimedia Commons search API")
    print("=" * 60)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting ROBUST real image loading...")
    print("Using live Wikimedia Commons search for maximum reliability")

    successful, failed = load_live_search_images()

    print(f"\n📊 Loading Results:")
    print(f"   ✅ Successfully added: {successful} REAL images")
    print(f"   ❌ Failed: {failed} images")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 ROBUST real image loading completed!")
    print("Your database now contains actual attraction photos from Wikimedia Commons!")
    print("=" * 60)

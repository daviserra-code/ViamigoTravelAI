"""
ViamigoTravelAI Real Image Loader
Fetches actual attraction images from multiple reliable sources
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


def download_and_process_image(url, max_size_mb=2):
    """Download and process image with robust error handling"""
    try:
        headers = {
            'User-Agent': 'ViamigoTravelAI/1.0 (Educational purpose; mailto:admin@viamigo.com)',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }

        logger.info(f"Downloading: {url}")
        response = requests.get(url, headers=headers, timeout=30, stream=True)

        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return None

        # Read content
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

            # Skip very small images (likely icons/thumbnails)
            if width < 300 or height < 200:
                logger.warning(f"Image too small: {width}x{height}")
                return None

            # Convert to JPEG for consistency
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()
                              [-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Optimize size - resize if too large
            if width > 1200 or height > 800:
                img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                width, height = img.size

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


def get_wikimedia_image(attraction_name, city):
    """Get image from Wikimedia Commons API"""
    try:
        # Search for the attraction
        search_term = f"{attraction_name} {city}"
        api_url = "https://commons.wikimedia.org/w/api.php"

        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': search_term,
            'srnamespace': 6,  # File namespace
            'srlimit': 5
        }

        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if 'query' not in data or 'search' not in data['query']:
            return None

        for result in data['query']['search']:
            filename = result['title']
            if any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png']):
                # Get file info to get the actual image URL
                info_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': filename,
                    'prop': 'imageinfo',
                    'iiprop': 'url|size',
                    'iiurlwidth': 800
                }

                info_response = requests.get(
                    api_url, params=info_params, timeout=10)
                if info_response.status_code == 200:
                    info_data = info_response.json()
                    pages = info_data.get('query', {}).get('pages', {})
                    for page in pages.values():
                        imageinfo = page.get('imageinfo', [])
                        if imageinfo and 'thumburl' in imageinfo[0]:
                            return imageinfo[0]['thumburl']
                        elif imageinfo and 'url' in imageinfo[0]:
                            return imageinfo[0]['url']

        return None

    except Exception as e:
        logger.warning(f"Wikimedia search error for {attraction_name}: {e}")
        return None


def get_wikipedia_main_image(attraction_name, city):
    """Get main image from Wikipedia article"""
    try:
        # Search for Wikipedia article
        search_term = f"{attraction_name} {city}"
        api_url = "https://en.wikipedia.org/w/api.php"

        # First, search for the article
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': search_term,
            'srlimit': 3
        }

        response = requests.get(api_url, params=search_params, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if 'query' not in data or 'search' not in data['query']:
            return None

        for result in data['query']['search']:
            page_title = result['title']

            # Get page images
            image_params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'pageimages|images',
                'pithumbsize': 800,
                'pilimit': 1
            }

            image_response = requests.get(
                api_url, params=image_params, timeout=10)
            if image_response.status_code == 200:
                image_data = image_response.json()
                pages = image_data.get('query', {}).get('pages', {})
                for page in pages.values():
                    if 'thumbnail' in page:
                        return page['thumbnail']['source']

        return None

    except Exception as e:
        logger.warning(f"Wikipedia search error for {attraction_name}: {e}")
        return None


def add_attraction_image(city, attraction_name, source_type="auto", max_attempts=3):
    """Add an attraction image from multiple sources"""

    sources_to_try = []

    if source_type == "auto":
        # Try multiple sources
        sources_to_try = [
            ('wikipedia', lambda: get_wikipedia_main_image(attraction_name, city)),
            ('wikimedia', lambda: get_wikimedia_image(attraction_name, city))
        ]

    for source_name, source_func in sources_to_try:
        try:
            logger.info(
                f"Trying {source_name} for {attraction_name} in {city}")
            image_url = source_func()

            if not image_url:
                logger.info(f"No image found on {source_name}")
                continue

            # Download and process the image
            image_data = download_and_process_image(image_url)

            if not image_data:
                logger.info(f"Failed to process image from {source_name}")
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
                        source_name, city, attraction_name, image_url,
                        image_data['bytes'], image_data['mime_type'],
                        image_data['width'], image_data['height'], sha256_hash
                    ))

                    conn.commit()
                    logger.info(
                        f"✅ Added {attraction_name} from {source_name} ({image_data['size']} bytes, {image_data['width']}x{image_data['height']})")
                    return True

            finally:
                conn.close()

        except Exception as e:
            logger.error(
                f"Error with {source_name} for {attraction_name}: {e}")
            continue

    logger.warning(f"❌ Could not find image for {attraction_name} in {city}")
    return False


def load_real_attraction_images():
    """Load real images for major Italian attractions"""

    # Major Italian attractions that should have good Wikipedia coverage
    attractions = [
        # Roma
        {'city': 'Roma', 'name': 'Colosseo'},
        {'city': 'Roma', 'name': 'Fontana di Trevi'},
        {'city': 'Roma', 'name': 'Pantheon'},
        {'city': 'Roma', 'name': 'Foro Romano'},
        {'city': 'Roma', 'name': 'Castel Sant Angelo'},
        {'city': 'Roma', 'name': 'Piazza San Pietro'},
        {'city': 'Roma', 'name': 'Basilica di San Pietro'},

        # Firenze
        {'city': 'Firenze', 'name': 'Duomo di Firenze'},
        {'city': 'Firenze', 'name': 'Ponte Vecchio'},
        {'city': 'Firenze', 'name': 'Uffizi'},
        {'city': 'Firenze', 'name': 'Palazzo Pitti'},
        {'city': 'Firenze', 'name': 'Piazzale Michelangelo'},

        # Venezia
        {'city': 'Venezia', 'name': 'Piazza San Marco'},
        {'city': 'Venezia', 'name': 'Basilica di San Marco'},
        {'city': 'Venezia', 'name': 'Palazzo Ducale'},
        {'city': 'Venezia', 'name': 'Ponte di Rialto'},
        {'city': 'Venezia', 'name': 'Canal Grande'},

        # Milano
        {'city': 'Milano', 'name': 'Duomo di Milano'},
        {'city': 'Milano', 'name': 'La Scala'},
        {'city': 'Milano', 'name': 'Castello Sforzesco'},
        {'city': 'Milano', 'name': 'Galleria Vittorio Emanuele'},

        # Napoli
        {'city': 'Napoli', 'name': 'Vesuvio'},
        {'city': 'Napoli', 'name': 'Pompei'},
        {'city': 'Napoli', 'name': 'Castel dell Ovo'},

        # Other cities
        {'city': 'Pisa', 'name': 'Torre di Pisa'},
        {'city': 'Bologna', 'name': 'Piazza Maggiore'},
        {'city': 'Torino', 'name': 'Mole Antonelliana'},
        {'city': 'Genova', 'name': 'Palazzo Rosso'},
        {'city': 'Palermo', 'name': 'Teatro Massimo'},
    ]

    successful = 0
    failed = 0

    logger.info(
        f"Starting to load {len(attractions)} real attraction images...")

    for i, attraction in enumerate(attractions, 1):
        logger.info(
            f"Processing {i}/{len(attractions)}: {attraction['name']} in {attraction['city']}")

        success = add_attraction_image(
            city=attraction['city'],
            attraction_name=attraction['name']
        )

        if success:
            successful += 1
        else:
            failed += 1

        # Be respectful to APIs
        time.sleep(2)

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
                       SUM(LENGTH(img_bytes)) as total_bytes
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
        for city, count, size_bytes in city_stats:
            size_mb = size_bytes / 1024 / 1024
            print(f"  {city}: {count} images ({size_mb:.2f} MB)")

        print("\nBy Source:")
        for source, count in source_stats:
            print(f"  {source}: {count} images")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")


if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI REAL Image Database Loader")
    print("Fetching actual attraction images from Wikipedia/Wikimedia")
    print("=" * 60)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting REAL image loading process...")
    print("This will fetch actual photos from Wikipedia and Wikimedia Commons")

    # Ask for confirmation
    response = input("\nProceed with real image loading? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        exit(0)

    successful, failed = load_real_attraction_images()

    print(f"\n📊 Loading Results:")
    print(f"   ✅ Successfully added: {successful} REAL images")
    print(f"   ❌ Failed: {failed} images")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 REAL image loading process completed!")
    print("Your database now contains actual attraction photos!")
    print("=" * 60)

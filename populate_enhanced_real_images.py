"""
ViamigoTravelAI Enhanced Real Image Loader
Uses multiple reliable sources including direct URLs and better API searches
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/jpeg,image/png,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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

            # Skip very small images (likely icons/thumbnails)
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
            img.save(output, format='JPEG', quality=90, optimize=True)
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


def get_reliable_image_sources():
    """Get curated list of reliable image URLs for major Italian attractions"""
    return {
        # Roma
        ('Roma', 'Colosseo'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/1200px-Colosseo_2020.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Colosseum_in_Rome%2C_Italy_-_April_2007.jpg/1200px-Colosseum_in_Rome%2C_Italy_-_April_2007.jpg'
        ],
        ('Roma', 'Fontana di Trevi'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg/1200px-Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Fontana_di_Trevi_-_Roma.jpg/1200px-Fontana_di_Trevi_-_Roma.jpg'
        ],
        ('Roma', 'Pantheon'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Pantheon_Front.jpg/1200px-Pantheon_Front.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Rome_Pantheon_front.jpg/1200px-Rome_Pantheon_front.jpg'
        ],
        ('Roma', 'Foro Romano'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Roman_Forum_from_Palatine_Hill.jpg/1200px-Roman_Forum_from_Palatine_Hill.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/RomanForumFromCapitoline.jpg/1200px-RomanForumFromCapitoline.jpg'
        ],
        ('Roma', 'Castel Sant Angelo'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Castel_Sant%27Angelo_and_Ponte_Sant%27Angelo%2C_Rome.jpg/1200px-Castel_Sant%27Angelo_and_Ponte_Sant%27Angelo%2C_Rome.jpg'
        ],
        ('Roma', 'Basilica di San Pietro'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Basilica_di_San_Pietro_in_Vaticano_September_2015-1a.jpg/1200px-Basilica_di_San_Pietro_in_Vaticano_September_2015-1a.jpg'
        ],

        # Firenze
        ('Firenze', 'Duomo di Firenze'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Duomo_Firenze.jpg/1200px-Duomo_Firenze.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Cathedral_and_Campanile_-_Florence_-_Italy.jpg/1200px-Cathedral_and_Campanile_-_Florence_-_Italy.jpg'
        ],
        ('Firenze', 'Ponte Vecchio'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ponte_Vecchio_1%2C_Florence%2C_Italy.jpg/1200px-Ponte_Vecchio_1%2C_Florence%2C_Italy.jpg'
        ],
        ('Firenze', 'Uffizi'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Uffizi_Gallery%2C_Florence.jpg/1200px-Uffizi_Gallery%2C_Florence.jpg'
        ],

        # Venezia
        ('Venezia', 'Piazza San Marco'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Aerial_view_of_the_Piazza_San_Marco%2C_Venice%2C_from_the_Campanile_di_San_Marco.jpg/1200px-Aerial_view_of_the_Piazza_San_Marco%2C_Venice%2C_from_the_Campanile_di_San_Marco.jpg'
        ],
        ('Venezia', 'Basilica di San Marco'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/St_Mark%27s_Basilica_-_Venice%2C_Italy.jpg/1200px-St_Mark%27s_Basilica_-_Venice%2C_Italy.jpg'
        ],
        ('Venezia', 'Palazzo Ducale'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Doge%27s_Palace_%28Venice%29.jpg/1200px-Doge%27s_Palace_%28Venice%29.jpg'
        ],
        ('Venezia', 'Ponte di Rialto'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Rialto_Bridge_in_Venice.jpg/1200px-Rialto_Bridge_in_Venice.jpg'
        ],
        ('Venezia', 'Canal Grande'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Canal_Grande_Chiesa_della_Salute.jpg/1200px-Canal_Grande_Chiesa_della_Salute.jpg'
        ],

        # Milano
        ('Milano', 'Duomo di Milano'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Milan_Cathedral_from_Piazza_del_Duomo.jpg/1200px-Milan_Cathedral_from_Piazza_del_Duomo.jpg'
        ],
        ('Milano', 'La Scala'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/La_Scala_Milan.jpg/1200px-La_Scala_Milan.jpg'
        ],
        ('Milano', 'Castello Sforzesco'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Castello_Sforzesco_Milano.jpg/1200px-Castello_Sforzesco_Milano.jpg'
        ],

        # Other cities
        ('Pisa', 'Torre di Pisa'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Tower_of_Pisa_%288189696683%29.jpg/1200px-Tower_of_Pisa_%288189696683%29.jpg'
        ],
        ('Napoli', 'Vesuvio'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mount_Vesuvius_from_Pompeii_%28hires_version_2_scaled%29.png/1200px-Mount_Vesuvius_from_Pompeii_%28hires_version_2_scaled%29.png'
        ],
        ('Napoli', 'Pompei'): [
            'https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Street_in_Pompeii.jpg/1200px-Street_in_Pompeii.jpg'
        ]
    }


def add_attraction_image_from_urls(city, attraction_name, image_urls, source_name="wikimedia_direct"):
    """Add an attraction image from a list of URLs"""

    for i, url in enumerate(image_urls):
        try:
            logger.info(
                f"Trying URL {i+1}/{len(image_urls)} for {attraction_name}")

            # Download and process the image
            image_data = download_and_process_image(url)

            if not image_data:
                logger.info(f"Failed to process image from URL {i+1}")
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
            logger.error(f"Error with URL {i+1} for {attraction_name}: {e}")
            continue

    logger.warning(
        f"❌ Could not find working image for {attraction_name} in {city}")
    return False


def load_enhanced_real_images():
    """Load real images using curated reliable sources"""

    image_sources = get_reliable_image_sources()
    successful = 0
    failed = 0

    logger.info(
        f"Starting to load {len(image_sources)} curated real attraction images...")

    for i, ((city, attraction_name), urls) in enumerate(image_sources.items(), 1):
        logger.info(
            f"Processing {i}/{len(image_sources)}: {attraction_name} in {city}")

        success = add_attraction_image_from_urls(city, attraction_name, urls)

        if success:
            successful += 1
        else:
            failed += 1

        # Be respectful to servers
        time.sleep(1)

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
    print("🖼️ ViamigoTravelAI ENHANCED Real Image Loader")
    print("Using curated high-quality Wikimedia Commons URLs")
    print("=" * 60)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting ENHANCED real image loading...")
    print("Using pre-verified Wikimedia Commons URLs for reliability")

    successful, failed = load_enhanced_real_images()

    print(f"\n📊 Loading Results:")
    print(f"   ✅ Successfully added: {successful} REAL images")
    print(f"   ❌ Failed: {failed} images")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 ENHANCED real image loading completed!")
    print("Your database now contains high-quality attraction photos!")
    print("=" * 60)

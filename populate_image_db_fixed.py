"""
ViamigoTravelAI Image Database Loader - Fixed Version
Uses reliable image sources and proper database constraints
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
    """Download and process image, ensuring reasonable size"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            logger.warning(f"Failed to download {url}: {response.status_code}")
            return None

        # Check size
        content_length = len(response.content)
        if content_length > max_size_mb * 1024 * 1024:
            logger.warning(f"Image too large: {content_length} bytes")
            return None

        # Verify it's an image and get info
        try:
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            format_name = img.format

            # Convert to JPEG if needed for consistency
            if format_name not in ['JPEG', 'JPG']:
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert RGBA/LA/P to RGB with white background
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()
                                  [-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                img_bytes = output.getvalue()
                mime_type = 'image/jpeg'
            else:
                img_bytes = response.content
                mime_type = 'image/jpeg'

            return {
                'bytes': img_bytes,
                'width': width,
                'height': height,
                'mime_type': mime_type,
                'size': len(img_bytes)
            }

        except Exception as e:
            logger.warning(f"Invalid image format for {url}: {e}")
            return None

    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return None


def add_attraction_image(city, attraction_name, image_url, attraction_qid=None, source="manual"):
    """Add an attraction image to the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False

        # Download and process the image
        logger.info(f"Downloading image for {attraction_name} in {city}...")
        image_data = download_and_process_image(image_url)

        if not image_data:
            logger.error(f"Failed to process image for {attraction_name}")
            return False

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(image_data['bytes']).hexdigest()

        with conn.cursor() as cur:
            # Check if image already exists by hash or name+city combination
            cur.execute("""
                SELECT id FROM attraction_images 
                WHERE sha256_hash = %s OR (LOWER(city) = LOWER(%s) AND LOWER(attraction_name) = LOWER(%s))
            """, (sha256_hash, city, attraction_name))

            existing = cur.fetchone()
            if existing:
                logger.info(
                    f"Image already exists for {attraction_name} in {city}")
                return True

            # Insert new image
            cur.execute("""
                INSERT INTO attraction_images 
                (source, city, attraction_name, attraction_qid, original_url,
                 img_bytes, mime_type, width, height, sha256_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                source, city, attraction_name, attraction_qid, image_url,
                image_data['bytes'], image_data['mime_type'],
                image_data['width'], image_data['height'], sha256_hash
            ))

            conn.commit()
            logger.info(
                f"✅ Added image for {attraction_name} ({image_data['size']} bytes, {image_data['width']}x{image_data['height']})")
            return True

    except Exception as e:
        logger.error(f"Error adding image for {attraction_name}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def load_italian_attractions():
    """Load high-quality images for Italian attractions from working sources"""

    # Working image sources - using direct URLs from reliable sources
    attractions = [
        # Roma - Using working Wikipedia Commons URLs
        {
            'city': 'Roma',
            'name': 'Fontana di Trevi',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg/400px-Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg',
            'qid': 'Q186579'
        },
        {
            'city': 'Roma',
            'name': 'Pantheon',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Pantheon_Front.jpg/400px-Pantheon_Front.jpg',
            'qid': 'Q37986'
        },
        {
            'city': 'Roma',
            'name': 'Foro Romano',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Forum_Romanum_Rom.jpg/400px-Forum_Romanum_Rom.jpg',
            'qid': 'Q31870'
        },
        {
            'city': 'Roma',
            'name': 'Castel Sant Angelo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Castel_sant_angelo_HDR.jpg/400px-Castel_sant_angelo_HDR.jpg',
            'qid': 'Q50158'
        },

        # Firenze
        {
            'city': 'Firenze',
            'name': 'Duomo di Firenze',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Duomo_di_Firenze.jpg/400px-Duomo_di_Firenze.jpg',
            'qid': 'Q118674'
        },
        {
            'city': 'Firenze',
            'name': 'Ponte Vecchio',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Ponte_Vecchio_2019.jpg/400px-Ponte_Vecchio_2019.jpg',
            'qid': 'Q172408'
        },
        {
            'city': 'Firenze',
            'name': 'Palazzo Pitti',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Palazzo_Pitti.jpg/400px-Palazzo_Pitti.jpg',
            'qid': 'Q615912'
        },

        # Venezia
        {
            'city': 'Venezia',
            'name': 'Piazza San Marco',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Basilica_di_San_Marco_-_facade.jpg/400px-Basilica_di_San_Marco_-_facade.jpg',
            'qid': 'Q166140'
        },
        {
            'city': 'Venezia',
            'name': 'Ponte di Rialto',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Canal_Grande_Rialto_bridge.jpg/400px-Canal_Grande_Rialto_bridge.jpg',
            'qid': 'Q597851'
        },
        {
            'city': 'Venezia',
            'name': 'Palazzo Ducale',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Doge%27s_Palace_%28Venice%29.jpg/400px-Doge%27s_Palace_%28Venice%29.jpg',
            'qid': 'Q621728'
        },

        # Milano
        {
            'city': 'Milano',
            'name': 'Duomo di Milano',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Milan_Cathedral_from_Piazza_del_Duomo.jpg/400px-Milan_Cathedral_from_Piazza_del_Duomo.jpg',
            'qid': 'Q132053'
        },
        {
            'city': 'Milano',
            'name': 'Castello Sforzesco',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Milano_Castello_Sforzesco_2005.jpg/400px-Milano_Castello_Sforzesco_2005.jpg',
            'qid': 'Q178679'
        },

        # Napoli
        {
            'city': 'Napoli',
            'name': 'Castel Nuovo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Maschio_Angioino_-_Napoli.jpg/400px-Maschio_Angioino_-_Napoli.jpg',
            'qid': 'Q389331'
        },
        {
            'city': 'Napoli',
            'name': 'Castel dell Ovo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Castel_dell%27Ovo_Naples.jpg/400px-Castel_dell%27Ovo_Naples.jpg',
            'qid': 'Q925094'
        },

        # Pisa
        {
            'city': 'Pisa',
            'name': 'Torre di Pisa',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Leaning_Tower_of_Pisa_%28May_2022%29.jpg/300px-Leaning_Tower_of_Pisa_%28May_2022%29.jpg',
            'qid': 'Q39054'
        },

        # Bologna
        {
            'city': 'Bologna',
            'name': 'Due Torri',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Bologna-torri.jpg/400px-Bologna-torri.jpg',
            'qid': 'Q843263'
        },

        # Additional attractions with alternative sources
        {
            'city': 'Roma',
            'name': 'Piazza Navona',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Piazza_Navona_Roma.jpg/400px-Piazza_Navona_Roma.jpg',
            'qid': 'Q33965'
        },
        {
            'city': 'Firenze',
            'name': 'Piazzale Michelangelo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Firenze_-_Piazzale_Michelangelo_-_View_01.jpg/400px-Firenze_-_Piazzale_Michelangelo_-_View_01.jpg',
            'qid': 'Q1134103'
        },
        {
            'city': 'Venezia',
            'name': 'Canal Grande',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Venice_-_The_Grand_Canal.jpg/400px-Venice_-_The_Grand_Canal.jpg',
            'qid': 'Q185983'
        }
    ]

    successful = 0
    failed = 0

    logger.info(
        f"🖼️ Starting to load {len(attractions)} Italian attraction images...")

    for i, attraction in enumerate(attractions, 1):
        logger.info(
            f"[{i}/{len(attractions)}] Processing {attraction['name']} in {attraction['city']}")

        success = add_attraction_image(
            city=attraction['city'],
            attraction_name=attraction['name'],
            image_url=attraction['url'],
            attraction_qid=attraction['qid'],
            source='wikimedia_commons'
        )

        if success:
            successful += 1
        else:
            failed += 1

        # Small delay to be respectful to image servers
        time.sleep(0.5)

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

        conn.close()

        print("\n📊 Database Statistics:")
        print("=" * 50)
        print(f"Total images: {overall[0]}")
        print(f"Cities covered: {overall[1]}")
        if overall[2]:
            print(f"Total size: {overall[2] / 1024 / 1024:.2f} MB")
            print(f"Average size: {overall[3] / 1024:.1f} KB")

        print("\nBy City:")
        for city, count, size_bytes in city_stats:
            size_mb = size_bytes / 1024 / 1024 if size_bytes else 0
            print(f"  {city}: {count} images ({size_mb:.2f} MB)")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")


if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI Image Database Loader - Fixed Version")
    print("=" * 60)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting image loading process...")
    successful, failed = load_italian_attractions()

    print(f"\n📊 Loading Results:")
    print(f"   ✅ Successfully added: {successful} images")
    print(f"   ❌ Failed: {failed} images")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 Image loading process completed!")
    print("=" * 60)

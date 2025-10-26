"""
Enhanced image loader for ViamigoTravelAI with reliable sources
Populates PostgreSQL database with high-quality attraction images
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
                    # Convert RGBA/LA/P to RGB
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
            # Check if image already exists by hash
            cur.execute(
                "SELECT id FROM attraction_images WHERE sha256_hash = %s", (sha256_hash,))
            if cur.fetchone():
                logger.info(
                    f"Image already exists for {attraction_name} (duplicate hash)")
                return True

            # Insert new image
            cur.execute("""
                INSERT INTO attraction_images 
                (source, city, attraction_name, attraction_qid, original_url,
                 img_bytes, mime_type, width, height, sha256_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sha256_hash) DO NOTHING
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
    """Load high-quality images for Italian attractions from reliable sources"""

    # High-quality reliable image sources (using Unsplash with proper dimensions)
    attractions = [
        # Roma
        {
            'city': 'Roma',
            'name': 'Colosseo',
            'url': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q10285'
        },
        {
            'city': 'Roma',
            'name': 'Fontana di Trevi',
            'url': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q186579'
        },
        {
            'city': 'Roma',
            'name': 'Pantheon',
            'url': 'https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q37986'
        },
        {
            'city': 'Roma',
            'name': 'Foro Romano',
            'url': 'https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q31870'
        },
        {
            'city': 'Roma',
            'name': 'Castel Sant Angelo',
            'url': 'https://images.unsplash.com/photo-1534445538805-cb5b5cc9a5c4?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q50158'
        },
        # Firenze
        {
            'city': 'Firenze',
            'name': 'Duomo di Firenze',
            'url': 'https://images.unsplash.com/photo-1543832923-44667a44c804?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q118674'
        },
        {
            'city': 'Firenze',
            'name': 'Ponte Vecchio',
            'url': 'https://images.unsplash.com/photo-1518307697693-e7a7e6e36b2d?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q172408'
        },
        {
            'city': 'Firenze',
            'name': 'Uffizi',
            'url': 'https://images.unsplash.com/photo-1601985843082-5e1ecdf71b71?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q51252'
        },
        {
            'city': 'Firenze',
            'name': 'Palazzo Pitti',
            'url': 'https://images.unsplash.com/photo-1574020976853-5b78b8e8b7c4?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q615912'
        },
        # Venezia
        {
            'city': 'Venezia',
            'name': 'Piazza San Marco',
            'url': 'https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q166140'
        },
        {
            'city': 'Venezia',
            'name': 'Ponte di Rialto',
            'url': 'https://images.unsplash.com/photo-1522199670076-2ac386793d85?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q597851'
        },
        {
            'city': 'Venezia',
            'name': 'Basilica di San Marco',
            'url': 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q173058'
        },
        {
            'city': 'Venezia',
            'name': 'Palazzo Ducale',
            'url': 'https://images.unsplash.com/photo-1530841344095-78cfc5ad1b14?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q621728'
        },
        # Milano
        {
            'city': 'Milano',
            'name': 'Duomo di Milano',
            'url': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q132053'
        },
        {
            'city': 'Milano',
            'name': 'La Scala',
            'url': 'https://images.unsplash.com/photo-1574020976853-5b78b8e8b7c4?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q11106'
        },
        {
            'city': 'Milano',
            'name': 'Castello Sforzesco',
            'url': 'https://images.unsplash.com/photo-1513581166391-887ba0ad7c1b?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q178679'
        },
        # Napoli
        {
            'city': 'Napoli',
            'name': 'Castel Nuovo',
            'url': 'https://images.unsplash.com/photo-1605720838999-0a1a9e8f8e98?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q389331'
        },
        {
            'city': 'Napoli',
            'name': 'Castel dell Ovo',
            'url': 'https://images.unsplash.com/photo-1555758292-972ddd980eb2?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q925094'
        },
        # Pisa
        {
            'city': 'Pisa',
            'name': 'Torre di Pisa',
            'url': 'https://images.unsplash.com/photo-1525874684015-58379d421a52?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q39054'
        },
        # Bologna
        {
            'city': 'Bologna',
            'name': 'Torri di Bologna',
            'url': 'https://images.unsplash.com/photo-1513581166391-887ba0ad7c1b?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q843263'
        },
        # Genova
        {
            'city': 'Genova',
            'name': 'Via del Campo',
            'url': 'https://images.unsplash.com/photo-1513581166391-887ba0ad7c1b?w=800&h=600&fit=crop&crop=center',
            'qid': 'Q3556823'
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
            source='unsplash_curated'
        )

        if success:
            successful += 1
        else:
            failed += 1

        # Small delay to be respectful to image servers
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
        print("=" * 50)

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")


if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI Image Database Loader")
    print("=" * 50)

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
    print("=" * 50)

"""
Enhanced attraction image loader with reliable sources
"""
import psycopg2
import requests
import os
import hashlib
from io import BytesIO
from PIL import Image
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


def download_and_process_image(url, max_size_mb=1):
    """Download and process image, ensuring reasonable size"""
    try:
        headers = {
            'User-Agent': 'ViamigoTravelAI/1.0 (Educational Project)'
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
            if format_name != 'JPEG':
                rgb_img = img.convert('RGB')
                output = BytesIO()
                rgb_img.save(output, format='JPEG', quality=85)
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
            logger.warning(f"Invalid image format: {e}")
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
                logger.info(f"Image already exists for {attraction_name}")
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
                f"✅ Added image for {attraction_name} ({image_data['size']} bytes)")
            return True

    except Exception as e:
        logger.error(f"Error adding image for {attraction_name}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def load_italian_attractions():
    """Load high-quality images for Italian attractions"""

    # High-quality reliable image sources
    attractions = [
        {
            'city': 'Roma',
            'name': 'Colosseo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/800px-Colosseo_2020.jpg',
            'qid': 'Q10285'
        },
        {
            'city': 'Roma',
            'name': 'Fontana di Trevi',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg/800px-Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg',
            'qid': 'Q186579'
        },
        {
            'city': 'Roma',
            'name': 'Pantheon',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Pantheon_Front.jpg/800px-Pantheon_Front.jpg',
            'qid': 'Q37986'
        },
        {
            'city': 'Firenze',
            'name': 'Duomo di Firenze',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Duomo_di_Firenze.jpg/800px-Duomo_di_Firenze.jpg',
            'qid': 'Q118674'
        },
        {
            'city': 'Firenze',
            'name': 'Ponte Vecchio',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Ponte_Vecchio_2019.jpg/800px-Ponte_Vecchio_2019.jpg',
            'qid': 'Q172408'
        },
        {
            'city': 'Venezia',
            'name': 'Piazza San Marco',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Basilica_di_San_Marco_-_facade.jpg/800px-Basilica_di_San_Marco_-_facade.jpg',
            'qid': 'Q166140'
        },
        {
            'city': 'Venezia',
            'name': 'Ponte di Rialto',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Canal_Grande_Rialto_bridge.jpg/800px-Canal_Grande_Rialto_bridge.jpg',
            'qid': 'Q597851'
        },
        {
            'city': 'Milano',
            'name': 'Duomo di Milano',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Milan_Cathedral_from_Piazza_del_Duomo.jpg/800px-Milan_Cathedral_from_Piazza_del_Duomo.jpg',
            'qid': 'Q132053'
        },
        {
            'city': 'Napoli',
            'name': 'Castel Nuovo',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Maschio_Angioino_-_Napoli.jpg/800px-Maschio_Angioino_-_Napoli.jpg',
            'qid': 'Q389331'
        },
        {
            'city': 'Pisa',
            'name': 'Torre di Pisa',
            'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Leaning_Tower_of_Pisa_%28May_2022%29.jpg/600px-Leaning_Tower_of_Pisa_%28May_2022%29.jpg',
            'qid': 'Q39054'
        }
    ]

    successful = 0
    failed = 0

    for attraction in attractions:
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

    logger.info(f"✅ Completed: {successful} successful, {failed} failed")
    return successful, failed


if __name__ == "__main__":
    print("🖼️ Loading Italian attraction images")
    print("=" * 50)

    successful, failed = load_italian_attractions()

    print(f"\n📊 Results:")
    print(f"   ✅ Successfully added: {successful} images")
    print(f"   ❌ Failed: {failed} images")
    print("=" * 50)

"""
ViamigoTravelAI Apify Dataset Processor
Processes Apify Google Images scraper results and populates PostgreSQL database
with classified attraction images
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
from attraction_classifier import AttractionImageClassifier

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/jpeg,image/png,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        }

        # Handle different URL types
        if 'google.com/imgres' in url:
            # Extract actual image URL from Google redirect
            import urllib.parse
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if 'imgurl' in parsed:
                actual_url = parsed['imgurl'][0]
                logger.info(f"Extracted actual URL: {actual_url}")
                url = actual_url
            else:
                logger.warning(f"Could not extract image URL from: {url}")
                return None

        logger.info(f"Downloading: {url[:80]}...")
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

            # Skip very small images (likely broken thumbnails)
            if width < 100 or height < 100:
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

            # Resize if too large (keep reasonable size for web display)
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


def add_classified_image_to_db(image_data, city, attraction, confidence, original_metadata):
    """Add classified image to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False

        # Download and process the image
        image_content = download_and_process_image(image_data.get('imageUrl'))

        if not image_content:
            logger.warning(f"Failed to download image for {attraction}")
            return False

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(image_content['bytes']).hexdigest()

        with conn.cursor() as cur:
            # Check if image already exists
            cur.execute(
                "SELECT id FROM attraction_images WHERE sha256_hash = %s", (sha256_hash,))
            if cur.fetchone():
                logger.info(f"Image already exists (duplicate hash)")
                return True

            # Determine source based on confidence
            if confidence >= 0.8:
                source = 'apify_high_confidence'
            elif confidence >= 0.6:
                source = 'apify_medium_confidence'
            else:
                source = 'apify_low_confidence'

            # Insert new image
            cur.execute("""
                INSERT INTO attraction_images 
                (source, city, attraction_name, original_url, confidence_score,
                 img_bytes, mime_type, width, height, sha256_hash, 
                 original_title, content_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sha256_hash) DO NOTHING
            """, (
                source, city, attraction, image_data.get('imageUrl'),
                confidence, image_content['bytes'], image_content['mime_type'],
                image_content['width'], image_content['height'], sha256_hash,
                original_metadata.get(
                    'title'), original_metadata.get('contentUrl')
            ))

            conn.commit()
            logger.info(
                f"✅ Added {attraction} in {city} ({image_content['size']} bytes, confidence: {confidence:.2f})")
            return True

    except Exception as e:
        logger.error(f"Error adding image for {attraction}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def process_apify_dataset(dataset_path, confidence_threshold=0.0, max_images_per_attraction=10):
    """Process Apify dataset and populate database"""

    logger.info(f"🚀 Processing Apify dataset: {dataset_path}")
    logger.info(f"📊 Confidence threshold: {confidence_threshold}")
    logger.info(f"🎯 Max images per attraction: {max_images_per_attraction}")

    # Initialize classifier
    classifier = AttractionImageClassifier()

    # Load dataset
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    logger.info(f"📁 Loaded {len(data)} images from dataset")

    # Classify all images
    classifications = {}
    for image in data:
        city, attraction, confidence = classifier.classify_image(image)

        if confidence >= confidence_threshold:
            key = f"{city}_{attraction}"
            if key not in classifications:
                classifications[key] = []

            classifications[key].append({
                'image_data': image,
                'city': city,
                'attraction': attraction,
                'confidence': confidence
            })

    logger.info(
        f"🎯 Found {len(classifications)} attraction categories after filtering")

    # Process each attraction category
    total_processed = 0
    total_successful = 0
    total_failed = 0

    for category, images in classifications.items():
        city, attraction = category.split('_', 1)

        # Sort by confidence (highest first) and limit
        images_sorted = sorted(
            images, key=lambda x: x['confidence'], reverse=True)
        images_to_process = images_sorted[:max_images_per_attraction]

        logger.info(
            f"📍 Processing {len(images_to_process)} images for {attraction} in {city}")

        for item in images_to_process:
            total_processed += 1

            success = add_classified_image_to_db(
                item['image_data'],
                item['city'],
                item['attraction'],
                item['confidence'],
                item['image_data']
            )

            if success:
                total_successful += 1
            else:
                total_failed += 1

            # Small delay to be respectful
            time.sleep(0.5)

    return {
        'total_processed': total_processed,
        'successful': total_successful,
        'failed': total_failed,
        'categories': len(classifications)
    }


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
                       AVG(LENGTH(img_bytes)) as avg_size,
                       AVG(confidence_score) as avg_confidence
                FROM attraction_images
                WHERE confidence_score IS NOT NULL
            """)
            overall = cur.fetchone()

            # By source stats
            cur.execute("""
                SELECT source, COUNT(*) as count,
                       AVG(confidence_score) as avg_confidence
                FROM attraction_images 
                WHERE source LIKE 'apify%'
                GROUP BY source 
                ORDER BY count DESC
            """)
            source_stats = cur.fetchall()

            # By attraction stats (top 10)
            cur.execute("""
                SELECT city, attraction_name, COUNT(*) as count,
                       AVG(confidence_score) as avg_confidence
                FROM attraction_images 
                WHERE source LIKE 'apify%'
                GROUP BY city, attraction_name 
                ORDER BY count DESC
                LIMIT 10
            """)
            attraction_stats = cur.fetchall()

        conn.close()

        print("\n📊 Database Statistics (Apify Images)")
        print("=" * 60)
        if overall[0]:
            print(f"Total Apify images: {overall[0]}")
            print(f"Cities covered: {overall[1]}")
            print(f"Total size: {overall[2] / 1024 / 1024:.2f} MB")
            print(f"Average size: {overall[3] / 1024:.1f} KB")
            print(f"Average confidence: {overall[4]:.2f}")

        if source_stats:
            print("\nBy Confidence Level:")
            for source, count, avg_conf in source_stats:
                conf_level = source.replace(
                    'apify_', '').replace('_confidence', '')
                print(
                    f"  {conf_level.title()}: {count} images (avg confidence: {avg_conf:.2f})")

        if attraction_stats:
            print("\nTop Attractions:")
            for city, attraction, count, avg_conf in attraction_stats:
                print(
                    f"  {attraction} ({city}): {count} images (confidence: {avg_conf:.2f})")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")


if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI Apify Dataset Processor")
    print("Processing Google Images scraper results...")
    print("=" * 60)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting Apify dataset processing...")

    # Process the dataset
    # You can adjust these parameters:
    # - confidence_threshold: minimum confidence to include (0.0 = all, 0.6 = medium+, 0.8 = high only)
    # - max_images_per_attraction: limit images per attraction to avoid spam

    results = process_apify_dataset(
        'dataset_google-images-scraper_2025-10-18_14-03-15-264.json',
        confidence_threshold=0.5,  # Include medium+ confidence
        max_images_per_attraction=5  # Max 5 images per attraction for testing
    )

    print(f"\n📊 Processing Results:")
    print(f"   📁 Categories processed: {results['categories']}")
    print(f"   🖼️ Images processed: {results['total_processed']}")
    print(f"   ✅ Successfully added: {results['successful']}")
    print(f"   ❌ Failed: {results['failed']}")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 Apify dataset processing completed!")
    print("=" * 60)

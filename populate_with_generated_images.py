"""
ViamigoTravelAI Image Database Loader - Local Generation Version
Creates beautiful placeholder images locally to populate the database
"""
import psycopg2
import os
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
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


def create_attraction_image(city, attraction_name, width=400, height=300):
    """Create a beautiful placeholder image for an attraction"""
    try:
        # Color schemes for different cities
        city_colors = {
            # Brown/Gold
            'Roma': {'bg': (139, 69, 19), 'accent': (255, 215, 0), 'text': (255, 255, 255)},
            # Purple/Pink
            'Firenze': {'bg': (128, 0, 128), 'accent': (255, 20, 147), 'text': (255, 255, 255)},
            # Blue/Light Blue
            'Venezia': {'bg': (0, 100, 139), 'accent': (135, 206, 235), 'text': (255, 255, 255)},
            # Dark Gray/Silver
            'Milano': {'bg': (47, 79, 79), 'accent': (192, 192, 192), 'text': (255, 255, 255)},
            # Red/Orange
            'Napoli': {'bg': (255, 69, 0), 'accent': (255, 165, 0), 'text': (255, 255, 255)},
            # Green/Light Green
            'Pisa': {'bg': (34, 139, 34), 'accent': (144, 238, 144), 'text': (255, 255, 255)},
            # Brown/Pink
            'Bologna': {'bg': (165, 42, 42), 'accent': (255, 182, 193), 'text': (255, 255, 255)},
        }

        colors = city_colors.get(city, {'bg': (70, 130, 180), 'accent': (
            173, 216, 230), 'text': (255, 255, 255)})

        # Create image with gradient background
        img = Image.new('RGB', (width, height), colors['bg'])
        draw = ImageDraw.Draw(img)

        # Create gradient effect
        for i in range(height):
            alpha = i / height
            r = int(colors['bg'][0] * (1 - alpha) +
                    colors['accent'][0] * alpha)
            g = int(colors['bg'][1] * (1 - alpha) +
                    colors['accent'][1] * alpha)
            b = int(colors['bg'][2] * (1 - alpha) +
                    colors['accent'][2] * alpha)
            draw.line([(0, i), (width, i)], fill=(r, g, b))

        # Add decorative elements
        # Draw corner triangles
        triangle_size = 40
        draw.polygon([(0, 0), (triangle_size, 0),
                     (0, triangle_size)], fill=colors['accent'])
        draw.polygon([(width, 0), (width-triangle_size, 0),
                     (width, triangle_size)], fill=colors['accent'])
        draw.polygon([(0, height), (triangle_size, height),
                     (0, height-triangle_size)], fill=colors['accent'])
        draw.polygon([(width, height), (width-triangle_size, height),
                     (width, height-triangle_size)], fill=colors['accent'])

        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 24)
            font_small = ImageFont.truetype(
                "/usr/share/fonts/dejavu/DejaVuSans.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Add city name at top
        city_text = f"📍 {city}"
        city_bbox = draw.textbbox((0, 0), city_text, font=font_small)
        city_x = (width - (city_bbox[2] - city_bbox[0])) // 2
        city_y = 30

        # Add shadow for better readability
        draw.text((city_x + 2, city_y + 2), city_text,
                  fill=(0, 0, 0, 128), font=font_small)
        draw.text((city_x, city_y), city_text,
                  fill=colors['text'], font=font_small)

        # Add attraction name in center
        # Split long names into multiple lines
        words = attraction_name.split()
        if len(' '.join(words)) > 20:
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            attraction_lines = [line1, line2]
        else:
            attraction_lines = [attraction_name]

        # Draw attraction name
        total_height = len(attraction_lines) * 35
        start_y = (height - total_height) // 2 + 20

        for i, line in enumerate(attraction_lines):
            line_bbox = draw.textbbox((0, 0), line, font=font_large)
            line_x = (width - (line_bbox[2] - line_bbox[0])) // 2
            line_y = start_y + i * 35

            # Add shadow
            draw.text((line_x + 2, line_y + 2), line,
                      fill=(0, 0, 0, 128), font=font_large)
            draw.text((line_x, line_y), line,
                      fill=colors['text'], font=font_large)

        # Add decorative icon based on attraction type
        icon = get_attraction_icon(attraction_name)
        icon_bbox = draw.textbbox((0, 0), icon, font=font_large)
        icon_x = (width - (icon_bbox[2] - icon_bbox[0])) // 2
        icon_y = height - 60

        draw.text((icon_x + 2, icon_y + 2), icon,
                  fill=(0, 0, 0, 128), font=font_large)
        draw.text((icon_x, icon_y), icon,
                  fill=colors['accent'], font=font_large)

        # Convert to bytes
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
        logger.error(f"Error creating image for {attraction_name}: {e}")
        return None


def get_attraction_icon(attraction_name):
    """Get appropriate icon for attraction type"""
    name_lower = attraction_name.lower()

    if 'duomo' in name_lower or 'basilica' in name_lower or 'chiesa' in name_lower:
        return '⛪'
    elif 'ponte' in name_lower:
        return '🌉'
    elif 'palazzo' in name_lower or 'castel' in name_lower:
        return '🏰'
    elif 'fontana' in name_lower:
        return '⛲'
    elif 'piazza' in name_lower:
        return '🏛️'
    elif 'torre' in name_lower:
        return '🗼'
    elif 'foro' in name_lower:
        return '🏛️'
    elif 'canal' in name_lower:
        return '🛶'
    else:
        return '🏛️'


def add_attraction_image(city, attraction_name, attraction_qid=None, source="generated"):
    """Add a generated attraction image to the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False

        with conn.cursor() as cur:
            # Check if image already exists
            cur.execute("""
                SELECT id FROM attraction_images 
                WHERE LOWER(city) = LOWER(%s) AND LOWER(attraction_name) = LOWER(%s)
            """, (city, attraction_name))

            existing = cur.fetchone()
            if existing:
                logger.info(
                    f"Image already exists for {attraction_name} in {city}")
                return True

        # Create the image
        logger.info(f"Creating image for {attraction_name} in {city}...")
        image_data = create_attraction_image(city, attraction_name)

        if not image_data:
            logger.error(f"Failed to create image for {attraction_name}")
            return False

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(image_data['bytes']).hexdigest()

        with conn.cursor() as cur:
            # Insert new image
            cur.execute("""
                INSERT INTO attraction_images 
                (source, city, attraction_name, attraction_qid, original_url,
                 img_bytes, mime_type, width, height, sha256_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                source, city, attraction_name, attraction_qid, 'generated://local',
                image_data['bytes'], image_data['mime_type'],
                image_data['width'], image_data['height'], sha256_hash
            ))

            conn.commit()
            logger.info(
                f"✅ Added generated image for {attraction_name} ({image_data['size']} bytes)")
            return True

    except Exception as e:
        logger.error(f"Error adding image for {attraction_name}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def load_italian_attractions():
    """Load generated images for Italian attractions"""

    attractions = [
        # Roma
        {'city': 'Roma', 'name': 'Fontana di Trevi', 'qid': 'Q186579'},
        {'city': 'Roma', 'name': 'Pantheon', 'qid': 'Q37986'},
        {'city': 'Roma', 'name': 'Foro Romano', 'qid': 'Q31870'},
        {'city': 'Roma', 'name': 'Castel Sant Angelo', 'qid': 'Q50158'},
        {'city': 'Roma', 'name': 'Piazza Navona', 'qid': 'Q33965'},
        {'city': 'Roma', 'name': 'Basilica di San Pietro', 'qid': 'Q12512'},

        # Firenze
        {'city': 'Firenze', 'name': 'Duomo di Firenze', 'qid': 'Q118674'},
        {'city': 'Firenze', 'name': 'Ponte Vecchio', 'qid': 'Q172408'},
        {'city': 'Firenze', 'name': 'Palazzo Pitti', 'qid': 'Q615912'},
        {'city': 'Firenze', 'name': 'Uffizi', 'qid': 'Q51252'},
        {'city': 'Firenze', 'name': 'Piazzale Michelangelo', 'qid': 'Q1134103'},

        # Venezia
        {'city': 'Venezia', 'name': 'Piazza San Marco', 'qid': 'Q166140'},
        {'city': 'Venezia', 'name': 'Ponte di Rialto', 'qid': 'Q597851'},
        {'city': 'Venezia', 'name': 'Palazzo Ducale', 'qid': 'Q621728'},
        {'city': 'Venezia', 'name': 'Basilica di San Marco', 'qid': 'Q173058'},
        {'city': 'Venezia', 'name': 'Canal Grande', 'qid': 'Q185983'},

        # Milano
        {'city': 'Milano', 'name': 'Duomo di Milano', 'qid': 'Q132053'},
        {'city': 'Milano', 'name': 'Castello Sforzesco', 'qid': 'Q178679'},
        {'city': 'Milano', 'name': 'La Scala', 'qid': 'Q11106'},
        {'city': 'Milano', 'name': 'Navigli', 'qid': 'Q1345003'},

        # Napoli
        {'city': 'Napoli', 'name': 'Castel Nuovo', 'qid': 'Q389331'},
        {'city': 'Napoli', 'name': 'Castel dell Ovo', 'qid': 'Q925094'},
        {'city': 'Napoli', 'name': 'Spaccanapoli', 'qid': 'Q752361'},

        # Pisa
        {'city': 'Pisa', 'name': 'Torre di Pisa', 'qid': 'Q39054'},
        {'city': 'Pisa', 'name': 'Piazza dei Miracoli', 'qid': 'Q332415'},

        # Bologna
        {'city': 'Bologna', 'name': 'Due Torri', 'qid': 'Q843263'},
        {'city': 'Bologna', 'name': 'Piazza Maggiore', 'qid': 'Q632285'},

        # Additional cities
        {'city': 'Genova', 'name': 'Via del Campo', 'qid': 'Q3556823'},
        {'city': 'Torino', 'name': 'Mole Antonelliana', 'qid': 'Q2112088'},
        {'city': 'Palermo', 'name': 'Cattedrale di Palermo', 'qid': 'Q1052475'},
    ]

    successful = 0
    failed = 0

    logger.info(
        f"🖼️ Starting to generate {len(attractions)} Italian attraction images...")

    for i, attraction in enumerate(attractions, 1):
        logger.info(
            f"[{i}/{len(attractions)}] Processing {attraction['name']} in {attraction['city']}")

        success = add_attraction_image(
            city=attraction['city'],
            attraction_name=attraction['name'],
            attraction_qid=attraction['qid'],
            source='viamigo_generated'
        )

        if success:
            successful += 1
        else:
            failed += 1

        # Small delay
        time.sleep(0.1)

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
    print("🖼️ ViamigoTravelAI Image Database Loader - Local Generation")
    print("=" * 65)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting image generation process...")
    successful, failed = load_italian_attractions()

    print(f"\n📊 Generation Results:")
    print(f"   ✅ Successfully generated: {successful} images")
    print(f"   ❌ Failed: {failed} images")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 Image generation process completed!")
    print("=" * 65)

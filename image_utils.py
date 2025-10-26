"""
Image utility functions for ViamigoTravelAI
"""
import os
import base64
from io import BytesIO
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Get database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def get_local_image_url(city, attraction_name):
    """Get local database image URL for an attraction"""
    try:
        conn = get_db_connection()
        if not conn:
            return None

        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM attraction_images 
                WHERE LOWER(city) = LOWER(%s) 
                AND LOWER(attraction_name) ILIKE LOWER(%s)
                LIMIT 1
            """, (city, f"%{attraction_name}%"))

            result = cur.fetchone()
            if result:
                return f"/api/images/attraction/{result[0]}"

        conn.close()
        return None
    except Exception as e:
        print(f"Error getting local image: {e}")
        return None


def create_placeholder_image_data_url(city, attraction):
    """Create a placeholder image data URL"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create a simple placeholder image
        width, height = 400, 300
        img = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(img)

        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Draw city and attraction name
        city_text = f"📍 {city}"
        attraction_text = f"🏛️ {attraction}"

        # Calculate text position
        city_bbox = draw.textbbox((0, 0), city_text, font=font)
        attraction_bbox = draw.textbbox((0, 0), attraction_text, font=font)

        city_x = (width - (city_bbox[2] - city_bbox[0])) // 2
        city_y = height // 2 - 30

        attraction_x = (width - (attraction_bbox[2] - attraction_bbox[0])) // 2
        attraction_y = height // 2 + 10

        # Draw text
        draw.text((city_x, city_y), city_text, fill='#666666', font=font)
        draw.text((attraction_x, attraction_y),
                  attraction_text, fill='#333333', font=font)

        # Convert to base64 data URL
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/jpeg;base64,{img_str}"

    except Exception as e:
        print(f"Error creating placeholder: {e}")
        # Return a minimal SVG placeholder
        svg = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="200" y="140" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">📍 {city}</text>
            <text x="200" y="170" text-anchor="middle" font-family="Arial" font-size="18" fill="#333">🏛️ {attraction}</text>
        </svg>'''
        svg_base64 = base64.b64encode(svg.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_base64}"


def get_image_for_attraction(city, attraction_name, fallback_url=None):
    """
    Get the best available image for an attraction
    Priority: 1) Local database, 2) Provided fallback URL, 3) Placeholder
    """
    # Try local database first
    local_url = get_local_image_url(city, attraction_name)
    if local_url:
        return {
            'type': 'local',
            'url': local_url,
            'source': 'database'
        }

    # Try fallback URL if provided
    if fallback_url:
        return {
            'type': 'external',
            'url': fallback_url,
            'source': 'external'
        }

    # Create placeholder
    placeholder_url = create_placeholder_image_data_url(city, attraction_name)
    return {
        'type': 'placeholder',
        'url': placeholder_url,
        'source': 'generated'
    }

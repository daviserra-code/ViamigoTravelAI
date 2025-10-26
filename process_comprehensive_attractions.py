#!/usr/bin/env python3
"""
Comprehensive Attractions Dataset Processor for ViamigoTravelAI
Processes the custom Apify actor dataset with OSM + Wikidata + Commons integration
"""
import json
import os
import psycopg2
import requests
from PIL import Image
from io import BytesIO
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ComprehensiveAttractionsProcessor:
    def __init__(self, db_url: str = None):
        """Initialize the processor with database connection"""
        self.db_url = db_url or os.getenv(
            'DATABASE_URL') or os.getenv('NEON_POSTGRES_POOLED_URL')
        if not self.db_url:
            raise ValueError("Database URL not provided")

        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0

        # Enhanced mapping for attraction types
        self.attraction_mapping = {
            'tourism:attraction': 'Tourist Attraction',
            'historic:monument': 'Historic Monument',
            'historic:ruins': 'Historic Ruins',
            'historic:castle': 'Castle',
            'historic:church': 'Church',
            'historic:palace': 'Palace',
            'historic:villa': 'Villa',
            'historic:fountain': 'Fountain',
            'historic:sarcophagus': 'Ancient Artifact',
            'historic:tower': 'Tower',
            'historic:building': 'Historic Building',
            'amenity:place_of_worship': 'Place of Worship',
            'amenity:theatre': 'Theatre',
            'amenity:arts_centre': 'Arts Centre',
            'leisure:park': 'Park',
            'natural:water': 'Natural Water Feature',
            'building:cathedral': 'Cathedral',
            'building:church': 'Church',
            'man_made:tower': 'Tower'
        }

    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(self.db_url)

    def setup_enhanced_tables(self):
        """Create enhanced tables for comprehensive attraction data"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Enhanced attractions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS comprehensive_attractions (
                        id SERIAL PRIMARY KEY,
                        city VARCHAR(100) NOT NULL,
                        name VARCHAR(500),
                        raw_name VARCHAR(500),
                        description TEXT,
                        category VARCHAR(100),
                        attraction_type VARCHAR(100),
                        
                        -- Coordinates
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        
                        -- OSM Data
                        osm_id BIGINT,
                        osm_type VARCHAR(20),
                        osm_tags JSONB,
                        
                        -- Wikidata/Wikipedia
                        wikidata_id VARCHAR(50),
                        wikipedia_url VARCHAR(500),
                        
                        -- Image Data
                        has_image BOOLEAN DEFAULT FALSE,
                        image_url VARCHAR(1000),
                        thumb_url VARCHAR(1000),
                        original_url VARCHAR(1000),
                        image_creator VARCHAR(500),
                        image_license VARCHAR(100),
                        image_attribution TEXT,
                        
                        -- Source tracking
                        source_osm BOOLEAN DEFAULT FALSE,
                        source_wikidata BOOLEAN DEFAULT FALSE,
                        source_commons BOOLEAN DEFAULT FALSE,
                        
                        -- Processing metadata
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Indexes
                        UNIQUE(osm_id, osm_type)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_comp_attractions_city ON comprehensive_attractions(city);
                    CREATE INDEX IF NOT EXISTS idx_comp_attractions_coords ON comprehensive_attractions(latitude, longitude);
                    CREATE INDEX IF NOT EXISTS idx_comp_attractions_category ON comprehensive_attractions(category);
                    CREATE INDEX IF NOT EXISTS idx_comp_attractions_has_image ON comprehensive_attractions(has_image);
                    CREATE INDEX IF NOT EXISTS idx_comp_attractions_wikidata ON comprehensive_attractions(wikidata_id);
                """)

                # Enhanced images table (reuse existing but ensure compatibility)
                cur.execute("""
                    -- Add new columns to existing attraction_images if they don't exist
                    DO $$ 
                    BEGIN
                        BEGIN
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS source_actor VARCHAR(100) DEFAULT 'comprehensive';
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS osm_id BIGINT;
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS wikidata_id VARCHAR(50);
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS license VARCHAR(100);
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS creator VARCHAR(500);
                            ALTER TABLE attraction_images ADD COLUMN IF NOT EXISTS attribution TEXT;
                        EXCEPTION
                            WHEN duplicate_column THEN NULL;
                        END;
                    END $$;
                """)

                conn.commit()
                print("✅ Enhanced database tables created/updated")

    def process_image(self, image_data: Dict, attraction_name: str) -> Optional[Tuple[bytes, str, int]]:
        """Download and process image from the dataset"""
        if not image_data or not image_data.get('thumbUrl'):
            return None

        try:
            thumb_url = image_data['thumbUrl']
            response = requests.get(thumb_url, timeout=10, headers={
                'User-Agent': 'ViamigoTravelAI/1.0 (Educational Research)'
            })

            if response.status_code != 200:
                print(f"❌ Failed to download image: {response.status_code}")
                return None

            # Process image
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if too large (max 1280px width)
            if img.width > 1280:
                ratio = 1280 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((1280, new_height), Image.Resampling.LANCZOS)

            # Save as JPEG
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            image_bytes = output.getvalue()

            # Generate hash for deduplication
            image_hash = hashlib.sha256(image_bytes).hexdigest()

            return image_bytes, image_hash, len(image_bytes)

        except Exception as e:
            print(f"❌ Error processing image for {attraction_name}: {e}")
            return None

    def calculate_confidence(self, record: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        confidence = 0.0

        # Base score for having a name
        if record.get('name') and record['name'].strip():
            confidence += 0.3

        # Wikidata presence (high value indicator)
        if record.get('wikidata'):
            confidence += 0.3

        # Image presence
        if record.get('image', {}).get('thumbUrl'):
            confidence += 0.2

        # Description
        if record.get('description') and record['description'].strip():
            confidence += 0.1

        # Wikipedia reference
        if record.get('wikipedia'):
            confidence += 0.1

        return min(confidence, 1.0)

    def map_attraction_type(self, record: Dict) -> str:
        """Map category and OSM tags to attraction type"""
        category = record.get('category', '')
        tags = record.get('tags', {})

        # Direct category mapping
        if category in self.attraction_mapping:
            return self.attraction_mapping[category]

        # Check OSM tags for more specific types
        tourism = tags.get('tourism', '')
        historic = tags.get('historic', '')
        amenity = tags.get('amenity', '')
        building = tags.get('building', '')

        if tourism == 'attraction':
            return 'Tourist Attraction'
        elif historic:
            return f"Historic {historic.title()}"
        elif amenity in ['place_of_worship', 'theatre', 'arts_centre']:
            return amenity.replace('_', ' ').title()
        elif building in ['cathedral', 'church']:
            return building.title()

        return 'Attraction'

    def process_record(self, record: Dict) -> bool:
        """Process a single attraction record"""
        try:
            # Skip records without proper names (but allow wikidata entries)
            if not record.get('name') and not record.get('wikidata'):
                return False

            # Calculate confidence
            confidence = self.calculate_confidence(record)

            # Skip very low confidence records
            if confidence < 0.2:
                return False

            name = record.get('name', '').strip(
            ) or f"Unnamed {record.get('category', 'Attraction')}"
            city = record.get('city', '')

            # Insert into comprehensive_attractions table
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO comprehensive_attractions (
                            city, name, raw_name, description, category, attraction_type,
                            latitude, longitude, osm_id, osm_type, osm_tags,
                            wikidata_id, wikipedia_url, has_image, image_url, 
                            thumb_url, original_url, image_creator, image_license, image_attribution,
                            source_osm, source_wikidata, source_commons
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (osm_id, osm_type) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        city,
                        name,
                        record.get('rawName', ''),
                        record.get('description', ''),
                        record.get('category', ''),
                        self.map_attraction_type(record),
                        record.get('coords', {}).get('lat'),
                        record.get('coords', {}).get('lon'),
                        record.get('osmId'),
                        record.get('osmType'),
                        json.dumps(record.get('tags', {})),
                        record.get('wikidata'),
                        record.get('wikipedia'),
                        bool(record.get('image', {}).get('thumbUrl')),
                        record.get('image', {}).get('thumbUrl'),
                        record.get('image', {}).get('thumbUrl'),
                        record.get('image', {}).get('originalUrl'),
                        record.get('image', {}).get('creator'),
                        record.get('image', {}).get('license'),
                        record.get('image', {}).get('attribution'),
                        record.get('source', {}).get('osm', False),
                        record.get('source', {}).get('wikidata', False),
                        record.get('source', {}).get('commons', False)
                    ))

                    attraction_id = cur.fetchone()[0]

                    # Process and store image if available
                    image_data = record.get('image', {})
                    if image_data and image_data.get('thumbUrl'):
                        image_result = self.process_image(image_data, name)
                        if image_result:
                            image_bytes, image_hash, image_size = image_result

                            # Insert into attraction_images table
                            cur.execute("""
                                INSERT INTO attraction_images (
                                    source, city, attraction_name, img_bytes, 
                                    confidence_score, original_title, content_url,
                                    source_actor, osm_id, wikidata_id, license, creator, attribution,
                                    sha256_hash, fetched_at, mime_type
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'image/jpeg'
                                ) ON CONFLICT (sha256_hash) DO NOTHING
                            """, (
                                'comprehensive_actor',  # source
                                city,
                                name,
                                psycopg2.Binary(image_bytes),
                                confidence,
                                name,
                                image_data.get('thumbUrl'),
                                'comprehensive',
                                record.get('osmId'),
                                record.get('wikidata'),
                                image_data.get('license'),
                                image_data.get('creator'),
                                image_data.get('attribution'),
                                image_hash
                            ))

                conn.commit()
                return True

        except Exception as e:
            print(
                f"❌ Error processing record {record.get('name', 'Unknown')}: {e}")
            return False

    def process_dataset(self, json_file_path: str, limit: int = None):
        """Process the comprehensive attractions dataset"""
        print(
            f"🚀 Processing comprehensive attractions dataset: {json_file_path}")

        # Setup database tables
        self.setup_enhanced_tables()

        # Load and process data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📊 Dataset loaded: {len(data)} attractions")

        # Apply limit if specified
        if limit:
            data = data[:limit]
            print(f"🔢 Processing limited to {limit} records")

        # Process each record
        for i, record in enumerate(data, 1):
            if i % 50 == 0:
                print(
                    f"📈 Progress: {i}/{len(data)} ({(i/len(data)*100):.1f}%)")

            success = self.process_record(record)
            if success:
                self.processed_count += 1
            else:
                self.skipped_count += 1

            # Small delay to avoid overwhelming the system
            time.sleep(0.01)

        # Final report
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"   ✅ Processed: {self.processed_count}")
        print(f"   ⏭️  Skipped: {self.skipped_count}")
        print(f"   ❌ Errors: {self.error_count}")
        print(
            f"   📊 Success Rate: {(self.processed_count/(self.processed_count+self.skipped_count)*100):.1f}%")


def main():
    """Main execution function"""
    json_file = 'dataset_tourism-it-attractions_2025-10-18_20-46-30-223.json'

    if not os.path.exists(json_file):
        print(f"❌ Dataset file not found: {json_file}")
        return

    processor = ComprehensiveAttractionsProcessor()

    # Process the complete dataset (remove limit for full processing)
    processor.process_dataset(json_file)  # Process all 1800 attractions


if __name__ == "__main__":
    main()

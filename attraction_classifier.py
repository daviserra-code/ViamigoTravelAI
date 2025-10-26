"""
ViamigoTravelAI Attraction Image Classifier
Maps scraped images to specific attractions using multiple identification methods
"""
import json
import re
from typing import Dict, List, Tuple, Optional


class AttractionImageClassifier:
    def __init__(self):
        # Define attraction keywords for major Italian cities
        self.attraction_keywords = {
            # Roma
            'Colosseo': ['colosseum', 'colosseo', 'amphitheatre rome', 'flavian amphitheatre'],
            'Fontana di Trevi': ['trevi fountain', 'fontana di trevi', 'trevi'],
            'Pantheon': ['pantheon rome', 'pantheon roma'],
            'Foro Romano': ['roman forum', 'foro romano', 'forum rome'],
            'Castel Sant Angelo': ['castel sant angelo', 'mausoleum hadrian', 'sant angelo castle'],
            'Basilica San Pietro': ['st peter basilica', 'basilica san pietro', 'vatican basilica'],

            # Milano
            'Duomo Milano': ['milan cathedral', 'duomo milano', 'cathedral milan'],
            'La Scala': ['la scala', 'scala opera', 'teatro alla scala'],
            'Castello Sforzesco': ['sforza castle', 'castello sforzesco'],
            'Galleria Vittorio Emanuele': ['galleria vittorio emanuele', 'milan gallery'],

            # Firenze
            'Duomo Firenze': ['florence cathedral', 'duomo firenze', 'santa maria del fiore'],
            'Ponte Vecchio': ['ponte vecchio', 'old bridge florence'],
            'Uffizi': ['uffizi gallery', 'uffizi museum', 'galleria uffizi'],
            'Palazzo Pitti': ['pitti palace', 'palazzo pitti'],

            # Venezia
            'Piazza San Marco': ['st mark square', 'piazza san marco'],
            'Basilica San Marco': ['st mark basilica', 'basilica san marco'],
            'Palazzo Ducale': ['doge palace', 'palazzo ducale', 'doges palace'],
            'Ponte di Rialto': ['rialto bridge', 'ponte rialto'],
            'Canal Grande': ['grand canal', 'canal grande'],

            # Pisa
            'Torre di Pisa': ['leaning tower', 'torre pendente', 'tower of pisa', 'pisa tower'],
            'Duomo Pisa': ['pisa cathedral', 'duomo pisa'],

            # Verona
            'Arena di Verona': ['verona arena', 'arena verona', 'amphitheatre verona'],
            'Casa di Giulietta': ['juliet house', 'casa giulietta', 'juliet balcony'],

            # Bergamo
            'Mura Veneziane': ['venetian walls', 'mura veneziane', 'walls bergamo'],
            'Citta Alta': ['upper town', 'citta alta', 'old town bergamo'],

            # Napoli
            'Vesuvio': ['mount vesuvius', 'vesuvio', 'volcano naples'],
            'Pompei': ['pompeii', 'pompei', 'archaeological site'],
            'Castel dell Ovo': ['castel dell ovo', 'egg castle'],
        }

        # City mappings
        self.city_mappings = {
            'roma': 'Roma',
            'rome': 'Roma',
            'milan': 'Milano',
            'milano': 'Milano',
            'florence': 'Firenze',
            'firenze': 'Firenze',
            'venice': 'Venezia',
            'venezia': 'Venezia',
            'pisa': 'Pisa',
            'verona': 'Verona',
            'bergamo': 'Bergamo',
            'naples': 'Napoli',
            'napoli': 'Napoli'
        }

    def classify_image(self, image_data: Dict) -> Tuple[str, str, float]:
        """
        Classify an image to determine city and specific attraction

        Returns: (city, attraction, confidence_score)
        """
        title = image_data.get('title', '').lower()
        content_url = image_data.get('contentUrl', '').lower()
        query = image_data.get('query', '').lower()

        # Normalize city from query
        city = self._normalize_city(query)

        # Try to identify specific attraction
        attraction, confidence = self._identify_attraction(
            title, content_url, city)

        return city, attraction, confidence

    def _normalize_city(self, query: str) -> str:
        """Normalize city name"""
        query_clean = query.lower().strip()
        return self.city_mappings.get(query_clean, query.title())

    def _identify_attraction(self, title: str, content_url: str, city: str) -> Tuple[str, float]:
        """Identify specific attraction from title and URL"""

        # Combine title and URL for analysis
        text_to_analyze = f"{title} {content_url}"

        best_match = None
        highest_score = 0.0

        # Check each attraction's keywords
        for attraction, keywords in self.attraction_keywords.items():
            score = 0.0
            matches = 0

            for keyword in keywords:
                if keyword in text_to_analyze:
                    matches += 1
                    # Weight longer, more specific keywords higher
                    keyword_weight = len(keyword.split()) * 0.2 + 0.1
                    score += keyword_weight

            # Bonus for multiple keyword matches
            if matches > 1:
                score *= 1.5

            # City relevance check
            if self._attraction_belongs_to_city(attraction, city):
                score *= 1.2
            else:
                score *= 0.3  # Penalty for wrong city

            if score > highest_score:
                highest_score = score
                best_match = attraction

        # Determine confidence level
        if highest_score > 0.8:
            confidence = 0.9  # High confidence
        elif highest_score > 0.4:
            confidence = 0.7  # Medium confidence
        elif highest_score > 0.1:
            confidence = 0.5  # Low confidence
        else:
            confidence = 0.2  # Very low confidence - generic city image
            best_match = f"{city}_generic"

        return best_match or f"{city}_generic", confidence

    def _attraction_belongs_to_city(self, attraction: str, city: str) -> bool:
        """Check if attraction belongs to the given city"""
        city_attractions = {
            'Roma': ['Colosseo', 'Fontana di Trevi', 'Pantheon', 'Foro Romano', 'Castel Sant Angelo', 'Basilica San Pietro'],
            'Milano': ['Duomo Milano', 'La Scala', 'Castello Sforzesco', 'Galleria Vittorio Emanuele'],
            'Firenze': ['Duomo Firenze', 'Ponte Vecchio', 'Uffizi', 'Palazzo Pitti'],
            'Venezia': ['Piazza San Marco', 'Basilica San Marco', 'Palazzo Ducale', 'Ponte di Rialto', 'Canal Grande'],
            'Pisa': ['Torre di Pisa', 'Duomo Pisa'],
            'Verona': ['Arena di Verona', 'Casa di Giulietta'],
            'Bergamo': ['Mura Veneziane', 'Citta Alta'],
            'Napoli': ['Vesuvio', 'Pompei', 'Castel dell Ovo']
        }

        return attraction in city_attractions.get(city, [])

    def classify_dataset(self, dataset_path: str) -> Dict:
        """Classify entire dataset and return statistics"""
        with open(dataset_path, 'r') as f:
            data = json.load(f)

        results = {
            'total_images': len(data),
            'classifications': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0, 'very_low': 0},
            'by_city': {},
            'by_attraction': {}
        }

        for image in data:
            city, attraction, confidence = self.classify_image(image)

            # Store classification
            classification_key = f"{city}_{attraction}"
            if classification_key not in results['classifications']:
                results['classifications'][classification_key] = []

            results['classifications'][classification_key].append({
                'title': image.get('title', ''),
                'imageUrl': image.get('imageUrl', ''),
                'confidence': confidence
            })

            # Update statistics
            if confidence >= 0.8:
                results['confidence_distribution']['high'] += 1
            elif confidence >= 0.6:
                results['confidence_distribution']['medium'] += 1
            elif confidence >= 0.4:
                results['confidence_distribution']['low'] += 1
            else:
                results['confidence_distribution']['very_low'] += 1

            # By city
            if city not in results['by_city']:
                results['by_city'][city] = 0
            results['by_city'][city] += 1

            # By attraction
            if attraction not in results['by_attraction']:
                results['by_attraction'][attraction] = 0
            results['by_attraction'][attraction] += 1

        return results


def analyze_current_dataset():
    """Analyze the current test dataset"""
    classifier = AttractionImageClassifier()
    results = classifier.classify_dataset(
        'dataset_google-images-scraper_2025-10-18_14-03-15-264.json')

    print("🎯 ATTRACTION CLASSIFICATION RESULTS")
    print("=" * 60)
    print(f"Total images analyzed: {results['total_images']}")

    print(f"\n📊 Confidence Distribution:")
    for level, count in results['confidence_distribution'].items():
        percentage = (count / results['total_images']) * 100
        print(f"  {level.title()}: {count} images ({percentage:.1f}%)")

    print(f"\n📍 By City:")
    for city, count in sorted(results['by_city'].items()):
        print(f"  {city}: {count} images")

    print(f"\n🏛️ By Attraction (top 10):")
    top_attractions = sorted(
        results['by_attraction'].items(), key=lambda x: x[1], reverse=True)[:10]
    for attraction, count in top_attractions:
        print(f"  {attraction}: {count} images")

    print(f"\n🔍 Sample Classifications:")
    for classification, images in list(results['classifications'].items())[:5]:
        print(f"\n  {classification}:")
        for img in images[:3]:
            print(
                f"    • {img['title'][:50]}... (confidence: {img['confidence']:.2f})")

    return results


if __name__ == "__main__":
    results = analyze_current_dataset()

"""
🗺️ GEOGRAPHIC CLUSTERING SYSTEM
Groups nearby cities for efficient batch scraping
"""
from typing import List, Dict, Tuple, Set
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class GeographicClusterer:
    """Clusters cities by geographic proximity for efficient scraping"""
    
    def __init__(self):
        # Major Italian cities with coordinates
        self.italian_cities = {
            'Roma': {'lat': 41.9028, 'lng': 12.4964, 'region': 'Lazio'},
            'Milano': {'lat': 45.4642, 'lng': 9.1900, 'region': 'Lombardia'},
            'Napoli': {'lat': 40.8518, 'lng': 14.2681, 'region': 'Campania'},
            'Torino': {'lat': 45.0703, 'lng': 7.6869, 'region': 'Piemonte'},
            'Palermo': {'lat': 38.1157, 'lng': 13.3615, 'region': 'Sicilia'},
            'Genova': {'lat': 44.4056, 'lng': 8.9463, 'region': 'Liguria'},
            'Bologna': {'lat': 44.4949, 'lng': 11.3426, 'region': 'Emilia-Romagna'},
            'Firenze': {'lat': 43.7696, 'lng': 11.2558, 'region': 'Toscana'},
            'Bari': {'lat': 41.1171, 'lng': 16.8719, 'region': 'Puglia'},
            'Catania': {'lat': 37.5079, 'lng': 15.0830, 'region': 'Sicilia'},
            'Venezia': {'lat': 45.4408, 'lng': 12.3155, 'region': 'Veneto'},
            'Verona': {'lat': 45.4384, 'lng': 10.9916, 'region': 'Veneto'},
            'Messina': {'lat': 38.1937, 'lng': 15.5542, 'region': 'Sicilia'},
            'Padova': {'lat': 45.4064, 'lng': 11.8768, 'region': 'Veneto'},
            'Trieste': {'lat': 45.6495, 'lng': 13.7768, 'region': 'Friuli-Venezia Giulia'},
            'Brescia': {'lat': 45.5416, 'lng': 10.2118, 'region': 'Lombardia'},
            'Parma': {'lat': 44.8015, 'lng': 10.3279, 'region': 'Emilia-Romagna'},
            'Prato': {'lat': 43.8777, 'lng': 11.1022, 'region': 'Toscana'},
            'Modena': {'lat': 44.6471, 'lng': 10.9252, 'region': 'Emilia-Romagna'},
            'Reggio Calabria': {'lat': 38.1080, 'lng': 15.6435, 'region': 'Calabria'},
            'Siena': {'lat': 43.3188, 'lng': 11.3308, 'region': 'Toscana'},
            'Pisa': {'lat': 43.7228, 'lng': 10.4017, 'region': 'Toscana'},
            'Perugia': {'lat': 43.1107, 'lng': 12.3908, 'region': 'Umbria'},
            'Livorno': {'lat': 43.5485, 'lng': 10.3106, 'region': 'Toscana'},
            'Cagliari': {'lat': 39.2238, 'lng': 9.1217, 'region': 'Sardegna'},
        }
        
        # Regional groupings
        self.regions = self._build_regional_clusters()
    
    def _build_regional_clusters(self) -> Dict[str, List[str]]:
        """Group cities by region"""
        regions = {}
        for city, data in self.italian_cities.items():
            region = data['region']
            if region not in regions:
                regions[region] = []
            regions[region].append(city)
        return regions
    
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points in km using Haversine formula
        """
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def find_nearby_cities(self, city: str, radius_km: float = 100) -> List[Tuple[str, float]]:
        """
        Find cities within radius_km of the given city
        
        Returns:
            List of (city_name, distance_km) sorted by distance
        """
        if city not in self.italian_cities:
            logger.warning(f"City {city} not in database")
            return []
        
        base = self.italian_cities[city]
        nearby = []
        
        for other_city, coords in self.italian_cities.items():
            if other_city == city:
                continue
            
            distance = self.haversine_distance(
                base['lat'], base['lng'],
                coords['lat'], coords['lng']
            )
            
            if distance <= radius_km:
                nearby.append((other_city, distance))
        
        # Sort by distance
        nearby.sort(key=lambda x: x[1])
        
        return nearby
    
    def create_scraping_clusters(self, cities: List[str], max_cluster_radius: float = 150) -> List[Dict]:
        """
        Create efficient scraping clusters from a list of cities
        
        Args:
            cities: List of city names to cluster
            max_cluster_radius: Maximum radius for a cluster in km
        
        Returns:
            List of cluster dicts with cities and center point
        """
        remaining = set(cities)
        clusters = []
        
        while remaining:
            # Pick a city from remaining
            center_city = remaining.pop()
            
            if center_city not in self.italian_cities:
                continue
            
            # Find nearby cities
            nearby = self.find_nearby_cities(center_city, max_cluster_radius)
            
            # Add cities to cluster
            cluster_cities = [center_city]
            for nearby_city, distance in nearby:
                if nearby_city in remaining:
                    cluster_cities.append(nearby_city)
                    remaining.discard(nearby_city)
            
            # Calculate cluster center
            cluster_coords = [self.italian_cities[c] for c in cluster_cities if c in self.italian_cities]
            avg_lat = sum(c['lat'] for c in cluster_coords) / len(cluster_coords)
            avg_lng = sum(c['lng'] for c in cluster_coords) / len(cluster_coords)
            
            clusters.append({
                'center_city': center_city,
                'cities': cluster_cities,
                'center_coords': {'lat': avg_lat, 'lng': avg_lng},
                'city_count': len(cluster_cities)
            })
        
        logger.info(f"🗺️ Created {len(clusters)} geographic clusters from {len(cities)} cities")
        return clusters
    
    def get_regional_scraping_plan(self, target_regions: List[str] = None) -> List[Dict]:
        """
        Get a scraping plan organized by region
        
        Args:
            target_regions: List of regions to include (None = all)
        
        Returns:
            List of regional scraping plans
        """
        if target_regions is None:
            target_regions = list(self.regions.keys())
        
        plans = []
        for region in target_regions:
            if region not in self.regions:
                continue
            
            cities = self.regions[region]
            plans.append({
                'region': region,
                'cities': cities,
                'city_count': len(cities),
                'priority': self._get_region_priority(region)
            })
        
        # Sort by priority
        plans.sort(key=lambda x: x['priority'], reverse=True)
        
        return plans
    
    def _get_region_priority(self, region: str) -> float:
        """Assign priority to regions based on tourism importance"""
        priority_map = {
            'Lazio': 1.0,  # Roma
            'Toscana': 0.95,  # Firenze, Siena, Pisa
            'Veneto': 0.9,  # Venezia, Verona
            'Lombardia': 0.85,  # Milano
            'Campania': 0.8,  # Napoli, Amalfi
            'Sicilia': 0.75,
            'Piemonte': 0.7,
            'Emilia-Romagna': 0.65,
            'Liguria': 0.6,
            'Puglia': 0.55,
        }
        return priority_map.get(region, 0.5)


class BatchScrapingOptimizer:
    """Optimizes batch scraping operations for cost efficiency"""
    
    def __init__(self, clusterer: GeographicClusterer):
        self.clusterer = clusterer
    
    def optimize_scraping_order(self, cities: List[str]) -> List[Dict]:
        """
        Optimize the order of scraping to maximize efficiency
        
        Strategy:
        1. Group by geographic clusters
        2. Within clusters, order by priority
        3. Batch similar categories together
        
        Returns:
            Ordered list of scraping tasks
        """
        # Create geographic clusters
        clusters = self.clusterer.create_scraping_clusters(cities)
        
        # Optimize each cluster
        optimized_tasks = []
        
        for cluster in clusters:
            # For each city in cluster
            for city in cluster['cities']:
                # Group by category to batch API calls
                for category in ['tourist_attraction', 'restaurant', 'lodging']:
                    optimized_tasks.append({
                        'city': city,
                        'category': category,
                        'cluster_id': cluster['center_city'],
                        'priority': self._calculate_task_priority(city, category, cluster)
                    })
        
        # Sort by priority
        optimized_tasks.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"⚡ Optimized {len(optimized_tasks)} scraping tasks across {len(clusters)} clusters")
        return optimized_tasks
    
    def _calculate_task_priority(self, city: str, category: str, cluster: Dict) -> float:
        """Calculate priority score for a scraping task"""
        
        # Base priority
        priority = 1.0
        
        # Boost major cities
        major_cities = ['Roma', 'Milano', 'Firenze', 'Venezia', 'Napoli']
        if city in major_cities:
            priority += 0.5
        
        # Boost tourist attractions over other categories
        if category == 'tourist_attraction':
            priority += 0.3
        elif category == 'restaurant':
            priority += 0.2
        
        # Small boost for cluster center (scrape nearby cities together)
        if city == cluster['center_city']:
            priority += 0.1
        
        return priority
    
    def estimate_batch_cost(self, tasks: List[Dict], cost_per_call: float = 0.02) -> Dict:
        """
        Estimate cost and time for batch scraping
        
        Returns:
            Cost and time estimates
        """
        total_tasks = len(tasks)
        total_cost = total_tasks * cost_per_call
        
        # Estimate time (assuming 5 seconds per API call)
        estimated_seconds = total_tasks * 5
        estimated_minutes = estimated_seconds / 60
        
        return {
            'total_tasks': total_tasks,
            'estimated_cost_usd': total_cost,
            'estimated_time_minutes': estimated_minutes,
            'cost_per_task': cost_per_call,
            'tasks_per_minute': 12  # 60 / 5
        }


# Integration functions

def create_geographic_scraping_plan(cities: List[str], max_cluster_radius: float = 150) -> Dict:
    """
    Create an optimized geographic scraping plan
    
    Args:
        cities: List of cities to scrape
        max_cluster_radius: Maximum cluster radius in km
    
    Returns:
        Complete scraping plan with clusters and tasks
    """
    clusterer = GeographicClusterer()
    optimizer = BatchScrapingOptimizer(clusterer)
    
    # Create clusters
    clusters = clusterer.create_scraping_clusters(cities, max_cluster_radius)
    
    # Optimize task order
    tasks = optimizer.optimize_scraping_order(cities)
    
    # Estimate costs
    cost_estimate = optimizer.estimate_batch_cost(tasks)
    
    plan = {
        'total_cities': len(cities),
        'clusters': clusters,
        'tasks': tasks,
        'cost_estimate': cost_estimate,
        'created_at': datetime.now().isoformat()
    }
    
    logger.info(f"📋 Created scraping plan: {len(cities)} cities, {len(clusters)} clusters, {len(tasks)} tasks")
    logger.info(f"💰 Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}, Time: {cost_estimate['estimated_time_minutes']:.1f} min")
    
    return plan


def get_regional_batch_tasks(region: str = 'Toscana') -> List[Dict]:
    """
    Get batch scraping tasks for a specific region
    
    Example:
        tasks = get_regional_batch_tasks('Toscana')
        # Returns tasks for Firenze, Siena, Pisa, etc.
    """
    clusterer = GeographicClusterer()
    optimizer = BatchScrapingOptimizer(clusterer)
    
    # Get regional plan
    regional_plans = clusterer.get_regional_scraping_plan([region])
    
    if not regional_plans:
        return []
    
    # Get cities for region
    cities = regional_plans[0]['cities']
    
    # Optimize tasks
    tasks = optimizer.optimize_scraping_order(cities)
    
    logger.info(f"🗺️ Created {len(tasks)} tasks for {region}")
    return tasks

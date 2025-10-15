"""
🚀 VIAMIGO TRAVEL AI - ENHANCEMENT MODULES
Advanced intelligence systems for proactive scraping
"""

from .seasonal_intelligence import (
    SeasonalIntelligence,
    EventBasedIntelligence,
    get_seasonal_scraping_priorities,
    integrate_seasonal_intelligence_with_scraping
)

from .ml_predictions import (
    UserBehaviorAnalyzer,
    CollaborativeFiltering,
    get_ml_based_scraping_priorities
)

from .analytics import (
    CacheAnalytics,
    CostMonitor,
    QualityValidator,
    create_analytics_dashboard_data,
    monitor_and_alert
)

from .multi_source import (
    MultiSourceAggregator,
    DataEnrichmentPipeline,
    create_enriched_place_profile
)

from .geographic_clustering import (
    GeographicClusterer,
    BatchScrapingOptimizer,
    create_geographic_scraping_plan,
    get_regional_batch_tasks
)

__all__ = [
    # Seasonal Intelligence
    'SeasonalIntelligence',
    'EventBasedIntelligence',
    'get_seasonal_scraping_priorities',
    'integrate_seasonal_intelligence_with_scraping',

    # ML Predictions
    'UserBehaviorAnalyzer',
    'CollaborativeFiltering',
    'get_ml_based_scraping_priorities',

    # Analytics
    'CacheAnalytics',
    'CostMonitor',
    'QualityValidator',
    'create_analytics_dashboard_data',
    'monitor_and_alert',

    # Multi-Source Aggregation
    'MultiSourceAggregator',
    'DataEnrichmentPipeline',
    'create_enriched_place_profile',

    # Geographic Clustering
    'GeographicClusterer',
    'BatchScrapingOptimizer',
    'create_geographic_scraping_plan',
    'get_regional_batch_tasks',
]

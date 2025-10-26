#!/usr/bin/env python3
"""
ViamigoTravelAI Performance Monitor
Advanced performance monitoring and optimization system for 9,930+ places across 56 Italian cities
"""

import time
import psutil
import psycopg2
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from flask import Blueprint, jsonify, request

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it
import chromadb
from functools import wraps
import threading
import logging
from collections import defaultdict, deque

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    endpoint: str
    response_time: float
    database_query_time: float
    chromadb_query_time: float
    memory_usage: float
    cpu_usage: float
    cache_hit_rate: float
    error_count: int = 0


class ViamigoPerformanceMonitor:
    """Advanced performance monitoring system"""

    def __init__(self):
        """Initialize the performance monitor"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # PostgreSQL connection from environment
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError(
                    "DATABASE_URL not found in environment variables")
            self.db_conn = psycopg2.connect(database_url)
            self.logger.info("✅ Performance monitor connected to PostgreSQL")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            self.db_conn = None

        # ChromaDB connection (setup is delegated to method)
        self.setup_chromadb_connection()

        # Performance monitoring data
        self.metrics_history: List[PerformanceMetrics] = []
        self.cache = {}  # In-memory cache
        self.cache_timestamps = {}  # Cache TTL tracking
        self.cache_ttl = 300  # 5 minutes
        self.monitoring_thread = None

        # Start background monitoring
        self.start_background_monitoring()

    def setup_database_connection(self):
        """Setup database connection for monitoring"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url and 'sslmode=' not in database_url:
                database_url += '&sslmode=require' if '?' in database_url else '?sslmode=require'

            self.db_conn = psycopg2.connect(database_url)
            logger.info("✅ Performance monitor connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            self.db_conn = None

    def setup_chromadb_connection(self):
        """Setup ChromaDB connection for monitoring with graceful degradation"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path="/workspaces/ViamigoTravelAI/chromadb_data"
            )
            # Try to get or create the collection
            try:
                self.chroma_collection = self.chroma_client.get_collection(
                    "viamigo_travel_data")
            except ValueError:
                # Collection doesn't exist, create it
                self.chroma_collection = self.chroma_client.create_collection(
                    "viamigo_travel_data")
                logger.info(
                    "✅ Created new ChromaDB collection: viamigo_travel_data")

            logger.info("✅ Performance monitor connected to ChromaDB")
        except Exception as e:
            logger.warning(
                f"⚠️ ChromaDB connection failed, continuing without it: {e}")
            self.chroma_client = None
            self.chroma_collection = None
            self.chroma_collection = None

    def start_background_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while True:
                try:
                    # System metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()

                    # Database connection check
                    db_healthy = self.check_database_health()
                    chromadb_healthy = self.check_chromadb_health()

                    # Log critical issues
                    if cpu_percent > 80:
                        logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                    if memory.percent > 85:
                        logger.warning(
                            f"⚠️ High memory usage: {memory.percent}%")
                    if not db_healthy:
                        logger.error("❌ Database health check failed")
                    if not chromadb_healthy:
                        logger.error("❌ ChromaDB health check failed")

                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Background monitoring error: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        logger.info("🔄 Background performance monitoring started")

    def check_database_health(self) -> bool:
        """Check PostgreSQL database health"""
        if not self.db_conn:
            return False

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False

    def check_chromadb_health(self) -> bool:
        """Check ChromaDB health with graceful degradation"""
        if not self.chroma_client or not self.chroma_collection:
            return False

        try:
            self.chroma_collection.count()
            return True
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB health check failed: {e}")
            return False

    def get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for request"""
        param_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}:{hash(param_str)}"

    def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response if valid"""
        if cache_key in self.query_cache:
            cached_data, timestamp = self.query_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                self.cache_stats['hits'] += 1
                return cached_data
            else:
                # Remove expired cache
                del self.query_cache[cache_key]

        self.cache_stats['misses'] += 1
        return None

    def set_cached_response(self, cache_key: str, response: Any):
        """Cache response with timestamp"""
        self.query_cache[cache_key] = (response, datetime.now())

        # Cleanup old cache entries if needed
        if len(self.query_cache) > 1000:
            # Remove oldest 20% of entries
            sorted_items = sorted(
                self.query_cache.items(),
                key=lambda x: x[1][1]
            )
            for key, _ in sorted_items[:200]:
                del self.query_cache[key]

    def performance_decorator(self, endpoint_name: str):
        """Decorator to monitor endpoint performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                db_query_time = 0
                chromadb_query_time = 0
                error_count = 0

                try:
                    # Check cache first
                    cache_key = self.get_cache_key(endpoint_name, kwargs)
                    cached_response = self.get_cached_response(cache_key)

                    if cached_response is not None:
                        logger.info(f"🚀 Cache hit for {endpoint_name}")
                        return cached_response

                    # Execute function and measure DB times
                    result = func(*args, **kwargs)

                    # Cache successful responses
                    self.set_cached_response(cache_key, result)

                except Exception as e:
                    error_count = 1
                    logger.error(f"❌ Error in {endpoint_name}: {e}")
                    raise
                finally:
                    # Record metrics
                    end_time = time.time()
                    response_time = end_time - start_time

                    # System metrics
                    memory_usage = psutil.virtual_memory().percent
                    cpu_usage = psutil.cpu_percent()

                    # Cache hit rate
                    total_requests = self.cache_stats['hits'] + \
                        self.cache_stats['misses']
                    cache_hit_rate = (
                        self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

                    # Create metrics
                    metrics = PerformanceMetrics(
                        timestamp=datetime.now(),
                        endpoint=endpoint_name,
                        response_time=response_time,
                        database_query_time=db_query_time,
                        chromadb_query_time=chromadb_query_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        cache_hit_rate=cache_hit_rate,
                        error_count=error_count
                    )

                    self.metrics_history.append(metrics)

                    # Log slow queries
                    if response_time > self.slow_query_threshold:
                        logger.warning(
                            f"🐌 Slow query detected: {endpoint_name} took {response_time:.2f}s")

                return result
            return wrapper
        return decorator

    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No performance data available yet"}

        # Recent metrics (last hour)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if not recent_metrics:
            # Last 100 requests
            recent_metrics = list(self.metrics_history)[-100:]

        # Calculate statistics
        response_times = [m.response_time for m in recent_metrics]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        # Error rate
        error_count = sum(m.error_count for m in recent_metrics)
        error_rate = (error_count / len(recent_metrics)
                      * 100) if recent_metrics else 0

        # System metrics
        current_memory = psutil.virtual_memory().percent
        current_cpu = psutil.cpu_percent()

        # Cache statistics
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (
            self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        # Database metrics
        db_stats = self.get_database_performance_stats()
        chromadb_stats = self.get_chromadb_performance_stats()

        # Endpoint performance breakdown
        endpoint_stats = defaultdict(list)
        for metric in recent_metrics:
            endpoint_stats[metric.endpoint].append(metric.response_time)

        endpoint_performance = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_performance[endpoint] = {
                'avg_response_time': sum(times) / len(times),
                'max_response_time': max(times),
                'request_count': len(times)
            }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "avg_response_time": round(avg_response_time, 3),
                "max_response_time": round(max_response_time, 3),
                "min_response_time": round(min_response_time, 3),
                "error_rate": round(error_rate, 2),
                "total_requests": len(recent_metrics),
                "cache_hit_rate": round(cache_hit_rate, 2)
            },
            "system": {
                "cpu_usage": round(current_cpu, 1),
                "memory_usage": round(current_memory, 1),
                "cache_size": len(self.query_cache)
            },
            "database": db_stats,
            "chromadb": chromadb_stats,
            "endpoints": endpoint_performance,
            "cache_stats": dict(self.cache_stats),
            "recent_slow_queries": [
                {
                    "endpoint": m.endpoint,
                    "response_time": round(m.response_time, 3),
                    "timestamp": m.timestamp.isoformat()
                }
                for m in recent_metrics
                if m.response_time > self.slow_query_threshold
            ][-10:]  # Last 10 slow queries
        }

    def get_database_performance_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL performance statistics"""
        if not self.db_conn:
            return {"status": "disconnected"}

        try:
            with self.db_conn.cursor() as cursor:
                # Database size and counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_places,
                        COUNT(DISTINCT city) as total_cities,
                        pg_size_pretty(pg_total_relation_size('place_cache')) as table_size
                    FROM place_cache
                """)
                total_places, total_cities, table_size = cursor.fetchone()

                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) as recent_access_count
                    FROM place_cache 
                    WHERE last_accessed > NOW() - INTERVAL '1 hour'
                """)
                recent_access = cursor.fetchone()[0]

                return {
                    "status": "connected",
                    "total_places": total_places,
                    "total_cities": total_cities,
                    "table_size": table_size,
                    "recent_access_count": recent_access
                }
        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return {"status": "error", "message": str(e)}

    def get_chromadb_performance_stats(self) -> Dict[str, Any]:
        """Get ChromaDB performance statistics with graceful degradation"""
        if not self.chroma_client or not self.chroma_collection:
            return {
                "status": "disconnected",
                "message": "ChromaDB not available - performance monitoring continues without it"
            }

        try:
            count = self.chroma_collection.count()
            return {
                "status": "connected",
                "total_documents": count,
                "collection_name": "viamigo_travel_data"
            }
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB stats error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "impact": "minimal"
            }

    def optimize_database_queries(self):
        """Optimize database performance"""
        if not self.db_conn:
            return {"status": "error", "message": "No database connection"}

        optimizations = []

        try:
            with self.db_conn.cursor() as cursor:
                # Check for missing indexes
                cursor.execute("""
                    SELECT schemaname, tablename, attname, n_distinct, correlation 
                    FROM pg_stats 
                    WHERE tablename = 'place_cache' 
                    AND schemaname = 'public'
                """)

                stats = cursor.fetchall()

                # Suggest indexes for frequently queried columns
                if any('city' in str(stat) for stat in stats):
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_place_cache_city 
                        ON place_cache(city)
                    """)
                    optimizations.append("Created index on city column")

                # Create composite index for common queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_place_cache_city_category 
                    ON place_cache(city, (place_data->>'category'))
                """)
                optimizations.append(
                    "Created composite index on city and category")

                # Update table statistics
                cursor.execute("ANALYZE place_cache")
                optimizations.append("Updated table statistics")

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"Database optimization error: {e}")
            return {"status": "error", "message": str(e)}

        return {
            "status": "success",
            "optimizations": optimizations,
            "timestamp": datetime.now().isoformat()
        }


# Global performance monitor instance
performance_monitor = ViamigoPerformanceMonitor()

# Flask Blueprint for performance endpoints
performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/performance/dashboard', methods=['GET'])
def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        dashboard_data = performance_monitor.get_performance_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Performance dashboard error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@performance_bp.route('/performance/dashboard/view', methods=['GET'])
def view_performance_dashboard():
    """Serve the performance dashboard HTML page"""
    from flask import send_from_directory
    return send_from_directory('static', 'performance_dashboard.html')


@performance_bp.route('/performance/optimize', methods=['POST'])
def optimize_performance():
    """Run performance optimizations"""
    try:
        optimization_results = performance_monitor.optimize_database_queries()
        return jsonify(optimization_results)
    except Exception as e:
        logger.error(f"Performance optimization error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@performance_bp.route('/performance/cache/clear', methods=['POST'])
def clear_cache():
    """Clear performance cache"""
    try:
        performance_monitor.query_cache.clear()
        performance_monitor.cache_stats.clear()
        return jsonify({
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@performance_bp.route('/performance/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    try:
        db_healthy = performance_monitor.check_database_health()
        chromadb_healthy = performance_monitor.check_chromadb_health()

        system_metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

        overall_health = db_healthy and chromadb_healthy

        return jsonify({
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "chromadb": "healthy" if chromadb_healthy else "unhealthy",
                "system": system_metrics
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Test the performance monitor
    print("🔍 Testing ViamigoTravelAI Performance Monitor")
    print("=" * 50)

    monitor = ViamigoPerformanceMonitor()

    # Test dashboard data
    dashboard = monitor.get_performance_dashboard_data()
    print(f"📊 Dashboard Status: {dashboard['status']}")

    if dashboard['status'] == 'success':
        print(
            f"🗄️  Database: {dashboard['database']['total_places']} places across {dashboard['database']['total_cities']} cities")
        print(
            f"🧠 ChromaDB: {dashboard['chromadb']['total_documents']} documents")
        print(f"💾 Cache Hit Rate: {dashboard['overview']['cache_hit_rate']}%")

    print("✅ Performance monitor initialized successfully!")

#!/usr/bin/env python3
"""
Semantic Search Demo for Viamigo Travel AI
Demonstrates the new semantic search capabilities in the RAG system
"""

from simple_rag_helper import (
    semantic_search_places,
    hybrid_search_places,
    search_places_by_description,
    get_city_context_with_semantic,
    rag_helper
)


def main():
    print("🔍 Viamigo Travel AI - Semantic Search Demo")
    print("=" * 50)

    # Demo 1: Basic semantic search
    print("\n1. 🍽️ Semantic Search for Restaurants")
    print("Query: 'romantic restaurants with beautiful view'")

    restaurants = semantic_search_places(
        query="romantic restaurants with beautiful view",
        city="roma",
        n_results=3
    )

    for i, place in enumerate(restaurants, 1):
        print(
            f"   {i}. {place.get('name', 'Restaurant')} - Score: {place.get('relevance_score', 0):.3f}")
        print(f"      City: {place.get('city', 'Unknown')}")
        print(f"      Category: {place.get('category', 'Unknown')}")

    # Demo 2: Hybrid search combining traditional + semantic
    print("\n2. 🔄 Hybrid Search (Traditional + Semantic)")
    print("Query: 'ancient Roman monuments and historical sites'")

    hybrid_results = hybrid_search_places(
        query="ancient Roman monuments and historical sites",
        city="Roma",
        categories=["tourist_attraction", "museum"],
        semantic_weight=0.4,
        n_results=3
    )

    for i, place in enumerate(hybrid_results, 1):
        source = place.get('search_source', 'unknown')
        enhanced = "✨" if place.get('semantic_enhanced') else ""
        print(f"   {i}. {place.get('name', 'Place')} - Source: {source} {enhanced}")
        if 'relevance_score' in place:
            print(
                f"      Semantic score: {place.get('relevance_score', 0):.3f}")

    # Demo 3: Natural language description search
    print("\n3. 📝 Search by Description")
    print("Description: 'museum with ancient Roman artifacts and sculptures'")

    museums = search_places_by_description(
        description="museum with ancient Roman artifacts and sculptures",
        city="roma",
        limit=3
    )

    for i, place in enumerate(museums, 1):
        print(
            f"   {i}. {place.get('name', 'Museum')} - Score: {place.get('relevance_score', 0):.3f}")

    # Demo 4: Enhanced city context with semantic integration
    print("\n4. 📊 Enhanced City Context with Semantic Search")
    print("City: Florence, Query: 'Renaissance art and sculptures'")

    context = get_city_context_with_semantic(
        city="Firenze",
        categories=["museum", "tourist_attraction"],
        semantic_query="Renaissance art and sculptures"
    )

    print(f"   Total places: {context.get('total_places', 0)}")
    print(f"   Categories: {list(context.get('categories', {}).keys())}")
    print(f"   Semantic enhanced: {context.get('semantic_enhanced', False)}")

    if 'semantic_results' in context:
        semantic_count = context['semantic_results'].get('count', 0)
        print(f"   Semantic results: {semantic_count}")

    # Performance metrics
    print("\n5. 📈 Performance Metrics")
    metrics = rag_helper.get_performance_metrics()
    print(f"   Total queries: {metrics['total_queries']}")
    print(f"   Cache hits: {metrics['cache_hits']}")
    print(f"   Semantic queries: {metrics.get('semantic_queries', 0)}")
    print(f"   Cache hit rate: {metrics['cache_hit_rate']:.1f}%")

    # ChromaDB status
    print("\n6. 🗄️ ChromaDB Status")
    if rag_helper._chroma_collection:
        count = rag_helper._chroma_collection.count()
        print(f"   ✅ ChromaDB connected with {count:,} documents")
    else:
        print("   ❌ ChromaDB not available")

    print("\n" + "=" * 50)
    print("🎉 Semantic Search Demo Complete!")
    print("\nAvailable Functions:")
    print("• semantic_search_places() - Natural language queries")
    print("• hybrid_search_places() - Traditional + semantic combined")
    print("• search_places_by_description() - Find places by description")
    print("• get_city_context_with_semantic() - Enhanced context retrieval")
    print("\nUsage Examples:")
    print("semantic_search_places('cozy wine bars', 'Milano', n_results=5)")
    print(
        "hybrid_search_places('historic churches', 'Roma', categories=['tourist_attraction'])")
    print("search_places_by_description('museum with medieval art', 'Firenze')")


if __name__ == "__main__":
    main()

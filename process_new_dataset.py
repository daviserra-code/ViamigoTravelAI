"""
Process the new larger Apify dataset
"""
from process_apify_dataset import process_apify_dataset, show_database_stats

if __name__ == "__main__":
    print("🖼️ ViamigoTravelAI - Processing NEW LARGER Dataset")
    print("Processing dataset_google-images-scraper_2025-10-18_16-14-07-199.json")
    print("=" * 70)

    # Show current state
    print("Current database state:")
    show_database_stats()

    print("\nStarting NEW dataset processing...")
    print("Strategy: Lower confidence threshold to capture more city/region images")

    # Process the new larger dataset
    # Lower confidence threshold (0.2) to include more city images
    # Limit to 3 images per attraction/city for good coverage

    results = process_apify_dataset(
        'dataset_google-images-scraper_2025-10-18_16-14-07-199.json',
        confidence_threshold=0.2,  # Lower threshold for city images
        max_images_per_attraction=3  # 3 images per destination for coverage
    )

    print(f"\n📊 NEW Dataset Processing Results:")
    print(f"   📁 Categories processed: {results['categories']}")
    print(f"   🖼️ Images processed: {results['total_processed']}")
    print(f"   ✅ Successfully added: {results['successful']}")
    print(f"   ❌ Failed: {results['failed']}")

    # Show final state
    print("\nFinal database state:")
    show_database_stats()

    print("\n🎉 NEW LARGER dataset processing completed!")
    print("=" * 70)

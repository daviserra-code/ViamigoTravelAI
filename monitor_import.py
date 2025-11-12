#!/usr/bin/env python3
"""Quick progress monitor for the Italian hotels import"""

import psycopg2
import time
import sys

DB_URL = 'postgresql://neondb_owner:npg_r9e2PGORqsAx@ep-ancient-morning-a6us6om6.us-west-2.aws.neon.tech/neondb?sslmode=require'


def get_italian_hotel_count():
    """Get current count of Italian hotels"""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM hotel_reviews WHERE country = 'Italy';")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count


def main():
    print("🏨 Monitoring Italian Hotels Import Progress")
    print("=" * 60)

    initial_count = get_italian_hotel_count()
    print(f"Initial count: {initial_count:,} Italian hotels")
    print("\nPress Ctrl+C to stop monitoring\n")

    try:
        while True:
            time.sleep(10)  # Check every 10 seconds
            current_count = get_italian_hotel_count()
            added = current_count - initial_count
            print(
                f"[{time.strftime('%H:%M:%S')}] Current: {current_count:,} hotels (+{added:,} new)")

    except KeyboardInterrupt:
        print(
            f"\n\n✅ Final count: {get_italian_hotel_count():,} Italian hotels")
        print(
            f"   Total added during monitoring: +{get_italian_hotel_count() - initial_count:,}")


if __name__ == "__main__":
    main()

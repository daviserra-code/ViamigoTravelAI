#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Italy Attractions Image Ingestor
--------------------------------
Pulls tourist attractions for selected Italian cities from Wikidata,
resolves Wikimedia Commons images, downloads 1280px thumbnails,
and stores them (as bytea) + metadata into PostgreSQL.

Usage:
  export DATABASE_URL="postgresql://user:pass@host:port/dbname"
  python italy_attractions_to_postgres.py --cities "Roma,Firenze,Milano,Venezia,Napoli,Bologna,Genova,Palermo,Verona,Siena" --limit 500

Notes:
- Adjust the --cities list or pass a text file via --cities-file (one city per line).
- Deduping happens by (source, source_id) unique index and by attraction_qid.
- Licenses/creator pulled from Commons extmetadata when available.
- For production: consider S3 for originals and keep thumbnails in DB.
"""

import os
import sys
import io
import argparse
import time
import hashlib
from typing import Dict, List, Optional, Tuple
import requests
import psycopg2
import psycopg2.extras

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

DEFAULT_CITIES = [
    "Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna",
    "Firenze", "Venezia", "Verona", "Siena", "Pisa", "Bari", "Catania",
    "Trieste", "Parma", "Modena", "Ravenna", "Perugia", "Lecce"
]

USER_AGENT = "ItalyAttractionsCollector/1.0 (contact: dev@example.com)"

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def db_connect() -> psycopg2.extensions.connection:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable not set.")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS attraction_images (
  id BIGSERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL,
  source_id TEXT,
  attraction_qid TEXT,
  city TEXT,
  attraction_name TEXT,
  license TEXT,
  license_url TEXT,
  creator TEXT,
  attribution TEXT,
  original_url TEXT,
  thumb_url TEXT,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  img_bytes BYTEA,
  mime_type TEXT,
  width INT,
  height INT,
  sha256 TEXT
);

-- Fast lookups & dedupe protections
CREATE INDEX IF NOT EXISTS idx_attraction_images_city ON attraction_images (LOWER(city));
CREATE UNIQUE INDEX IF NOT EXISTS uq_attraction_imgs_source_sid ON attraction_images (source, source_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_attraction_imgs_qid ON attraction_images (attraction_qid);
"""

INSERT_SQL = r"""
INSERT INTO attraction_images (
  source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
  attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256
) VALUES (
  %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s, %(license)s, %(license_url)s, %(creator)s,
  %(attribution)s, %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(width)s, %(height)s, %(sha256)s
)
ON CONFLICT ON CONSTRAINT uq_attraction_imgs_qid DO NOTHING
"""

def http_get(url: str, params: Optional[Dict]=None, headers: Optional[Dict]=None, stream=False):
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    r = requests.get(url, params=params, headers=h, timeout=30, stream=stream)
    r.raise_for_status()
    return r

def wikidata_search_city_qid(city_name: str) -> Optional[str]:
    """Find QID for a city by name within Italy (Q38)."""
    params = {
        "action": "wbsearchentities",
        "search": city_name,
        "language": "it",
        "format": "json",
        "type": "item",
        "limit": 5
    }
    try:
        data = http_get(WIKIDATA_SEARCH, params=params).json()
        # Heuristic: pick first where description mentions Italy or instance looks like city/commune
        for ent in data.get("search", []):
            if "description" in ent and ent["description"]:
                desc = ent["description"].lower()
                if "italia" in desc or "italian" in desc or "comune" in desc or "città" in desc:
                    return ent["id"]
        # Fallback to first result
        if data.get("search"):
            return data["search"][0]["id"]
    except Exception as e:
        log(f"wikidata_search_city_qid error for {city_name}: {e}")
    return None

def build_sparql_for_city_qid(city_qid: str, limit: int = 1000) -> str:
    # Tourist attraction QID
    q_tourist_attraction = "wd:Q570116"
    return f"""
SELECT ?item ?itemLabel ?image ?coord WHERE {{
  ?item wdt:P31/wdt:P279* {q_tourist_attraction};
        wdt:P131* wd:{city_qid};
        wdt:P625 ?coord.
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }}
}}
LIMIT {limit}
"""

def run_sparql(query: str) -> List[Dict]:
    headers = {"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT}
    r = requests.get(WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j.get("results", {}).get("bindings", [])

def commons_resolve_image_info(file_title: str, thumb_width: int = 1280) -> Optional[Dict]:
    # file_title is like: "File:Colosseo di Roma.jpg"
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "titles": file_title,
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": thumb_width
    }
    try:
        data = http_get(COMMONS_API, params=params).json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            ii = page.get("imageinfo", [])
            if not ii:
                continue
            info = ii[0]
            # extmetadata extraction
            ext = info.get("extmetadata", {}) or {}
            creator = (ext.get("Artist", {}) or {}).get("value") or ""
            license_name = (ext.get("LicenseShortName", {}) or {}).get("value") or ""
            license_url = (ext.get("LicenseUrl", {}) or {}).get("value") or ""
            credit = (ext.get("Credit", {}) or {}).get("value") or ""
            # Build simple attribution
            attribution = ""
            if creator or license_name:
                attribution = f"{creator} – {license_name}".strip(" –")
            return {
                "original_url": info.get("url"),
                "thumb_url": info.get("thumburl") or info.get("url"),
                "mime_type": info.get("mime"),
                "width": info.get("thumbwidth") or info.get("width"),
                "height": info.get("thumbheight") or info.get("height"),
                "creator": creator,
                "license": license_name,
                "license_url": license_url,
                "attribution": attribution or credit
            }
    except Exception as e:
        log(f"commons_resolve_image_info error for {file_title}: {e}")
    return None

def download_bytes(url: str) -> Tuple[bytes, Optional[str]]:
    r = http_get(url, stream=True)
    content = io.BytesIO()
    for chunk in r.iter_content(chunk_size=65536):
        if chunk:
            content.write(chunk)
    mime = r.headers.get("Content-Type")
    return content.getvalue(), mime

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)

def insert_row(conn, row: Dict) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(INSERT_SQL, row)
        return True
    except Exception as e:
        # Likely conflict; log and continue
        log(f"Insert skipped/failed for {row.get('attraction_qid')} ({row.get('source_id')}): {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Ingest Italian tourist-attraction images into Postgres as bytea")
    parser.add_argument("--cities", type=str, help="Comma-separated city names (IT)", default=",".join(DEFAULT_CITIES))
    parser.add_argument("--cities-file", type=str, help="File path with one city per line", default=None)
    parser.add_argument("--limit", type=int, default=500, help="Max attractions per city")
    parser.add_argument("--thumb-width", type=int, default=1280, help="Thumbnail width to fetch from Commons")
    args = parser.parse_args()

    # Build city list
    cities: List[str] = []
    if args.cities_file and os.path.exists(args.cities_file):
        with open(args.cities_file, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    cities.append(name)
    else:
        cities = [c.strip() for c in args.cities.split(",") if c.strip()]

    if not cities:
        log("No cities provided. Exiting.")
        sys.exit(1)

    conn = db_connect()
    ensure_schema(conn)

    total_inserted = 0
    for city in cities:
        log(f"Resolving QID for city: {city}")
        qid = wikidata_search_city_qid(city)
        if not qid:
            log(f"  Could not resolve QID for {city}, skipping.")
            continue

        log(f"  City {city} → {qid}")
        sparql = build_sparql_for_city_qid(qid, limit=args.limit)
        rows = run_sparql(sparql)
        log(f"  Found {len(rows)} attractions (with/without images)")

        for b in rows:
            item_uri = b["item"]["value"]
            item_qid = item_uri.rsplit("/", 1)[-1]
            item_label = b.get("itemLabel", {}).get("value", "")
            image_file = b.get("image", {}).get("value", "")  # Commons file URL like http://.../Special:FilePath/...
            # If SPARQL returns actual File entity URL, convert to title
            file_title = None
            if image_file:
                # Often it's a direct URL. We prefer the canonical "File:..." title when possible.
                # Try to extract from URL if it contains /Special:FilePath/ or /File:
                if "/Special:FilePath/" in image_file:
                    # Use the last segment as name; prepend "File:"
                    name = image_file.split("/Special:FilePath/")[-1]
                    file_title = "File:" + requests.utils.unquote(name)
                elif "/File:" in image_file:
                    file_title = image_file.split("/File:")[-1]
                    file_title = "File:" + requests.utils.unquote(file_title)
                else:
                    # Last resort: skip if we can't form a title
                    file_title = None

            if not file_title:
                # No image; skip. You can later backfill with Openverse/Flickr.
                continue

            info = commons_resolve_image_info(file_title, thumb_width=args.thumb_width)
            if not info or not info.get("thumb_url"):
                continue

            try:
                img_bytes, mime = download_bytes(info["thumb_url"])
            except Exception as e:
                log(f"  Download failed for {file_title}: {e}")
                continue

            digest = sha256_bytes(img_bytes)

            row = {
                "source": "wikimedia",
                "source_id": file_title,
                "attraction_qid": item_qid,
                "city": city,
                "attraction_name": item_label,
                "license": info.get("license"),
                "license_url": info.get("license_url"),
                "creator": info.get("creator"),
                "attribution": info.get("attribution"),
                "original_url": info.get("original_url"),
                "thumb_url": info.get("thumb_url"),
                "img_bytes": psycopg2.Binary(img_bytes),
                "mime_type": info.get("mime_type") or mime,
                "width": info.get("width"),
                "height": info.get("height"),
                "sha256": digest,
            }

            ok = insert_row(conn, row)
            if ok:
                total_inserted += 1
                if total_inserted % 25 == 0:
                    log(f"Inserted so far: {total_inserted}")

        log(f"City done: {city} → inserted cumulative: {total_inserted}")

    log(f"ALL DONE. Total inserted: {total_inserted}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Openverse Fallback Collector (stable)
------------------------------------
- Endpoint: https://api.openverse.org/v1/images/ (nuovo host)
- page_size: max 20 senza token (evita 401)
- Backoff educato su 429/5xx e rispetto di Retry-After
- Modalità:
    A) per città (query generiche: landmark/monument/piazza/duomo/museum/...)
    B) da CSV: attraction_qid,city,attraction_name  ->  "<name> <city>"
- Inserisce in 'attraction_images' come BLOB (bytea), source='openverse'
- ON CONFLICT DO NOTHING (idempotente)

Esempi:
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
  python openverse_fallback.py --cities "Milano,Roma" --per-query 120 --queries-per-city 4 --thumb-first
  python openverse_fallback.py --missing-file missing_attractions.csv --per-query 60 --thumb-first
"""
import os
import io
import csv
import time
import argparse
import sys
import hashlib
import random
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry
import psycopg2
import psycopg2.extras

OPENVERSE_API = "https://api.openverse.org/v1/images/"
UA = "OpenverseFallback/1.2 (+https://example.com/contact)"
DEFAULT_CITIES = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Venezia",
                  "Verona", "Siena", "Pisa", "Bari", "Catania", "Trieste", "Parma", "Modena", "Ravenna", "Perugia", "Lecce"]


def make_session(connect_timeout: int, read_timeout: int) -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=6, connect=3, read=3, backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    a = HTTPAdapter(max_retries=retries, pool_maxsize=20)
    s.mount("https://", a)
    s.mount("http://", a)
    s.headers.update({"User-Agent": UA})
    # wrap timeouts
    s.request = _timeout_wrapper(
        s.request, connect_timeout, read_timeout)  # type: ignore
    return s


def _timeout_wrapper(fn, connect_timeout, read_timeout):
    def wrapped(method, url, **kwargs):
        timeout = kwargs.get("timeout", (connect_timeout, read_timeout))
        if isinstance(timeout, (int, float)):
            timeout = (timeout, timeout)
        kwargs["timeout"] = timeout
        return fn(method, url, **kwargs)
    return wrapped


def log(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def db_connect():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    return conn


INS = """
INSERT INTO attraction_images (
  source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
  attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256
) VALUES (
  %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s, %(license)s, %(license_url)s, %(creator)s,
  %(attribution)s, %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(width)s, %(height)s, %(sha256)s
)
ON CONFLICT DO NOTHING
"""


def openverse_search(sess: requests.Session, query: str, page: int, page_size: int, licenses: str,
                     max_backoff: float = 60.0, base_sleep: float = 1.0) -> Dict:
    """
    Chiama Openverse rispettando i limiti:
    - forza page_size<=20 per anonimi (evita 401)
    - gestisce 429 con Retry-After/backoff + jitter
    - ritenta sui 5xx qualche volta
    """
    if page_size > 20:
        page_size = 20  # hard cap per richieste anonime

    params = {
        "q": query,
        "license_type": licenses,      # "cc0,by,by-sa"
        "page": page,
        "page_size": page_size,
        "extension": "jpg,png,jpeg",
        "mature": "false",
        "source": "flickr,wikimedia",
    }

    attempt = 0
    sleep_s = base_sleep
    while True:
        attempt += 1
        r = sess.get(OPENVERSE_API, params=params, allow_redirects=True)
        status = r.status_code

        if 200 <= status < 300:
            return r.json()

        if status == 401:
            # È già page_size<=20: niente altro da fare da anonimi
            r.raise_for_status()

        if status == 429:
            ra = r.headers.get("Retry-After")
            if ra:
                try:
                    wait_s = max(float(ra), base_sleep)
                except Exception:
                    wait_s = sleep_s
            else:
                wait_s = sleep_s
            # jitter e cap
            wait_s = min(wait_s * (1.5 + random.random()*0.5), max_backoff)
            time.sleep(wait_s)
            sleep_s = wait_s
            continue

        if status >= 500 and attempt <= 5:
            time.sleep(min(sleep_s * (1.5 + random.random()*0.5), max_backoff))
            continue

        r.raise_for_status()


def download(sess: requests.Session, url: str) -> Tuple[bytes, Optional[str]]:
    r = sess.get(url, stream=True, allow_redirects=True)
    r.raise_for_status()
    buf = io.BytesIO()
    for ch in r.iter_content(65536):
        if ch:
            buf.write(ch)
    return buf.getvalue(), r.headers.get("Content-Type")


def insert_row(conn, row: Dict) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(INS, row)
        return True
    except Exception as e:
        log(f"Insert skipped/failed (source_id={row.get('source_id')}): {e}")
        return False


def city_mode(sess, conn, cities: List[str], per_query: int, queries_per_city: int,
              licenses: str, thumb_first: bool):
    query_bases = ["landmark", "monument", "piazza",
                   "duomo", "cathedral", "museum", "historic center"]
    for city in cities:
        log(f"[CITY] {city}")
        done = 0
        for qb in query_bases[:queries_per_city]:
            q = f"{city} {qb}"
            page = 1
            while done < per_query:
                page_size = min(20, per_query - done)
                try:
                    data = openverse_search(
                        sess, q, page=page, page_size=page_size, licenses=licenses)
                except Exception as e:
                    log(f"  search error '{q}' p{page}: {e}")
                    break

                results = data.get("results", []) or []
                if not results:
                    break

                for item in results:
                    src_id = item.get("id")
                    url = item.get("url") or item.get("foreign_landing_url")
                    thumb = item.get("thumbnail") or url
                    creator = item.get("creator") or item.get(
                        "creator_url") or ""
                    lic = item.get("license") or ""
                    lic_ver = item.get("license_version") or ""
                    license_url = item.get("license_url") or ""
                    title = item.get("title") or ""

                    d_url = thumb if (thumb_first and thumb) else url
                    if not d_url:
                        continue
                    try:
                        bytes_, mime = download(sess, d_url)
                    except Exception:
                        alt = url if d_url == thumb else thumb
                        if not alt:
                            continue
                        try:
                            bytes_, mime = download(sess, alt)
                        except Exception:
                            continue

                    row = {
                        "source": "openverse",
                        "source_id": src_id,
                        "attraction_qid": None,
                        "city": city,
                        "attraction_name": title or q,
                        "license": f"{lic} {lic_ver}".strip(),
                        "license_url": license_url,
                        "creator": creator,
                        "attribution": f"{creator} – {lic.upper()}",
                        "original_url": url,
                        "thumb_url": thumb,
                        "img_bytes": psycopg2.Binary(bytes_),
                        "mime_type": mime,
                        "width": None,
                        "height": None,
                        "sha256": hashlib.sha256(bytes_).hexdigest(),
                    }
                    if insert_row(conn, row):
                        done += 1
                        if done % 25 == 0:
                            log(f"  inserted {done}/{per_query} for {city}")

                page += 1
                time.sleep(1.0)  # respiro tra pagine
                if page > (data.get("page_count") or 1):
                    break

            # respiro tra query base
            time.sleep(1.5 + random.random())

        log(f"[CITY DONE] {city} target ~{done}/{per_query}")


def csv_mode(sess, conn, csv_path: str, per_query: int, licenses: str, thumb_first: bool):
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            qid = (r.get("attraction_qid") or "").strip() or None
            city = (r.get("city") or "").strip()
            name = (r.get("attraction_name") or "").strip()
            if not city and not name:
                continue
            q = f"{name} {city}".strip()
            log(f"[CSV] {qid or '-'} | '{q}'")
            done = 0
            page = 1
            while done < per_query:
                page_size = min(20, per_query - done)
                try:
                    data = openverse_search(
                        sess, q, page=page, page_size=page_size, licenses=licenses)
                except Exception as e:
                    log(f"  search error '{q}' p{page}: {e}")
                    break

                results = data.get("results", []) or []
                if not results:
                    break

                for item in results:
                    src_id = item.get("id")
                    url = item.get("url") or item.get("foreign_landing_url")
                    thumb = item.get("thumbnail") or url
                    creator = item.get("creator") or item.get(
                        "creator_url") or ""
                    lic = item.get("license") or ""
                    lic_ver = item.get("license_version") or ""
                    license_url = item.get("license_url") or ""
                    title = item.get("title") or name or city

                    d_url = thumb if (thumb_first and thumb) else url
                    if not d_url:
                        continue
                    try:
                        bytes_, mime = download(sess, d_url)
                    except Exception:
                        alt = url if d_url == thumb else thumb
                        if not alt:
                            continue
                        try:
                            bytes_, mime = download(sess, alt)
                        except Exception:
                            continue

                    row = {
                        "source": "openverse",
                        "source_id": src_id,
                        "attraction_qid": qid,
                        "city": city,
                        "attraction_name": title,
                        "license": f"{lic} {lic_ver}".strip(),
                        "license_url": license_url,
                        "creator": creator,
                        "attribution": f"{creator} – {lic.upper()}",
                        "original_url": url,
                        "thumb_url": thumb,
                        "img_bytes": psycopg2.Binary(bytes_),
                        "mime_type": mime,
                        "width": None,
                        "height": None,
                        "sha256": hashlib.sha256(bytes_).hexdigest(),
                    }
                    if insert_row(conn, row):
                        done += 1
                        if done % 25 == 0:
                            log(f"  inserted {done}/{per_query} for '{q}'")
                page += 1
                time.sleep(1.0)
                if page > (data.get("page_count") or 1):
                    break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", type=str, default=",".join(DEFAULT_CITIES),
                    help="Elenco città (se non usi --missing-file)")
    ap.add_argument("--missing-file", type=str, default=None,
                    help="CSV con colonne: attraction_qid,city,attraction_name")
    ap.add_argument("--per-query", type=int, default=80,
                    help="Target immagini per query/città o per riga CSV")
    ap.add_argument("--queries-per-city", type=int, default=4,
                    help="Numero di query generiche per città (solo city-mode)")
    ap.add_argument("--licenses", type=str, default="cc0,by,by-sa",
                    help="Filtri licenze Openverse")
    ap.add_argument("--thumb-first", action="store_true",
                    help="Scarica prima la thumbnail (più leggera)")
    ap.add_argument("--connect-timeout", type=int, default=10)
    ap.add_argument("--read-timeout", type=int, default=45)
    args = ap.parse_args()

    sess = make_session(args.connect_timeout, args.read_timeout)
    conn = db_connect()

    if args.missing_file and os.path.exists(args.missing_file):
        csv_mode(sess, conn, args.missing_file, args.per_query,
                 args.licenses, args.thumb_first)
    else:
        cities = [c.strip() for c in args.cities.split(",") if c.strip()]
        city_mode(sess, conn, cities, args.per_query,
                  args.queries_per_city, args.licenses, args.thumb_first)


if __name__ == "__main__":
    main()
